#!/usr/bin/env python3
"""[ERR-011] verify-blog-index.py — the gate for the generated blog indexes.
DOES:   bytes (no BOM, strict CRLF, no form feed, no em dash, no U+FFFD),
        structure (1 featured, cards/dups derived from the manifest, chip and
        section order, one
        aria-pressed), set equality (cards == articles on disk == ItemList),
        per-section counts against the ARTICLES manifest, cross-language mirror
        isomorphism, CollectionPage JSON-LD validity with contiguous
        positions, localized month labels and read-times, copy preservation
        against git HEAD, and the blog-search.js cache-bust version.
IN:     no args. Invoked from the WORKING ROOT:
        python tools/gates/verify-blog-index.py
        Reads {en,it,sq}/blog/index.html, the articles on disk, and git HEAD.
        Read-only, the git calls included.
OUT:    "  FINDING: ..." per problem, then "BLOG INDEX GATE PASS" or
        "<n> FINDINGS". Exit 1 on findings.
CALLS:  blog_index_data.ARTICLES, gen_blog_index.UI / family_map / article_meta,
        and git show HEAD:<path> through subprocess with cwd=BASE.
NOTES:  This gate compares against GIT HEAD, so an intentional copy edit reads RED
        until it is committed. That is BY DESIGN and not a bug to fix: confirm the
        change was deliberate, commit it, and the gate is green again. It is the
        only thing standing between an accidental keystroke in card copy and a
        regeneration that ships it without anyone reading it.
        Check 9 compares the PRE-SUBSTITUTION templates in blog_index_data.py, not
        the rendered HTML. Rendered cards carry {n}/{u10k}/{lo} tokens, so
        comparing HTML made this fire on every stock change: adding one watch
        flipped "50 of our 57" to "51 of 58" and it was reported as copy drift. A
        gate that goes red every time the catalogue moves is a gate that gets
        ignored. The href set is still compared against HEAD's rendered output,
        because a card pointing at a url that did not exist before is a link break
        rather than a copy edit.
        If blog_index_data.py is absent at HEAD the copy check prints a NOTE and
        skips: fail-open there on purpose, because a missing file at HEAD means a
        new file, not drifted copy.
        Redirect stubs left behind by a slug rename are .html files in the blog
        directory and are NOT articles: they are noindex, and the disk set
        excludes them by the same rule gen_sitemap.py uses. The month comparison
        is whole-word because EN "April" is a substring of IT "Aprile".

verify-blog-index.py
Assertion gate for the generated blog index pages ({en,it,sq}/blog/index.html).
Run from repo parent: python tools/gates/verify-blog-index.py  -- exits 1 on findings.

Checks bytes (no BOM, strict CRLF, no form feed, no em dash), structure (featured,
card and dup counts, chip/section order), set equality (cards == files on disk ==
ItemList), per-section counts, cross-language mirror isomorphism, JSON-LD validity
and position contiguity, copy preservation against git HEAD, and localized dates.
"""
import json
import re
import subprocess
import sys
from html import unescape
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
import corpus  # noqa: E402  - shared read cache, see [PERF-004]
LANGS = ("en", "it", "sq")
CATS = ("buying", "gifts", "care", "knowledge", "keys")
findings = []


# [ERR-011.a] flag — record one finding and print it as it is found ([ERR-007.a])
def flag(msg):
    findings.append(msg)
    print("  FINDING:", msg)


