#!/usr/bin/env python3
"""[DB-010] gen_sitemap.py — the single owner of sitemap.xml.
DOES:   enumerates every indexable page on disk, derives alternates from each
        page's own hreflang tags, lifts product images from Product JSON-LD,
        dates URLs from content fingerprints kept in sitemap_state.json, and
        SKIPs the write when nothing changed.

gen_sitemap.py
Owns sitemap.xml. Enumerates every indexable page on disk, reads each page's own
hreflang tags for its alternates, lifts product images from Product JSON-LD, and
dates each URL from a content fingerprint.

Why: the 462 url blocks used to be hand-typed. Adding a watch meant hand-writing
six of them and adding an article three, nothing checked that a new page had been
listed at all, and lastmod was whatever someone typed. Nine entries carried a
FUTURE date, the three blog indexes claimed 2026-07-27 the day after they were
rebuilt, and 297 were frozen at 2026-07-10.

The single source of truth for alternates is the page itself. A sitemap that
derives them cannot disagree with the page it describes, which is the whole class
of bug that the July hreflang break belonged to.

lastmod comes from a content fingerprint stored in sitemap_state.json, not from
the file mtime and not from the git date. A fingerprint ignores cache-bust ?v=
params, so the shared.css v55 to v56 sweep, which touched 475 files without
changing a word, correctly moves no date. It is deliberately whole-file rather
than body-only: an hreflang or canonical repair lives entirely in the head and is
exactly the kind of change we most want recrawled.

changefreq and priority are here for completeness. Google ignores both. Do not
spend time tuning them.

Run from the repo:
    python gen_sitemap.py --seed     once, walks git history to date every URL
    python gen_sitemap.py            normal run, SKIPs when nothing changed
    python gen_sitemap.py --freeze   recompute fingerprints, hold every date
"""
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent
SITE = "https://watch.al/"
TODAY = date.today().isoformat()
STATE = BASE / "sitemap_state.json"
OUT = BASE / "sitemap.xml"

# The apex is listed as a synthetic entry, NOT enumerated from disk. The edge
# 301s https://watch.al/ to /en/, so root index.html is never served there and
# stays noindex: Google is redirected before it ever sees the meta tag, so there
# is no "submitted URL marked noindex". The entry declares the canonical entry
# point and resolves to /en/, which GSC reports as the benign "Page with
# redirect". Its date tracks /en/, since that is the content a crawler receives.
#
# It carries no alternates: a self-referencing x-default would put two
# conflicting x-default in the home cluster, and folding it into that cluster
# would need a contentless shim to self-canonicalise against /en/.
APEX_TRACKS = "en/index.html"
NO_ALTERNATES = frozenset({SITE})

# Commercial-intent articles the owner ranks above the rest. Not derivable from
# blog_index_data.cat: four are buying, three knowledge, one gifts. This set IS
# the editorial decision.
COMMERCIAL = frozenset({
    "watch-price-tiers-60-190",
    "best-watches-under-200-albania",
    "best-watch-gifts-men-albania",
    "best-watch-gifts-women-albania",
    "where-to-buy-watch-durres",
    "hislon-vs-navimarine",
    "best-budget-watches-durres-under-100",
    "watch-gift-durres-same-day",
    "watch-wedding-gift-albania",
    "matching-watches-for-couples",
    "graduation-watch-ideas",
    "are-daniel-klein-watches-good",
    "which-navimarine-to-buy",
    "hislon-classic-review",
    "buy-watches-albania",
    "buy-watch-instagram-albania",
    "buy-watch-without-trying-on",
    "watches-i-would-buy-myself",
    "casio-vs-citizen",
    "seiko-vs-citizen-vs-casio",
    "summer-sea-watch-guide",
    "smartwatch-vs-traditional-watch",
    "watch-as-investment-guide",
    "first-watch-teenager",
    "repair-or-buy-new-watch-durres",
    "how-much-to-spend-on-a-watch-gift",
    "milestone-birthday-watch-gift",
    "watch-birthday-gift-albania",
    "mens-watches-albania", "womens-watches-albania", "watches-under-10000-lek",
    "chronograph-vs-three-hand-watch", "what-makes-a-watch-look-expensive",
    "how-long-does-a-cheap-watch-last", "gold-or-steel-watch",
    "new-year-watch-gifts-albania", "philippe-lauren-watches-albania",
    "cash-on-delivery-watches-albania", "watch-returns-exchange-guarantee",
    "why-buy-from-a-watchmaker", "bigotti-watches-albania",
    "daniel-klein-vs-philippe-lauren", "blue-dial-watches-albania",
    "quartz-watch-accuracy", "first-job-watch", "watch-for-working-hands",
    "buy-watch-tirana", "buy-watches-anywhere-albania",
})

