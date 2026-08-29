#!/usr/bin/env python3
"""[ERR-009] verify-sitemap.py — the gate for sitemap.xml and sitewide link health.
DOES:   eleven numbered checks. 1 bytes and XML shape, 2 the sitemap set equals
        the indexable pages on disk and every canonical equals its loc, 3 four
        alternates per url matching the page's own hreflang, 4 image entries, 5
        lastmod against the sitemap_state.json fingerprints, 6 the generator is
        idempotent (a re-render must equal the bytes on disk), 7 zero broken
        internal links sitewide, 8 hreflang reciprocity, 9 robots.txt, 10 llms.txt
        counts and links, 11 every shared.js/shared.css reference carries a ?v=.
IN:     no args. Invoked from the WORKING ROOT:
        python tools/gates/verify-sitemap.py
        BASE resolves from __file__, so the git repo is the subject wherever it is
        called from. Reads sitemap.xml, sitemap_state.json, robots.txt, llms.txt,
        watches.json and every *.html under mina.github.io. Read-only.
OUT:    "  FINDING: ..." per problem, a url/alternate/image/noindex tally, then
        "SITEMAP GATE PASS" or "<n> FINDINGS". Exit 1 on findings, plus an early
        exit 1 if sitemap.xml will not parse at all, since nothing after check 1
        could mean anything once the element tree is gone.
CALLS:  gen_sitemap for NO_ALTERNATES, APEX_TRACKS, fingerprint, collect, render
        and load_state, so check 6 compares against the real generator instead of
        a reimplementation that could be wrong in the same direction.
NOTES:  Checks 7 and 8 are why this file earns its length: NOTHING ELSE on the
        site covers them. 23 dead <a> hrefs shipped inside articles before check 7
        existed. Check 8 walks every page that DECLARES hreflang, noindex pages
        included, because the legal-page break lived entirely on noindex pages and
        any check scoped to sitemap urls could never have fired on it.
        Check 9 requires every robots.txt Disallow path to exist AND to carry
        noindex itself. Disallow alone deindexes nothing, so the page has to say
        it about itself, and a Disallow aimed at a file that is gone is a rule
        nobody is enforcing any more.
        Check 4's expected image count is DERIVED, 3 per live watch, and that is
        the entire point: it was hardcoded to 171 once and would have gone red the
        day a watch was added, which is exactly the class of failure the owner
        asked us to close. Check 7 stops after 30 broken links on purpose, so a
        structural break prints a diagnosis instead of a wall of output.

verify-sitemap.py
Assertion gate for sitemap.xml, its state file, and the sitewide link/hreflang
health it depends on. Run from repo parent:  python tools/gates/verify-sitemap.py

Two of these checks exist because nothing was watching and it cost us:
  * zero broken internal links  - 23 dead <a> hrefs shipped inside articles
  * hreflang reciprocity across EVERY hreflang-declaring page, noindex included -
    the legal-page break lived entirely on noindex pages, so any check scoped to
    sitemap URLs could never have fired on it.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parents[2]
import corpus  # noqa: E402  - shared read cache, see [PERF-004]
ROOT = BASE.parent
SITE = "https://watch.al/"
TODAY = date.today().isoformat()
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
XH = "{http://www.w3.org/1999/xhtml}link"
IM = "{http://www.google.com/schemas/sitemap-image/1.1}image"
findings = []


# [ERR-009.a] flag — record one finding and print it as it is found ([ERR-007.a])
def flag(m):
    findings.append(m)
    print("  FINDING:", m)


# [ERR-009.b] url_of — a file on disk -> its canonical https://watch.al/ url
# NOTES:  index.html is stripped so the directory form is the one true spelling.
#         Get this wrong and check 2 reports every directory page as missing from
#         the sitemap and extra in it, at the same time.
def url_of(p):
    rel = p.relative_to(BASE).as_posix()
    return SITE + (rel[:-len("index.html")] if rel.endswith("index.html") else rel)


# [ERR-009.c] file_of — the inverse: a site url -> the file that has to exist
# NOTES:  A trailing slash (and the bare apex) maps back to index.html. Checks 2,
#         3, 4 and 10 all decide "dead link" through this one function, so a bug
#         here would make the gate lie in four places at once instead of one.
def file_of(u):
    rel = u[len(SITE):]
    return BASE / (rel + "index.html" if rel.endswith("/") or rel == "" else rel)


# [ERR-009.d] main — the eleven checks, in order, over the whole site
# DOES:   parses sitemap.xml once and bails out immediately when the XML is
#         unparseable, because every later check reads that element tree.
# NOTES:  The apex is synthetic: the edge 301s it to /en/, so its own noindex shim
#         is never served there. It is never enumerated from disk, carries no
#         alternates (NO_ALTERNATES) and fingerprints APEX_TRACKS instead of
#         itself. Check 6 rebuilds the file with the real generator and compares
#         BYTES, BOM included, which is how a hand-edit to sitemap.xml is caught
#         even when the result is still valid XML.
def main():
    sys.path.insert(0, str(BASE))
    from gen_sitemap import NO_ALTERNATES, fingerprint, collect, render, load_state

    raw = corpus.raw((BASE / "sitemap.xml"))

    # --- 1. bytes and shape ---
    if not raw.startswith(b"\xef\xbb\xbf"):
        flag("sitemap.xml: BOM missing")
    if raw.count(b"\n") != raw.count(b"\r\n"):
        flag("sitemap.xml: not strict CRLF")
    if b"\x0c" in raw:
        flag("sitemap.xml: form feed byte")
    t = raw.decode("utf-8-sig")
    for bad in ("—", "&#8212;", "&mdash;"):
        if bad in t:
            flag(f"sitemap.xml: contains {bad!r}")
    try:
        root = ET.fromstring(t)
    except Exception as e:
        flag(f"sitemap.xml: XML parse error {e}")
        print(f"\n{len(findings)} FINDINGS")
        sys.exit(1)
    for ns in ("sitemaps.org/schemas/sitemap/0.9", "www.w3.org/1999/xhtml",
               "schemas/sitemap-image/1.1"):
        if ns not in t:
            flag(f"sitemap.xml: namespace {ns} not declared")

    urls = root.findall(NS + "url")
    locs = [u.find(NS + "loc").text for u in urls]
    if len(locs) != len(set(locs)):
        flag("duplicate <loc>")
    for u in urls:
        for tag in ("loc", "lastmod", "changefreq", "priority"):
            if len(u.findall(NS + tag)) != 1:
                flag(f"{u.find(NS+'loc').text}: {tag} count != 1")

    # --- 2. sitemap vs disk ---
    noindex, indexable = set(), set()
    for p in corpus.html_files():
        txt = corpus.raw(p).decode("utf-8-sig")
        m = re.search(r'<meta name="robots" content="([^"]*)"', txt)
        (noindex if m and "noindex" in m.group(1).lower() else indexable).add(url_of(p))
    # The apex is synthetic: the edge 301s it to /en/, so its own noindex shim is
    # never served there and it is neither enumerated from disk nor a noindex leak.
    expected = indexable | set(NO_ALTERNATES)
    if set(locs) != expected:
        flag(f"locs vs indexable: only-sitemap={sorted(set(locs)-expected)[:3]} "
             f"only-disk={sorted(expected-set(locs))[:3]}")
    for u in (noindex & set(locs)) - set(NO_ALTERNATES):
        flag(f"noindex page listed in sitemap: {u}")
    for u in locs:
        if u in NO_ALTERNATES:
            continue
        f = file_of(u)
        if not f.exists():
            flag(f"dead loc: {u}")
            continue
        c = re.search(r'<link rel="canonical"[^>]*?href="([^"]+)"',
                      corpus.raw(f).decode("utf-8-sig"))
        if u not in NO_ALTERNATES and (not c or c.group(1) != u):
            flag(f"{u}: canonical {c and c.group(1)} != loc")

    # --- 3. alternates ---
    n_alt = 0
    for u in urls:
        loc = u.find(NS + "loc").text
        alts = {(a.get("hreflang"), a.get("href")) for a in u.findall(XH)}
        n_alt += len(alts)
        if loc in NO_ALTERNATES:
            if alts:
                flag(f"{loc}: in NO_ALTERNATES but has {len(alts)} alternates")
            continue
        if len(alts) != 4:
            flag(f"{loc}: {len(alts)} alternates != 4")
        if loc not in {h for _, h in alts}:
            flag(f"{loc}: own loc not among its alternates")
        page = corpus.raw(file_of(loc)).decode("utf-8-sig")
        own = set(re.findall(r'<link rel="alternate" hreflang="([\w-]+)"[^>]*?href="([^"]+)"',
                             page))
        if alts != own:
            flag(f"{loc}: sitemap alternates != page hreflang")
        for _, h in alts:
            if not file_of(h).exists():
                flag(f"{loc}: alternate target missing {h}")

    # --- 4. images ---
    imgs = [(u.find(NS + "loc").text, i.find(NS.replace("sitemap/0.9", "sitemap/0.9") and
            "{http://www.google.com/schemas/sitemap-image/1.1}loc").text)
            for u in urls for i in u.findall(IM)]
    watches = json.loads((BASE / "watches.json").read_text(encoding="utf-8"))
    # [DB-006] a retired watch leaves the sitemap entirely, so it must not be
    # in the set we expect three <loc> blocks for. want_imgs below already
    # excluded it; this line did not, and that mismatch was the finding.
    ids = {w["id"] for w in watches if not w.get("deleted")}
    # derived, never typed: one image entry per live product per language. This
    # was hardcoded to 171 and would have failed the day a watch was added, which
    # is the whole class the owner asked us to close.
    want_imgs = 3 * len([w for w in watches if not w.get("sold") and not w.get("deleted")])
    if len(imgs) != want_imgs:
        flag(f"{len(imgs)} image entries != {want_imgs} (3 per live product)")
    for loc, img in imgs:
        if not re.match(rf"{re.escape(SITE)}(en|it|sq)/shop/[\w.-]+\.html$", loc):
            flag(f"image entry on a non-product block: {loc}")
        if not (BASE / img[len(SITE):]).exists():
            flag(f"{loc}: image file missing {img}")
        page = corpus.raw(file_of(loc)).decode("utf-8-sig")
        og = re.search(r'property="og:image"[^>]*content="([^"]+)"', page)
        if not og or og.group(1) != img:
            flag(f"{loc}: image:loc != og:image")
    per_id = {}
    for loc in locs:
        m = re.match(rf"{re.escape(SITE)}(?:en|it|sq)/shop/([\w.-]+)\.html$", loc)
        if m and m.group(1) in ids:
            per_id[m.group(1)] = per_id.get(m.group(1), 0) + 1
    if set(per_id) != ids or any(v != 3 for v in per_id.values()):
        flag("product ids with 3 locs != watches.json ids")

    # --- 5. dates and state ---
    state = load_state()
    for u in urls:
        loc, lm = u.find(NS + "loc").text, u.find(NS + "lastmod").text
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", lm):
            flag(f"{loc}: malformed lastmod {lm}")
        elif lm > TODAY:
            flag(f"{loc}: lastmod {lm} is in the future")
        if loc not in state:
            flag(f"{loc}: missing from state file")
        elif state[loc]["lastmod"] != lm:
            flag(f"{loc}: state lastmod {state[loc]['lastmod']} != sitemap {lm}")
    if set(state) != set(locs):
        flag("state keys != sitemap locs")
    from gen_sitemap import APEX_TRACKS
    for u, v in state.items():
        f = (BASE / APEX_TRACKS) if u in NO_ALTERNATES else file_of(u)
        if f.exists() and fingerprint(f) != v["fp"]:
            flag(f"{u}: stored fingerprint is stale (sitemap.xml edited by hand?)")
    sraw = corpus.raw((BASE / "sitemap_state.json"))
    if sraw.startswith(b"\xef\xbb\xbf"):
        flag("sitemap_state.json: unexpected BOM")
    if sraw.count(b"\n") != sraw.count(b"\r\n"):
        flag("sitemap_state.json: not strict CRLF")
    if b"generated" in sraw or b"timestamp" in sraw:
        flag("sitemap_state.json: carries a timestamp, which churns the diff")

    # --- 6. idempotence ---
    pages, fams, singles = collect()
    dates = {u: state[u]["lastmod"] for u in state}
    if b"\xef\xbb\xbf" + render(pages, fams, singles, dates).encode("utf-8") != raw:
        flag("generator is not idempotent: rerun produces different bytes")

    # --- 7. zero broken internal links, sitewide ---
    broken = 0
    for p in corpus.html_files():
        txt = corpus.raw(p).decode("utf-8-sig")
        for href in re.findall(r'<a [^>]*?href="([^"#?]+)', txt):
            if href.startswith(("http", "mailto:", "tel:", "javascript:", "#", "//")):
                continue
            tgt = (BASE / href.lstrip("/")) if href.startswith("/") else (p.parent / href)
            tgt = tgt / "index.html" if href.endswith("/") else tgt
            if not tgt.exists():
                flag(f"broken link in {p.relative_to(BASE).as_posix()} -> {href}")
                broken += 1
                if broken > 30:
                    flag("...more broken links suppressed")
                    break
        if broken > 30:
            break

    # --- 8. hreflang reciprocity across EVERY declaring page, noindex included ---
    decl = {}
    for p in corpus.html_files():
        txt = corpus.raw(p).decode("utf-8-sig")
        s = dict(re.findall(r'<link rel="alternate" hreflang="([\w-]+)"[^>]*?href="([^"]+)"', txt))
        if s:
            decl[url_of(p)] = s
    for u, s in decl.items():
        if u in NO_ALTERNATES:
            continue
        if u not in s.values():
            flag(f"{u}: hreflang set does not self-reference")
        if s.get("x-default") != s.get("en"):
            flag(f"{u}: x-default != en href")
        for hl, tgt in s.items():
            if hl == "x-default":
                continue
            if tgt not in decl:
                flag(f"{u}: hreflang {hl} target declares no hreflang: {tgt}")
            elif decl[tgt] != s:
                flag(f"{u}: hreflang not reciprocal with {tgt}")

    # --- 9. robots.txt ---
    rob = corpus.raw((BASE / "robots.txt")).decode("utf-8")
    if f"Sitemap: {SITE}sitemap.xml" not in rob:
        flag("robots.txt: Sitemap line wrong or missing")
    groups = [g for g in re.split(r"\r?\n\r?\n", rob) if "User-agent:" in g]
    for g in groups:
        dis = set(re.findall(r"Disallow: (\S+)", g))
        if "Allow: /" in g and not {"/admin.html", "/offline.html"} <= dis:
            flag(f"robots.txt: a group grants Allow: / without the global Disallow lines")
    for path in set(re.findall(r"Disallow: (\S+)", rob)):
        f = BASE / path.lstrip("/")
        if not f.exists():
            flag(f"robots.txt: Disallow {path} does not exist")
        elif "noindex" not in corpus.raw(f).decode("utf-8-sig", "replace").lower():
            flag(f"robots.txt: Disallow {path} is not noindex")

    # --- 10. llms.txt: it hard-codes counts nobody was checking, and said 75
    # guides when there were 80 for months. The guide count must still MATCH;
    # the catalogue size must now be ABSENT entirely.
    llms = corpus.raw((BASE / "llms.txt")).decode("utf-8")
    for bad, name in (("—", "em dash"), ("–", "en dash")):
        if bad in llms:
            flag(f"llms.txt: contains {name}")
    articles = len([p for p in (BASE / "en" / "blog").glob("*.html")
                    if p.stem != "index"
                    and "noindex" not in corpus.raw(p).decode("utf-8-sig").lower()])
    m = re.search(r"(\d+) practical guides", llms)
    if not m or int(m.group(1)) != articles:
        flag(f"llms.txt: claims {m and m.group(1)} guides, there are {articles}")
    # The catalogue SIZE is no longer published anywhere, llms.txt included: the
    # shop stocks considerably more than it lists, so any count understated it.
    # This check is inverted rather than deleted — it used to demand the number
    # match, and now it demands the number be absent, because llms.txt is what
    # AI answer engines read and a count there propagates further than a page.
    m = re.search(r"(\d+)\s+brand-new watches", llms)
    if m:
        flag(f"llms.txt: states a watch count ({m.group(1)}). No page publishes "
             f"how many watches; the shop stocks more than it lists.")
    for u in re.findall(r"\((https://watch\.al/[^)]+)\)", llms):
        if not file_of(u).exists():
            flag(f"llms.txt: dead link {u}")

    # --- 11. every asset reference carries a cache-bust version ---
    for f in corpus.html_files():
        b = corpus.raw(f)
        for asset in (rb"shared\.js", rb"shared\.css"):
            if re.search(rb'"[^"]*' + asset + rb'"', b):
                flag(f"{f.relative_to(BASE).as_posix()}: unversioned "
                     f"{asset.decode().replace(chr(92), '')}")

    print(f"\n  {len(urls)} urls | {n_alt} alternates | {len(imgs)} images | "
          f"{len(noindex)} noindex excluded")
    print(f"{'SITEMAP GATE PASS' if not findings else f'{len(findings)} FINDINGS'}")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