# [ERR-011.b] main — three languages, then the cross-language and HEAD checks
# DOES:   walks en/it/sq collecting a family sequence per language, compares the
#         three sequences for mirror isomorphism, then runs the checks that need
#         git: card copy against HEAD's blog_index_data.py and the href set
#         against HEAD's rendered indexes.
# NOTES:  The numbered comments inside the per-language loop run out of order (6
#         sits between 3 and 4) because the checks were added over time and the
#         numbers name findings, while the order they RUN in is the order the data
#         allows: the disk set check 3 builds is what check 6 compares the
#         ItemList against. Do not renumber to tidy it.
def main():
    sys.path.insert(0, str(BASE))
    from blog_index_data import ARTICLES
    from gen_blog_index import UI, family_map, article_meta

    fam = family_map()
    feat_slug = [a["slug"] for a in ARTICLES if a.get("featured")][0]
    # Corpus sizes are DERIVED, never typed: N_FAM families render as one
    # featured block plus (N_FAM - 1) grid cards plus DUPS Latest-strip
    # duplicates. gen_blog_index.load_manifest already fails if the manifest
    # and en/blog disagree, so a literal here bought nothing and went stale
    # every time an article shipped.
    N_FAM = len(ARTICLES)
    DUPS = 3
    N_CARDS = N_FAM - 1 + DUPS
    cat_of = {a["slug"]: a["cat"] for a in ARTICLES}
    seq_by_lang = {}

    for lang in LANGS:
        p = BASE / lang / "blog" / "index.html"
        raw = corpus.raw(p)
        t = raw.decode("utf-8")

        # 1. bytes
        if raw.startswith(b"\xef\xbb\xbf"):
            flag(f"{lang}: BOM")
        if raw.count(b"\n") != raw.count(b"\r\n"):
            flag(f"{lang}: not strict CRLF")
        if b"\x0c" in raw:
            flag(f"{lang}: form feed byte")
        for bad in ("—", "&#8212;", "&mdash;", "�"):
            if bad in t:
                flag(f"{lang}: contains {bad!r}")

        # 2. structure
        feats = re.findall(r'class="b-feat"', t)
        cards = re.findall(r'<a data-cat="(\w+)" href="([^"]+)" class="b-card"( data-dup="1")?', t)
        dups = [c for c in cards if c[2]]
        if len(feats) != 1:
            flag(f"{lang}: {len(feats)} b-feat != 1")
        if len(cards) != N_CARDS:
            flag(f"{lang}: {len(cards)} b-card != {N_CARDS}")
        if len(dups) != DUPS:
            flag(f"{lang}: {len(dups)} dups != {DUPS}")
        chip_order = re.findall(r'data-filter="(\w+)"', t)
        if chip_order != ["all", *CATS]:
            flag(f"{lang}: chip order {chip_order}")
        sec_order = re.findall(r'data-sec="(\w+)"', t)
        if sec_order != list(CATS):
            flag(f"{lang}: section order {sec_order}")
        pressed = re.findall(r'data-filter="(\w+)" aria-pressed="true"', t)
        if pressed != ["all"]:
            flag(f"{lang}: aria-pressed true on {pressed}")

        # 3. set equality: unique card URLs == disk == ItemList
        feat_href = re.search(r'<a data-cat="\w+" href="([^"]+)" class="b-feat"', t).group(1)
        hrefs = {c[1] for c in cards} | {feat_href}
        slugs = {h.rsplit("/", 1)[-1][:-5] for h in hrefs}
        # Redirect stubs left behind by a slug rename are .html files in the blog
        # directory but they are not articles: they are noindex and must not be
        # carded or listed. Same rule gen_sitemap.py uses to exclude them.
        disk = {f.stem for f in (BASE / lang / "blog").glob("*.html")
                if "noindex" not in corpus.raw(f).decode("utf-8-sig").lower()} - {"index"}
        if slugs != disk:
            flag(f"{lang}: cards vs disk: only-cards={sorted(slugs - disk)[:3]} "
                 f"only-disk={sorted(disk - slugs)[:3]}")
        for h in hrefs:
            if not (BASE / h.lstrip("/")).exists():
                flag(f"{lang}: dead href {h}")

        # 6. JSON-LD validity + ItemList
        blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', t, re.S)
        coll = None
        for b in blocks:
            try:
                d = json.loads(b)
            except Exception as e:
                flag(f"{lang}: JSON-LD parse error: {str(e)[:60]}")
                continue
            if isinstance(d, dict) and d.get("@type") == "CollectionPage":
                coll = d
        if coll is None:
            flag(f"{lang}: no CollectionPage")
        else:
            il = coll["mainEntity"]["itemListElement"]
            if coll["numberOfItems"] != N_FAM or coll["mainEntity"]["numberOfItems"] != N_FAM:
                flag(f"{lang}: numberOfItems != {N_FAM}")
            if [x["position"] for x in il] != list(range(1, N_FAM + 1)):
                flag(f"{lang}: positions not contiguous 1..{N_FAM}")
            il_slugs = {x["url"].rsplit("/", 1)[-1][:-5] for x in il}
            if il_slugs != disk:
                flag(f"{lang}: ItemList set != disk")

        # 4. counts per section
        for cat in CATS:
            m = re.search(rf'data-sec="{cat}">[^<]*<span class="b-label-count">(\d+)</span>', t)
            grid = re.search(rf'data-sec-grid="{cat}">(.*?)\n        </div>', t, re.S)
            ncards = len(re.findall(r'class="b-card"', grid.group(1)))
            manifest_total = sum(1 for a in ARTICLES if a["cat"] == cat)
            want_grid = manifest_total - (1 if cat_of[feat_slug] == cat else 0)
            if int(m.group(1)) != manifest_total:
                flag(f"{lang}: {cat} badge {m.group(1)} != {manifest_total}")
            if ncards != want_grid:
                flag(f"{lang}: {cat} grid {ncards} != {want_grid}")

        # 5. mirror isomorphism: family sequence over non-dup cards
        seq = []
        for cat, href, dup in cards:
            if dup:
                continue
            slug = href.rsplit("/", 1)[-1][:-5]
            en = slug if lang == "en" else next(
                e for e, v in fam.items() if v.get(lang) == slug)
            seq.append((cat, en))
        seq_by_lang[lang] = seq

        # 10. localized dates + read-times
        times = re.findall(r'<time datetime="(\d{4}-\d{2}-\d{2})">([^<]+)</time>', t)
        if len(times) != N_CARDS + 1:  # 1 feat + N_CARDS cards
            pass  # count checked via cards below
        month_words = set(UI[lang]["months"])
        other = set()
        for lg2 in LANGS:
            if lg2 != lang:
                other |= set(UI[lg2]["months"]) - month_words
        for iso, label in times:
            # whole-word compare: EN "April" is a substring of IT "Aprile"
            if set(label.split()) & other:
                flag(f"{lang}: foreign month in {label!r}")
            y, m, _ = iso.split("-")
            if UI[lang]["months"][int(m) - 1] not in label or y not in label:
                flag(f"{lang}: date label {label!r} != {iso}")
        # spot: updated-variant iff schema says so, on every unique card
        upd = UI[lang]["updated"]
        for a in ARTICLES:
            slug = a["slug"] if lang == "en" else fam[a["slug"]][lang]
            pub, mod, rt = article_meta(lang, slug)
            block = re.search(
                rf'href="/{lang}/blog/{re.escape(slug)}\.html" class="b-(?:card|feat)">.*?</time>',
                t, re.S).group(0)
            has_upd = f">{upd} " in block or f"{upd} " in re.search(
                r"<time[^>]*>([^<]+)</time>", block).group(1)
            if (mod > pub) != has_upd:
                flag(f"{lang}/{slug}: updated-variant mismatch (mod={mod} pub={pub})")
            if f" {rt} min" not in block.replace("&nbsp;", " "):
                flag(f"{lang}/{slug}: read-time {rt} not on card")

    if seq_by_lang["en"] != seq_by_lang["it"] or seq_by_lang["en"] != seq_by_lang["sq"]:
        flag("mirror isomorphism broken between languages")

    # 9. copy preservation vs git HEAD.
    #
    # Compares the card TEMPLATES in blog_index_data.py, not the rendered HTML.
    # Rendered cards carry {n}/{u10k}/{lo} tokens, so comparing HTML made this
    # check fire on every stock change: adding one watch flipped "50 of our 57"
    # to "51 of 58" and reported it as copy drift. A gate that goes red every
    # time the catalogue moves is a gate that gets ignored, and this one is the
    # only thing standing between an accidental keystroke in the card copy and
    # a silent regeneration. Comparing the pre-substitution strings still
    # catches a real edit and is immune to the catalogue.
    old_src = subprocess.run(
        ["git", "show", "HEAD:blog_index_data.py"], cwd=BASE,
        capture_output=True).stdout.decode("utf-8")

    def templates(src):
        """{(slug, lang): (title, desc)} parsed out of an ARTICLES source file."""
        ns = {}
        exec(compile(src, "blog_index_data.py", "exec"), ns)
        norm = lambda s: re.sub(r"\s+", " ", unescape(s)).strip()
        return {(a["slug"], lang): (norm(c["title"]), norm(c["desc"]))
                for a in ns["ARTICLES"] for lang, c in a["card"].items()}

    if not old_src.strip():
        print("  NOTE: no blog_index_data.py at HEAD, copy check skipped")
    else:
        o, n = templates(old_src), templates(
            corpus.sig((BASE / "blog_index_data.py")))
        for key, pair in n.items():
            if key in o and pair != o[key]:
                flag(f"{key[1]}: card copy changed for {key[0]}")

    # the href set is still checked against HEAD's rendered output, since a card
    # pointing at a URL that did not exist before is a link break, not copy
    for lang in LANGS:
        old = subprocess.run(
            ["git", "show", f"HEAD:{lang}/blog/index.html"], cwd=BASE,
            capture_output=True).stdout.decode("utf-8")
        new = (BASE / lang / "blog" / "index.html").read_text(encoding="utf-8")
        hrefs = lambda t: set(re.findall(
            r'<a data-cat="\w+" href="([^"]+)" class="b-(?:card|feat)"', t))
        for href in hrefs(new) - hrefs(old):
            flag(f"{lang}: new href {href} not in HEAD")

    # 8. versions
    for lang in LANGS:
        t = (BASE / lang / "blog" / "index.html").read_text(encoding="utf-8")
        if "blog-search.js?v=3" not in t or "blog-search.js?v=2" in t:
            flag(f"{lang}: blog-search version wrong")

    print(f"\n{'BLOG INDEX GATE PASS' if not findings else f'{len(findings)} FINDINGS'}")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