SECTIONS = ["apex", "home", "static", "shopindex", "brand", "product", "shopinfo",
            "servicechild", "blogindex", "blogarticle"]
BANNERS = {
    "apex": "SITE ROOT", "home": "HOME PAGES", "static": "TOP LEVEL PAGES",
    "shopindex": "SHOP INDEX", "brand": "BRAND LANDING PAGES",
    "product": "PRODUCT PAGES", "shopinfo": "SHOP INFO PAGES",
    "servicechild": "SERVICE PAGES", "blogindex": "BLOG INDEX PAGES",
    "blogarticle": "BLOG ARTICLES",
}
STATIC_ORDER = ["services.html", "about.html", "b2b.html"]

ASSET_V = re.compile(r"\?v=\d+")  # the only query-string form on any asset in the repo


# [DB-010.a] fingerprint_text — content hash that ignores non-content churn
# DOES:   normalizes line endings, strips ?v= cache-bust params and collapses
#         whitespace before hashing, so a cache-bust sweep moves no lastmod.
def fingerprint_text(t):
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    t = ASSET_V.sub("", t)              # a cache-bust sweep is not a content change
    return hashlib.sha256(re.sub(r"\s+", " ", t).strip().encode("utf-8")).hexdigest()


# [DB-010.b] fingerprint — fingerprint_text over a file on disk (BOM-tolerant)
def fingerprint(p):
    return fingerprint_text(p.read_bytes().decode("utf-8-sig"))


# [DB-010.c] url_of — disk path -> canonical URL (index.html becomes the directory)
def url_of(p):
    rel = p.relative_to(BASE).as_posix()
    return SITE + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)


def classify(en_path):
    """[DB-010.d] en_path is the EN URL minus https://watch.al/en/ ; '' for the language home.

    Returns (section, changefreq, priority); unclassifiable paths are a hard error
    so a new page type must be placed deliberately."""
    if en_path == "":
        return "home", "monthly", "1.0"
    if en_path == "services.html":
        return "static", "monthly", "0.8"
    if en_path == "about.html":
        return "static", "yearly", "0.7"
    if en_path == "b2b.html":
        return "static", "yearly", "0.6"
    if en_path == "shop/":
        return "shopindex", "weekly", "0.9"
    if en_path.startswith("shop/brand/"):
        return "brand", "monthly", "0.8"
    if en_path == "shop/delivery.html":
        return "shopinfo", "monthly", "0.8"
    if en_path.startswith("shop/"):
        return "product", "monthly", "0.8"
    if en_path.startswith("services/"):
        return "servicechild", "monthly", "0.8"
    if en_path == "blog/":
        return "blogindex", "monthly", "0.7"
    if en_path.startswith("blog/"):
        slug = en_path[len("blog/"):-len(".html")]
        return "blogarticle", "yearly", ("0.7" if slug in COMMERCIAL else "0.6")
    raise AssertionError(f"unclassified family: {en_path!r}")


def collect():
    """[DB-010.e] Every indexable page, grouped into families keyed by the EN url.

    Skips noindex pages, asserts every page self-canonicalises (apex excepted) and
    that every family has exactly en/it/sq + x-default==en."""
    pages = {}
    for p in sorted(BASE.rglob("*.html")):
        t = p.read_bytes().decode("utf-8-sig")
        m = re.search(r'<meta name="robots" content="([^"]*)"', t)
        if m and "noindex" in m.group(1).lower():
            continue
        # The 171 product pages carry id= between the attributes, because watch.js
        # rewrites these links at runtime. Never anchor on a single space here.
        alts = re.findall(r'<link rel="alternate" hreflang="([\w-]+)"[^>]*?href="([^"]+)"', t)
        canon = re.search(r'<link rel="canonical"[^>]*?href="([^"]+)"', t)
        u = url_of(p)
        # The apex deliberately canonicalises to /en/; every other page self-canonicalises.
        if u not in NO_ALTERNATES:
            assert canon and canon.group(1) == u, f"{p}: canonical {canon and canon.group(1)} != {u}"
        pages[u] = dict(path=p, alts=dict(alts), text=t)

    # synthetic apex: its own file is noindex and never served at /, see APEX_TRACKS
    pages[SITE] = dict(path=BASE / APEX_TRACKS, alts={}, text="")
    fams, singles = {}, [SITE]
    for u, d in sorted(pages.items()):
        if u in NO_ALTERNATES:
            continue
        a = d["alts"]
        assert sorted(a) == ["en", "it", "sq", "x-default"], f"{d['path']}: hreflang {sorted(a)}"
        assert u in a.values(), f"{d['path']}: own url not among its alternates"
        assert a["x-default"] == a["en"], f"{d['path']}: x-default != en"
        fams.setdefault(a["en"], []).append(u)
    for en, members in fams.items():
        assert len(members) == 3, f"family {en} has {len(members)} members: {members}"
    return pages, fams, singles


