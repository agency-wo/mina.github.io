#!/usr/bin/env python3
# [DB-002] sync_stock.py — the rebuild leg: CRM availability → static truth.
# DOES:   Fetches https://api.watch.al/public/stock (3 tries, backoff), maps
#         normalized site `reference` ↔ CRM keys, sets `sold` on LINKED
#         entries only, rewrites watches.json + watches-data.js byte-exactly,
#         reruns the generators (shop index, product pages, brand pages,
#         sitemap), and prints a linking report (linked / unlinked /
#         duplicates — reported, never guessed).
# IN:     No args. Run from anywhere; paths resolve to the repo this file
#         lives in. Offline behavior: fetch failure after retries → exit 2
#         with NOTHING changed (fail-closed: the last reconciled state
#         stands, and the Action goes loudly red).
# OUT:    Exit 0 = reconciled (changed or already true); exit 2 = no data.
#         The GitHub Action commits whatever diff this leaves behind;
#         replaying with the same feed produces zero diff (idempotent).
# CALLS:  gen_shop_index.py, gen_product_pages.py, gen_brand_pages.py,
#         gen_sitemap.py via subprocess (they own ALL generated HTML).
# NOTES:  Byte formats are load-bearing AND environment-dependent: git
#         materializes LF on the Action's Linux runner but CRLF on the
#         owner's autocrlf Windows tree — so the writers MIRROR the existing
#         file's EOL and BOM instead of assuming either (the first Action run
#         failed exactly here, caught by its own self-test before any write).
#         tools/test_sync_stock.py pins the roundtrip plus the flip
#         semantics. Contract: part-tracker repo, docs/CRM_SYNC.md.
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FEED = "https://api.watch.al/public/stock"
# The full chain, in CLAUDE.md's order. gen_blog_index is NOT optional on a
# catalogue change: the featured card carries {lolek}/{hilek} price tokens that
# only it resolves, and the rendered index has no data-stat marker for gen_stats
# to heal afterwards, so leaving it out quietly advertises the previous
# catalogue. gen_article_cta re-points every article bridge when stock moves.
# gen_sitemap stays LAST: it fingerprints page content to decide lastmod.
GENERATORS = ("gen_shop_index.py", "gen_product_pages.py",
              "gen_brand_pages.py", "gen_blog_index.py",
              "gen_article_cta.py", "gen_stats.py", "gen_sitemap.py")


def norm(s):
    return str(s or "").strip().upper()


def apply_stock(watches, stock):
    """Pure core: mutate `sold` on linked entries; return (changed_ids, report).

    Linked = the entry's normalized reference is a key of `stock` AND unique
    among site entries. Duplicated refs are never guessed at; absent refs are
    left owner-managed. Both directions: 0 → sold, >0 → back on sale.
    """
    # [DB-006] Archived records are excluded from the duplicate scan, not only
    # from the flip loop below. A retired watch keeps its shifra forever, so when
    # the same model came back in — the restock this archive exists to make easy —
    # the new entry collided with the retired one, the pair read as ambiguous, and
    # the LIVE watch was refused CRM linking silently, for good. A retired entry is
    # nobody's to flip; it is equally nobody's to block. Two LIVE entries sharing a
    # reference is still a real ambiguity and still blocks both.
    seen = {}
    for w in watches:
        if w.get("deleted"):
            continue
        r = norm(w.get("reference"))
        if r:
            seen.setdefault(r, []).append(w.get("id"))
    dups = {r: ids for r, ids in seen.items() if len(ids) > 1}

    changed, linked, unlinked = [], [], []
    for w in watches:
        if w.get("deleted"):
            continue          # [DB-006] retired entries are nobody's to flip
        r = norm(w.get("reference"))
        if not r or r in dups or r not in stock:
            unlinked.append(w.get("id"))
            continue
        linked.append(w.get("id"))
        should = stock[r] == 0
        if bool(w.get("sold", False)) != should:
            w["sold"] = should
            changed.append(w.get("id"))
    return changed, {"linked": linked, "unlinked": unlinked, "dups": dups}


def fetch_stock():
    last = None
    for i, delay in enumerate((0, 5, 15)):
        if delay:
            time.sleep(delay)
        try:
            req = urllib.request.Request(FEED, headers={"User-Agent": "stock-sync"})
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.load(r)
            if isinstance(d, dict) and isinstance(d.get("stock"), dict):
                return d["stock"]
            last = f"malformed body on try {i + 1}"
        except Exception as e:  # noqa: BLE001 — every failure retries, then reports
            last = f"try {i + 1}: {e}"
    print(f"FEED UNREACHABLE — nothing changed (fail-closed). Last error: {last}")
    return None


def style_of(raw):
    """(eol, bom) of an existing file — mirrored, never assumed."""
    return ("\r\n" if b"\r\n" in raw else "\n", raw.startswith(b"\xef\xbb\xbf"))


def json_bytes(data, eol="\n", bom=False):
    body = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    return (b"\xef\xbb\xbf" if bom else b"") + body.replace("\n", eol).encode("utf-8")


def data_js_bytes(data, eol="\n", bom=True):
    core = json.dumps(data, indent=2, ensure_ascii=False)
    body = "/* AUTO-GENERATED */\nwindow.WATCHES_DATA = " + core + ";\n"
    return (b"\xef\xbb\xbf" if bom else b"") + body.replace("\n", eol).encode("utf-8")


def regenerate(watches, why):
    """Rewrite both data files from `watches`, heal any stub, run the chain."""
    import make_shells
    j_eol, j_bom = style_of((BASE / "watches.json").read_bytes())
    d_eol, d_bom = style_of((BASE / "watches-data.js").read_bytes())
    (BASE / "watches.json").write_bytes(json_bytes(watches, j_eol, j_bom))
    (BASE / "watches-data.js").write_bytes(data_js_bytes(watches, d_eol, d_bom))
    # a watch whose `deleted` was just cleared still has a redirect stub, and
    # gen_product_pages refuses to patch one back into a full page
    make_shells.restore_missing(watches)
    for g in GENERATORS:
        print(f"— {g} —")
        subprocess.run([sys.executable, str(BASE / g)], cwd=BASE, check=True)
    print(why)


def main():
    # --regen: rebuild from whatever watches.json says now, no CRM call. This is
    # the admin-panel path: the flag is already written, the site has to catch up.
    if "--regen" in sys.argv:
        watches = json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))
        regenerate(watches, f"regenerated from watches.json ({len(watches)} watches)")
        return
    stock = fetch_stock()
    if stock is None:
        sys.exit(2)
    watches = json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))
    changed, report = apply_stock(watches, stock)

    print(f"linked: {len(report['linked'])}  unlinked: {len(report['unlinked'])}  "
          f"changed: {changed or 'none'}")
    if report["dups"]:
        print("DUPLICATE site refs (never guessed at):", report["dups"])
    if report["unlinked"]:
        print("unlinked (owner-managed, fill shifra in the CRM to link):")
        for wid in report["unlinked"]:
            print("  -", wid)

    if not changed:
        print("already reconciled — zero diff by design")
        return
    regenerate(watches, f"reconciled: {len(changed)} flag(s) flipped → {changed}")


if __name__ == "__main__":
    main()
