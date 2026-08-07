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
# NOTES:  Byte formats are load-bearing: watches.json = no BOM, CRLF,
#         json.dumps(indent=2, ensure_ascii=False); watches-data.js = BOM,
#         CRLF, the AUTO-GENERATED wrapper. tools/test_sync_stock.py pins
#         both plus the flip semantics. Contract: part-tracker repo,
#         docs/CRM_SYNC.md.
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
FEED = "https://api.watch.al/public/stock"
GENERATORS = ("gen_shop_index.py", "gen_product_pages.py",
              "gen_brand_pages.py", "gen_sitemap.py")


def norm(s):
    return str(s or "").strip().upper()


def apply_stock(watches, stock):
    """Pure core: mutate `sold` on linked entries; return (changed_ids, report).

    Linked = the entry's normalized reference is a key of `stock` AND unique
    among site entries. Duplicated refs are never guessed at; absent refs are
    left owner-managed. Both directions: 0 → sold, >0 → back on sale.
    """
    seen = {}
    for w in watches:
        r = norm(w.get("reference"))
        if r:
            seen.setdefault(r, []).append(w.get("id"))
    dups = {r: ids for r, ids in seen.items() if len(ids) > 1}

    changed, linked, unlinked = [], [], []
    for w in watches:
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


def json_bytes(data):
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").replace("\n", "\r\n").encode("utf-8")


def data_js_bytes(data):
    core = json.dumps(data, indent=2, ensure_ascii=False)
    body = "/* AUTO-GENERATED */\nwindow.WATCHES_DATA = " + core + ";\n"
    return b"\xef\xbb\xbf" + body.replace("\n", "\r\n").encode("utf-8")


def main():
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
    (BASE / "watches.json").write_bytes(json_bytes(watches))
    (BASE / "watches-data.js").write_bytes(data_js_bytes(watches))
    for g in GENERATORS:
        print(f"— {g} —")
        subprocess.run([sys.executable, str(BASE / g)], cwd=BASE, check=True)
    print(f"reconciled: {len(changed)} flag(s) flipped → {changed}")


if __name__ == "__main__":
    main()