def product_image(d):
    """[DB-010.f] The Product JSON-LD image, asserted equal to og:image and present on disk."""
    for b in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>',
                        d["text"], re.S):
        try:
            data = json.loads(b)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("@type") == "Product":
            img = data["image"]
            # id= sits between property and content on product pages; [^>]* keeps
            # the match inside the one tag.
            og = re.search(r'property="og:image"[^>]*content="([^"]+)"', d["text"])
            assert og and og.group(1) == img, f"{d['path']}: og:image != Product image"
            assert (BASE / img[len(SITE):]).exists(), f"{d['path']}: {img} missing on disk"
            return img
    return None


def ordered_families(fams):
    """[DB-010.g] Deterministic order: a new watch appends, a new article inserts cleanly."""
    watch_order = {w["id"]: i for i, w in enumerate(
        json.loads((BASE / "watches.json").read_text(encoding="utf-8")))}
    buckets = {s: [] for s in SECTIONS}
    for en in fams:
        p = en[len(SITE + "en/"):]
        sec, cf, pr = classify(p)
        buckets[sec].append((en, p, cf, pr))
    key = {
        "home": lambda x: 0,
        "static": lambda x: STATIC_ORDER.index(x[1]),
        "shopindex": lambda x: 0,
        "brand": lambda x: x[1],
        "product": lambda x: watch_order[x[1][len("shop/"):-len(".html")]],
        "shopinfo": lambda x: 0,
        "servicechild": lambda x: x[1],
        "blogindex": lambda x: 0,
        "blogarticle": lambda x: x[1],
    }
    return {s: sorted(buckets[s], key=key[s]) for s in SECTIONS if s != "apex"}


# [DB-010.h] render — the full sitemap.xml text (CRLF)
# DOES:   apex first, then each section under its banner comment; every url block
#         carries lastmod/changefreq/priority, the four alternates (except the
#         apex), and an image:image for product pages.
def render(pages, fams, singles, dates):
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
         '        xmlns:xhtml="http://www.w3.org/1999/xhtml"',
         '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">']
    labels = {w["id"]: f'{w["brand"]} {w["model"]}'.strip() for w in
              json.loads((BASE / "watches.json").read_text(encoding="utf-8"))}

    def block(u, cf, pr):
        d = pages[u]
        out = ["  <url>", f"    <loc>{u}</loc>", f"    <lastmod>{dates[u]}</lastmod>",
               f"    <changefreq>{cf}</changefreq>", f"    <priority>{pr}</priority>"]
        if u not in NO_ALTERNATES:
            for hl in ("en", "it", "sq", "x-default"):
                out.append(f'    <xhtml:link rel="alternate" hreflang="{hl}" '
                           f'href="{d["alts"][hl]}"/>')
        img = product_image(d) if "/shop/" in u and u.endswith(".html") else None
        if img:
            out += ["    <image:image>", f"      <image:loc>{img}</image:loc>",
                    "    </image:image>"]
        out.append("  </url>")
        return out

    L += ["", f"  <!-- {'─' * 12} {BANNERS['apex']} {'─' * 12} -->"]
    for u in singles:
        L += block(u, *classify_apex())
    for sec, fam_list in ordered_families(fams).items():
        L += ["", f"  <!-- {'─' * 12} {BANNERS[sec]} {'─' * 12} -->"]
        for en, p, cf, pr in fam_list:
            label = p
            if sec == "product":
                label = f'{p} - {labels[p[len("shop/"):-len(".html")]]}'
            L += [f"  <!-- {label} -->"]
            for u in sorted(fams[en], key=lambda x: ("/en/" not in x, "/it/" not in x)):
                L += block(u, cf, pr)
    L += ["", "</urlset>", ""]
    return "\r\n".join(L)


