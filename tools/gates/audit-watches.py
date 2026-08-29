#!/usr/bin/env python3
"""[ERR-007] audit-watches.py — the catalogue's cross-file integrity audit.
DOES:   ten numbered check groups over watches.json <-> watches-data.js <-> the
        three product pages <-> sitemap.xml <-> the image files. 1 id sets match,
        2 field-by-field drift between the two data files, 3 per-watch images +
        hreflang + Product JSON-LD + og:price + exactly 3 sitemap locs, 4 orphan
        shop pages, 5 orphan images, 6 shop.js parses, 7 sitewide JSON-LD parses,
        8 one watches-data.js ?v= sitewide, 9 the localized <title> formula, 10
        brand landing pages still in sync with stock.
IN:     no args. Invoked from the WORKING ROOT:
        python tools/gates/audit-watches.py
        BASE is ../mina.github.io resolved from __file__, so the git repo is
        always the subject and the caller's directory never is. Read-only: this
        gate opens nothing for writing.
OUT:    one "  FINDING: ..." line per problem as it is found, then either
        "AUDIT CLEAN - 0 findings" or "AUDIT: <n> findings". Exit 1 on findings.
CALLS:  catalog_stats.lek, imported lazily inside lek(); node --check through
        subprocess when node is on PATH, and check 6 silently does nothing when it
        is not.
NOTES:  Check 6 parses shop.js and NOTHING ELSE. watch.js was the second renderer
        and was deleted 2026-08-04, so the one-element tuple is deliberate: a
        renderer coming back has to be typed in here by hand. The check exists at
        all because it/sq watch.js shipped syntactically broken for months and no
        text-based check could see it.
        Check 8 exists because a half-finished ?v= bump made new watches read
        "Watch not found" for cached visitors (2026-07-24).
        Nothing here repairs anything, on purpose: a finding names the generator
        that owns the file, and rerunning that generator stays a human decision.
        The product pages get their own assertions in [ERR-008] and the sitemap
        gets its own in [ERR-009]; the three overlap deliberately so no single
        gate is the only thing between a bug and production.

audit-watches.py
Full integrity audit of the watch catalog: watches.json <-> watches-data.js <->
product pages (en/it/sq) <-> sitemap <-> image files. Prints findings; exits 1
if any. Run from repo parent: python tools/gates/audit-watches.py
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
import corpus  # noqa: E402  - shared read cache, see [PERF-004]
LANGS = ("en", "it", "sq")
# No LEK_RATE here on purpose. lek() below imports catalog_stats, so a constant
# at this level could only ever be a stale second opinion; one sat here reading
# 97 for the whole life of the 92.25 change and was used by nothing.

findings = []


# [ERR-007.a] flag — record one finding and print it the moment it is found
# NOTES:  Prints as it goes instead of buffering, so a run that dies inside a
#         later group still leaves the reader everything it had already proved.
#         findings is what drives the exit code; printing is not enough.
def flag(msg):
    findings.append(msg)
    print("  FINDING:", msg)


# [ERR-007.b] lek — the Lek price, from the module that owns the formula
# NOTES:  Imported inside the call, never copied. The half-up conversion had SIX
#         copies once and they had already begun to disagree about whether a sold
#         watch counts; a gate carrying a seventh could only confirm its own
#         drift.
def lek(price):
    # one definition, in mina.github.io/catalog_stats.py
    sys.path.insert(0, str(BASE))
    from catalog_stats import lek as _l
    return _l(price)


# [ERR-007.c] jsonld_blocks — every non-empty application/ld+json block on a page
# NOTES:  Whitespace-only blocks are skipped deliberately: the shop index ships an
#         empty shop-ld-list block for the runtime to fill, and calling that a
#         parse error would leave check 7 permanently red and therefore ignored.
def jsonld_blocks(html):
    return [b for b in re.findall(
        r'<script type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S) if b.strip()]


# [ERR-007.d] main — run the ten groups in source order, then set the exit code
# DOES:   loads both data files first so every later group may assume they exist
#         and parsed; the group numbers in the comments are how these findings get
#         talked about in commits, so do not renumber them.
# NOTES:  Group 3 is the expensive one (3 pages x every watch) and everything
#         after it assumes those pages were readable. Group 9 rebuilds the
#         expected title from watches.json rather than trusting the page, which is
#         what catches a stale price and an un-localized SQ/IT title in the same
#         assertion.
def main():
    # --- load both data files ---
    j = {x["id"]: x for x in json.loads(corpus.sig((BASE / "watches.json")))}
    t = corpus.sig((BASE / "watches-data.js"))
    d = {x["id"]: x for x in json.loads(t[t.index("["):t.rindex("]") + 1])}

    print(f"watches.json: {len(j)} | watches-data.js: {len(d)}")

    # --- 1. id sets match ---
    for i in sorted(set(j) - set(d)):
        flag(f"{i}: in watches.json but missing from watches-data.js")
    for i in sorted(set(d) - set(j)):
        flag(f"{i}: in watches-data.js but missing from watches.json")

    # --- 2. field consistency ---
    for i in sorted(set(j) & set(d)):
        for k in ("brand", "model", "reference", "price", "image", "sold", "condition", "currency"):
            if j[i].get(k) != d[i].get(k):
                flag(f"{i}.{k} drift: json={j[i].get(k)!r} js={d[i].get(k)!r}")

    sitemap = corpus.sig((BASE / "sitemap.xml"))

    # --- 3. per-watch checks ---
    for i, w in sorted(j.items()):
        img_base = w["image"].rsplit("/", 1)[-1]
        stem = img_base.rsplit(".", 1)[0]
        for ext in ("webp", "jpg"):
            if not (BASE / "images" / "watches" / f"{stem}.{ext}").exists():
                flag(f"{i}: image file missing: images/watches/{stem}.{ext}")

        # [DB-006] A retired watch keeps its record but its pages are noindex
        # stubs by design, built by gen_product_pages from shop_bits.stub_html.
        # Every check below assumes a rendered product page, so without this a
        # correctly archived watch reports as broken. Assert the retired
        # contract instead: three stubs present, and gone from the sitemap.
        if w.get("deleted"):
            for lang in LANGS:
                page = BASE / lang / "shop" / f"{i}.html"
                if not page.exists():
                    flag(f"{i}: retired, but {lang}/shop/{i}.html is missing")
                elif "noindex" not in corpus.sig(page):
                    flag(f"{i}: retired, but {lang}/shop/{i}.html is not a stub. "
                         f"Rerun gen_product_pages.py.")
            still = len(re.findall(
                rf"<loc>https://watch\.al/(?:en|it|sq)/shop/{re.escape(i)}\.html</loc>",
                sitemap))
            if still:
                flag(f"{i}: retired but still in the sitemap ({still} blocks). "
                     f"Rerun gen_sitemap.py.")
            continue

        for lang in LANGS:
            page = BASE / lang / "shop" / f"{i}.html"
            if not page.exists():
                flag(f"{i}: page missing: {lang}/shop/{i}.html")
                continue
            html = corpus.sig(page)

            # hreflang completeness + targets (id= attr may sit between hreflang and href)
            hl = dict(re.findall(r'hreflang="(en|it|sq)"[^>]*?href="([^"]+)"', html))
            if sorted(hl) != list(LANGS):
                flag(f"{i} [{lang}]: hreflang set {sorted(hl)} != en/it/sq")
            for hlang, url in hl.items():
                tgt = url.replace("https://watch.al/", "")
                if not (BASE / tgt).exists():
                    flag(f"{i} [{lang}]: hreflang {hlang} target missing: {tgt}")

            # product JSON-LD
            prod = None
            for b in jsonld_blocks(html):
                try:
                    data = json.loads(b)
                except Exception as e:
                    flag(f"{i} [{lang}]: JSON-LD parse error: {str(e)[:60]}")
                    continue
                if isinstance(data, dict) and data.get("@type") == "Product":
                    prod = data
            if prod is None:
                flag(f"{i} [{lang}]: no Product JSON-LD block")
                continue

            expected_name = f'{w["brand"]} {w["model"]}'.strip()
            if not prod.get("name", "").startswith(expected_name):
                flag(f"{i} [{lang}]: JSON-LD name {prod.get('name')!r} != {expected_name!r}")
            ref = w.get("reference", "")
            if ref and prod.get("sku") != ref:
                flag(f"{i} [{lang}]: sku {prod.get('sku')!r} != {ref!r}")
            if not ref and "sku" in prod:
                flag(f"{i} [{lang}]: sku present but reference empty")
            off = prod.get("offers", {})
            if not prod.get("image", "").endswith(w["image"].rsplit("/", 1)[-1]):
                flag(f"{i} [{lang}]: JSON-LD image {prod.get('image')!r} != {w['image']!r}")

            # A watch with no price yet publishes NO Offer and NO price meta,
            # rather than an Offer quoting 0. Asserting the priced shape here
            # reported nine findings against the Cortébert rectangular
            # (2026-08-25) for doing exactly the right thing. What must still be
            # true is the negative: nothing anywhere may state a figure.
            if not w.get("price"):
                if off:
                    flag(f"{i} [{lang}]: unpriced watch still carries an Offer")
                if re.search(r'property="product:price:amount"', html):
                    flag(f"{i} [{lang}]: unpriced watch still carries a price meta")
                continue

            if str(off.get("price")) != str(w["price"]):
                flag(f"{i} [{lang}]: offer price {off.get('price')!r} != {w['price']}")
            alls = [p["price"] for p in off.get("priceSpecification", [])
                    if p.get("priceCurrency") == "ALL"]
            if alls and str(alls[0]) != str(lek(w["price"])):
                flag(f"{i} [{lang}]: ALL price {alls[0]!r} != {lek(w['price'])}")
            pvu = off.get("priceValidUntil")
            if not pvu:
                flag(f"{i} [{lang}]: Offer missing priceValidUntil")
            elif pvu < __import__("datetime").date.today().isoformat():
                flag(f"{i} [{lang}]: priceValidUntil expired ({pvu}) - refresh scripts/add-price-valid-until.py")

            og = re.search(r'property="product:price:amount" content="([^"]*)"', html)
            if not og:
                flag(f"{i} [{lang}]: missing og product:price:amount meta")
            elif og.group(1) != str(w["price"]):
                flag(f"{i} [{lang}]: og price {og.group(1)!r} != {w['price']}")

        # sitemap coverage
        n_url = len(re.findall(rf"<loc>https://watch\.al/(?:en|it|sq)/shop/{re.escape(i)}\.html</loc>", sitemap))
        if n_url != 3:
            flag(f"{i}: sitemap has {n_url} <url> blocks (expect 3)")

    # --- 4. orphan shop pages (pages without data) ---
    for lang in LANGS:
        for p in sorted((BASE / lang / "shop").glob("*.html")):
            # index.html, the legacy ?id= query-param template (special-cased in watch.js),
            # and delivery.html, the hand-built ordering/payment/returns page
            if p.stem in ("index", "watch", "delivery") or p.stem in j:
                continue
            html = corpus.sig(p)
            if 'http-equiv="refresh"' in html and 'noindex' in html:
                continue  # intentional redirect stub
            flag(f"orphan page without data: {lang}/shop/{p.name}")

    # --- 5. orphan images ---
    refs = set()
    for f in list(corpus.html_files()) + [BASE / "watches.json", BASE / "watches-data.js"]:
        refs.update(re.findall(r"images/watches/([\w.\-]+\.(?:webp|jpg|jpeg))",
                               f.read_text(encoding="utf-8", errors="ignore")))
    # [DB-006] A retired watch keeps both files. watches.json still names the
    # .webp, but the .jpg was only ever referenced by the product page <img>,
    # and a stub has none, so it would read as orphaned and get deleted. The
    # image is exactly what a restore needs, so both extensions of every
    # record's image count as referenced.
    for w in j.values():
        stem = w.get("image", "").rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if stem:
            refs.update({f"{stem}.webp", f"{stem}.jpg"})
    for p in sorted((BASE / "images" / "watches").iterdir()):
        if p.name not in refs:
            flag(f"orphan image: images/watches/{p.name}")

    # --- 6. shop JS files must parse (it/sq watch.js shipped broken for months once) ---
    import shutil
    import subprocess
    if shutil.which("node"):
        for lang in LANGS:
            # watch.js was deleted 2026-08-04: it re-rendered pages that were already
            # correct and every difference it introduced was a bug.
            for name in ("shop.js",):
                f = BASE / lang / "shop" / name
                r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
                if r.returncode != 0:
                    flag(f"{lang}/shop/{name}: SYNTAX ERROR - {r.stderr.splitlines()[-1][:80]}")

    # --- 7. site-wide JSON-LD must parse (blog indexes shipped a broken ItemList array once) ---
    # --- 8. watches-data.js cache-bust version must be identical on every page (a stale/partial
    #        version made new watches show "Watch not found" for cached visitors, 2026-07-24) ---
    dv = {}
    for f in corpus.html_files():
        html = corpus.sig(f)
        for b in jsonld_blocks(html):  # helper skips intentionally-empty blocks (JS-filled shop-ld-list)
            try:
                json.loads(b)
            except Exception as e:
                flag(f"JSON-LD parse error in {f.relative_to(BASE).as_posix()}: {str(e)[:80]}")
        for v in re.findall(r"watches-data\.js\?v=(\d+)", html):
            dv.setdefault(v, f.relative_to(BASE).as_posix())
    if len(dv) > 1:
        flag(f"watches-data.js version mismatch: {', '.join(f'v={v} (e.g. {p})' for v, p in sorted(dv.items()))}")

    # --- 9. product <title> must equal the localized formula built from watches.json
    #        (catches stale prices, un-localized SQ/IT titles, and generator drift) ---
    tails = {"en": "Buy in Durrës, Albania", "it": "Orologi a Durazzo", "sq": "Blej Orë në Durrës"}
    names = {}
    for w in j.values():
        n = f'{w["brand"]} {w["model"]}'.strip()
        names[n] = names.get(n, 0) + 1
    for i, w in j.items():
        name = f'{w["brand"]} {w["model"]}'.strip()
        if w.get("reference") and names[name] > 1:
            name += f' {w["reference"]}'
        price = f' - €{w["price"]}' if w.get("price") else ""
        if w.get("deleted"):
            continue          # [DB-006] a stub carries a plain <title>, by design
        for lang in LANGS:
            page = BASE / lang / "shop" / f"{i}.html"
            if not page.exists():
                continue
            html = corpus.sig(page)
            m = re.search(r'<title id="page-title">([^<]*)</title>', html)
            if not m:
                flag(f"{i} [{lang}]: no <title id=\"page-title\">")
                continue
            want = f"{name}{price} | {tails[lang]}"
            if m.group(1) != want:
                flag(f"{i} [{lang}]: title {m.group(1)!r} != {want!r}")

    # --- 10. brand landing pages must exist and stay in sync with the catalog ---
    # --- 11. styles: fixed vocabulary, and chronograph strictly the verified list.
    # The published chronograph/lookalike split got it wrong once; the style tag
    # must never re-open that door. Verified ids are owner-confirmed at the bench.
    STYLE_VOCAB = {'chronograph', 'dress', 'sport', 'digital', 'gold-tone', 'moonphase'}
    VERIFIED_CHRONOGRAPHS = {'philippe-lauren-pl2427-5', 'philippe-lauren-pl2427-1',
                             'philippe-lauren-pl2435-2', 'philippe-lauren-pl2435-5',
                             'watch-23', 'daniel-klein-14243', 'watch-4',
                             'cortebert-black-bezel-chronograph', 'pulsar-crystal-chronograph'}
    styled_chronos = set()
    for w in j.values():
        for s in w.get('styles', []):
            if s not in STYLE_VOCAB:
                flag(f"{w['id']}: unknown style {s!r}")
        if 'chronograph' in w.get('styles', []):
            styled_chronos.add(w['id'])
    if not styled_chronos <= VERIFIED_CHRONOGRAPHS:
        flag(f"chronograph style on unverified watch(es): {sorted(styled_chronos - VERIFIED_CHRONOGRAPHS)}")

    brand_slugs = {"daniel-klein": "Daniel Klein", "navimarine": "Navimarine",
                   "hislon": "Hislon", "philippe-lauren": "Philippe Lauren",
                   "bigotti": "Bigotti",
                   "cortebert": "Cortébert", "pulsar": "Pulsar",
                   "polotime": "POLOTIME"}
    for slug, brand in brand_slugs.items():
        # [DB-006] gen_brand_pages drops retired watches from the hub, so they
        # must not be expected here either.
        expect = [w for w in j.values()
                  if w["brand"] == brand and not w.get("sold") and not w.get("deleted")]
        for lang in LANGS:
            page = BASE / lang / "shop" / "brand" / f"{slug}.html"
            if not page.exists():
                flag(f"brand page missing: {lang}/shop/brand/{slug}.html")
                continue
            html = corpus.sig(page)
            cards = html.count('<article class="watch-card')
            if cards != len(expect):
                flag(f"brand {slug} [{lang}]: {cards} cards != {len(expect)} in stock "
                     f"(rerun gen_brand_pages.py)")
            for w in expect:
                if f'href="/{lang}/shop/{w["id"]}.html"' not in html:
                    flag(f"brand {slug} [{lang}]: missing link to {w['id']}")
            if "shop.js" in html:
                flag(f"brand {slug} [{lang}]: loads shop.js (would wipe the static grid)")

    print(f"\n{'AUDIT CLEAN - 0 findings' if not findings else f'AUDIT: {len(findings)} findings'}")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
