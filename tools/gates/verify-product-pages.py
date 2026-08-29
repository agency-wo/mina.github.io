#!/usr/bin/env python3
"""[ERR-008] verify-product-pages.py — the assertion gate for the product pages.
DOES:   eight numbered checks per page across the 58 ids in watches.json x
        en/it/sq (174 pages): 1 bytes (BOM, EOL consistency, form feed, em dash,
        U+FFFD), 2 exactly one renderer, 3 no executable inline <script>, 4 every
        icon is inside the subsetted font, 5 the price line, 6 Product JSON-LD, 7
        social cards that resolve without JS, 8 no orphan Ref. line on a watch
        with no reference.
IN:     no args. Invoked from the WORKING ROOT:
        python tools/gates/verify-product-pages.py
        Reads watches.json and shared.css. The glyph whitelist is DERIVED from
        shared.css, never hardcoded, so re-subsetting the font moves the gate with
        it.
OUT:    a "  FINDING: ..." line per problem, a page and glyph tally, then
        "PRODUCT PAGE GATE PASS" or "<n> FINDINGS". Exit 1 on findings.
CALLS:  catalog_stats.nfmt, so the expected thousands separator comes from the one
        table the generators use (comma in EN, dot in IT and SQ).
NOTES:  Check 4 is the ONLY glyph gate on the site, and its regex is narrower than
        it looks:
        class="fa[sb]? (fa-[a-z0-9-]+)" is anchored on the opening quote, so it
        only ever sees a class attribute whose FIRST token is fa, fas or fab.
        Sitewide that is 12,437 of 15,074 icon class attributes; the other 2,637
        (the glyph written first, another class in front of it, the
        fa-solid/fa-brands spellings) are invisible to it.
        That is a KNOWN coverage hole, recorded here on purpose and NOT to be
        quietly widened: a class outside the subset renders as NOTHING, no
        text-based check can see it, and it is the most repeated bug in this repo.
        Widening the regex is a re-audit, not a one-line edit. faq-build.py
        --verify ([DB-020]) is the wider net, but only over the faq-icon subset.
        The line-ending assertion checks INTERNAL CONSISTENCY (all-CRLF or
        all-LF), never a fixed shape, because core.autocrlf=true with no
        .gitattributes means the correct bytes depend on which machine checked
        out: LF on the CI runner, CRLF on the owner's Windows tree, and both are
        correct. Mixed inside one file is the only real defect. Same principle as
        tools/sync_stock.py::style_of (see [ERR-004]).
        The loop walks the 58 catalogue ids ONLY. A retired id that still has a
        page on disk is [ERR-007] check 4's problem, not this gate's. The
        preserved header below says 171 pages: the count has always been derived
        from watches.json, and today it is 174.

verify-product-pages.py
Assertion gate for the 171 product pages. Run from repo parent:
    python tools/gates/verify-product-pages.py

Exists because the product page is where a buying decision is made and it had no
gate at all. Two checks here would have caught bugs that shipped and stayed live:

  * NO SECOND RENDERER. watch.js re-rendered pages that were already correct and
    every difference it introduced was a bug (NaN Lek price, dropped sale price,
    deleted opening hours, an em dash on reference-less watches, a locale-dependent
    thousands separator). Static and runtime can only disagree if there are two
    renderers, so the gate refuses to let a second one come back.
  * ICON GLYPHS. Font Awesome is subsetted; a class outside the subset renders as
    nothing and no text check can see it. That is how four rules stayed broken for
    months with a form feed in them.
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
import corpus  # noqa: E402  - shared read cache, see [PERF-004]
ROOT = BASE.parent
LANGS = ("en", "it", "sq")
findings = []


# [ERR-008.a] flag — record one finding and print it as it is found
# NOTES:  Same shape in all five gates ([ERR-007.a]); the " FINDING:" prefix is
#         what a reader greps for after a run that touched several of them.
def flag(m):
    findings.append(m)
    print("  FINDING:", m)


# [ERR-008.b] main — derive the glyph whitelist, then walk 58 ids x 3 languages
# DOES:   parses .fa-*::before out of shared.css first and complains if fewer than
#         50 come back, because an empty whitelist would flag every icon on the
#         site and a near-empty one would quietly approve almost nothing.
# NOTES:  Check 5 restates the half-up Lek arithmetic inline instead of importing
#         catalog_stats.lek. That is the one place a second copy is wanted: a gate
#         that borrows the generator's arithmetic agrees with it by construction
#         and can never catch it being wrong. The separator still comes from nfmt,
#         because that is per-language data rather than arithmetic. SQ must lead
#         with Lek, EN and IT with euro, and the check asserts the lead as well as
#         the value.
def main():
    sys.path.insert(0, str(BASE))
    from catalog_stats import nfmt
    # The "price on request" wording is data, not arithmetic, so unlike the Lek
    # formula above it is imported rather than restated.
    from shop_bits import PRICE_ON_REQUEST as POR, SWISS_BRANDS
    watches = json.loads(corpus.sig((BASE / "watches.json")))
    # [DB-006] retired watches are deliberately noindex stubs, so they are not
    # checked as product pages. They are checked as stubs, just below.
    live = [w for w in watches if not w.get("deleted")]
    ids = [w["id"] for w in live]
    by_id = {w["id"]: w for w in live}
    for w in watches:
        if not w.get("deleted"):
            continue
        for lang in LANGS:
            p = BASE / lang / "shop" / f"{w['id']}.html"
            if not p.exists():
                flag(f"{lang}/shop/{w['id']}.html: retired watch has no page")
            elif "noindex" not in corpus.sig(p):
                flag(f"{lang}/shop/{w['id']}.html: retired watch still has a "
                     f"full page. Rerun gen_product_pages.py.")

    # the subsetted Font Awesome whitelist, derived not hardcoded
    css = corpus.raw((BASE / "shared.css")).decode("utf-8-sig")
    glyphs = set(re.findall(r"\.(fa-[a-z0-9-]+)::before", css))
    brands = set(re.findall(r"\.fab[^{]*\{[^}]*\}", css))
    if len(glyphs) < 50:
        flag(f"only {len(glyphs)} glyphs parsed from shared.css, expected ~64")

    pages = 0
    for lang in LANGS:
        for wid in ids:
            p = BASE / lang / "shop" / f"{wid}.html"
            if not p.exists():
                flag(f"missing page {lang}/shop/{wid}.html")
                continue
            pages += 1
            raw = corpus.raw(p)
            rel = f"{lang}/shop/{wid}.html"
            w = by_id[wid]

            # 1. bytes
            if not raw.startswith(b"\xef\xbb\xbf"):
                flag(f"{rel}: BOM missing")
            # Internal consistency, not a fixed shape. core.autocrlf=true and no
            # .gitattributes mean the byte shape depends on which machine checked
            # out: this tree is LF since the CI runner landed, a Windows-only
            # checkout is CRLF, and both are correct. Mixed within one file is not.
            # Same principle as tools/sync_stock.py::style_of ([ERR-004]).
            if raw.count(b"\r\n") not in (0, raw.count(b"\n")):
                flag(f"{rel}: mixed line endings "
                     f"({raw.count(b'\r\n')} CRLF of {raw.count(b'\n')} LF)")
            if b"\x0c" in raw:
                flag(f"{rel}: form feed byte")
            t = raw.decode("utf-8-sig")
            for bad in ("—", "&#8212;", "&mdash;", "�"):
                if bad in t:
                    flag(f"{rel}: contains {bad!r}")

            # 2. exactly one renderer
            for dead in ("watch.js", "watches-data.js"):
                if dead in t:
                    flag(f"{rel}: loads {dead}, the second renderer is back")
            if "footerYear" in t:
                flag(f"{rel}: #footerYear needs JS that no longer exists")

            # 3. no EXECUTABLE inline script: script-src is 'self' with no
            #    unsafe-inline and no nonce, so one would never run. JSON-LD is
            #    data, not script, and is not governed by script-src.
            n_inline = len([m for m in re.finditer(r"<script(?![^>]*\bsrc=)([^>]*)>", t)
                            if "application/ld+json" not in m.group(1)])
            if n_inline:
                flag(f"{rel}: {n_inline} executable inline <script>, blocked by CSP")

            # 4. icons all exist in the subsetted font
            for cls in re.findall(r'class="fa[sb]? (fa-[a-z0-9-]+)"', t):
                if cls not in glyphs:
                    flag(f"{rel}: icon {cls} is outside the subsetted font")

            # 5. the price, which the deleted renderer used to destroy
            m = re.search(r'class="watch-price-pg"[^>]*>(.*?)</p>', t, re.S)
            if not m:
                flag(f"{rel}: no price element")
            else:
                price = m.group(1)
                # the separator is a comma in EN and a dot in IT and SQ, so this
                # cannot hardcode f"{lek:,}" the way it used to
                # 92.25 is written out here, NOT imported. See the note on main()
                # above: this copy exists so the gate can disagree with
                # catalog_stats rather than agree with it by construction. If the
                # two ever diverge this check fails loudly on all 183 pages,
                # which is the intended alarm, not a bug. Update both together.
                lek = int(w["price"] * 92.25 / 100 + 0.5) * 100 if w.get("price") else 0
                lek_s = nfmt(lek, lang) if lek else ""
                if lek and f"{lek_s} L" not in price:
                    flag(f"{rel}: Lek price {lek_s} L missing from {price[:60]!r}")
                if not w.get("price"):
                    # An unpriced watch must print this language's exact
                    # "price on request" string and NEVER a figure. Looking for
                    # €0 here reported "euro price missing" on all three pages
                    # of the Cortébert rectangular, which was the check being
                    # wrong rather than the page.
                    if price.strip() != POR[lang]:
                        flag(f"{rel}: unpriced watch should read {POR[lang]!r}, "
                             f"reads {price.strip()[:40]!r}")
                    if "€" in price or re.search(r"\d", price):
                        flag(f"{rel}: unpriced watch is showing a figure")
                elif f'€{w["price"]}' not in price:
                    flag(f"{rel}: euro price missing")
                if lek and lang == "sq" and not price.lstrip().startswith(f"{lek_s} L"):
                    flag(f"{rel}: Albanian page must lead with Lek")
                if lek and lang != "sq" and not price.lstrip().startswith("€"):
                    flag(f"{rel}: {lang} page must lead with euro")

            # 6. structured data
            ld = re.search(r'id="ld-json">(.*?)</script>', t, re.S)
            if not ld:
                flag(f"{rel}: no Product JSON-LD")
            else:
                try:
                    d = json.loads(ld.group(1))
                except Exception as e:
                    flag(f"{rel}: Product JSON-LD parse error {str(e)[:50]}")
                    d = {}
                if "NaN" in ld.group(1):
                    flag(f"{rel}: NaN in structured data")
                if d.get("aggregateRating"):
                    flag(f"{rel}: aggregateRating on Product (these are shop reviews)")

            # 7. social cards resolve without JS
            for name in ("twitter:title", "twitter:description", "twitter:image"):
                if f'name="{name}"' not in t:
                    flag(f"{rel}: {name} missing")
            img = re.search(r'name="twitter:image"[^>]*content="([^"]+)"', t)
            if img and not (BASE / img.group(1).replace("https://watch.al/", "")).exists():
                flag(f"{rel}: twitter:image does not exist on disk")

            # 8. reference-less watches must not show an orphan label
            if not w.get("reference") and re.search(r'class="watch-ref-pg"[^>]*>\s*\S', t):
                flag(f"{rel}: empty reference but a Ref. line is rendered")

            # 9. the meta description must not OPEN by naming another brand.
            # gen_product_pages prefixes "Swiss watch by X." for a Swiss brand,
            # and X was the literal "Hislon" because Hislon was the only one when
            # it was written. Adding Cortebert to SWISS_BRANDS told crawlers and
            # every social preview that nine Cortebert pages were Hisl-ons, in
            # three languages, in a perfectly well-formed sentence no other check
            # could question. Only the OPENING is examined: six descriptions
            # legitimately compare a watch to a Casio further in.
            md = re.search(r'<meta name="description" id="page-desc" content="([^"]*)"', t)
            if md:
                opening = md.group(1).split(".")[0]
                wrong = [b for b in SWISS_BRANDS
                         if b != w["brand"] and b.lower() in opening.lower()]
                if wrong:
                    flag(f"{rel}: meta description opens by naming {wrong[0]}, "
                         f"but this is a {w['brand']}")

    print(f"\n  {pages} product pages | {len(glyphs)} glyphs in the subset")
    print("PRODUCT PAGE GATE PASS" if not findings else f"{len(findings)} FINDINGS")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