# [DB-010.i] classify_apex — changefreq/priority for the synthetic apex entry
def classify_apex():
    return "monthly", "1.0"


# ------------------------------------------------------------------ state / dates
# [DB-010.j] load_state — sitemap_state.json ({url: {fp, lastmod}}), or empty
def load_state():
    if not STATE.exists():
        return {}
    return json.loads(STATE.read_text(encoding="utf-8"))


def write_state(state):
    """[DB-010.k] No timestamp field: it would churn the diff and defeat SKIP."""
    txt = json.dumps(state, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    out = txt.replace("\n", "\r\n").encode("utf-8")
    if STATE.exists() and json.loads(STATE.read_text(encoding="utf-8")) == state:
        return False
    STATE.write_bytes(out)
    return True


# [DB-010.l] git — run git in the repo, stdout as text (errors surface as "")
def git(*args):
    r = subprocess.run(["git", *args], cwd=BASE, capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def seed_date(rel, fp_now, memo):
    """[DB-010.m] Newest commit at which this file's fingerprint actually changed.

    Walks newest-first and exits at the first real change, which is typically one
    to three commits back because the newest commits touching any page are the
    cache-bust sweeps.
    """
    revs = [l.split(" ", 1) for l in git("log", "--format=%as %H", "--", rel).splitlines()]
    if not revs:
        return TODAY

    def at(rev):
        k = (rev, rel)
        if k not in memo:
            blob = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=BASE,
                                  capture_output=True).stdout
            memo[k] = fingerprint_text(blob.decode("utf-8-sig", "replace")) if blob else None
        return memo[k]

    if at(revs[0][1]) != fp_now:
        return TODAY                      # uncommitted content change
    for (d_i, r_i), (_, r_j) in zip(revs, revs[1:]):
        if at(r_i) != at(r_j):
            return d_i                    # r_i is where the content moved
    return revs[-1][0]                    # never changed since it was added


# [DB-010.n] main — date every URL (seed/freeze/normal rules), render, SKIP-write
# DOES:   per URL: new page -> today, unchanged fingerprint (or --freeze) -> held
#         date, changed -> today; prunes state for pages that left disk; writes
#         sitemap.xml and sitemap_state.json only when their bytes changed.
def main():
    seed, freeze = "--seed" in sys.argv, "--freeze" in sys.argv
    if seed and STATE.exists():
        sys.exit(f"{STATE.name} exists; --seed refuses to overwrite it")
    if freeze:
        print("!! --freeze: fingerprints recorded, every lastmod held !!")

    pages, fams, singles = collect()
    state, memo, dates = load_state(), {}, {}
    urls = sorted(pages)
    for i, u in enumerate(urls, 1):
        d = pages[u]
        fp = fingerprint(d["path"])
        rel = d["path"].relative_to(BASE).as_posix()
        prev = state.get(u)
        if seed:
            dates[u] = seed_date(rel, fp, memo)
            if i % 50 == 0:
                print(f"  seeded {i}/{len(urls)}")
        elif prev is None:
            dates[u] = TODAY                                  # new page
        elif freeze or prev["fp"] == fp:
            dates[u] = prev["lastmod"]                        # unchanged content
        else:
            dates[u] = TODAY                                  # real content change
        assert dates[u] <= TODAY, f"{u}: lastmod {dates[u]} is in the future"
        state[u] = {"fp": fp, "lastmod": dates[u]}
    for gone in set(state) - set(urls):
        del state[gone]

    xml = render(pages, fams, singles, dates)
    assert "—" not in xml and "&#8212;" not in xml and "&mdash;" not in xml
    out = b"\xef\xbb\xbf" + xml.encode("utf-8")
    assert out.count(b"\n") == out.count(b"\r\n") and b"\x0c" not in out
    if OUT.exists() and OUT.read_bytes() == out:
        print(f"  SKIP {OUT.name}")
    else:
        OUT.write_bytes(out)
        print(f"  WROTE {OUT.name}: {len(urls)} urls")
    print(f"  {'WROTE' if write_state(state) else 'SKIP'} {STATE.name}")


if __name__ == "__main__":
    main()
