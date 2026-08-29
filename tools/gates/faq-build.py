#!/usr/bin/env python3
"""[DB-020] faq-build.py — BUILDS the visible FAQ from the schema, and verifies it.
DOES:   three modes. --screen classifies every target answer through the detector
        table and writes scripts/faq-screen.json with a wave split;
        --build --wave N renders the visible <details> block and splices the
        JSON-LD in the SAME pass (dry run unless --apply); --verify walks every
        page and fails any page whose FAQPage schema claims an answer the reader
        cannot see, plus any faq-icon outside the subsetted font.
IN:     python tools/gates/faq-build.py --screen | --build --wave N [--apply] |
        --verify [--blog-only], from the WORKING ROOT. Authored copy comes from
        scripts/faq-overrides.json, keyed "<page>#<index>" and guarded by a src
        hash of the exact answer it was written against.
OUT:    --screen writes scripts/faq-screen.json. --build --apply rewrites blog
        HTML in place, preserving each file's BOM and its own line ending, and
        exits 1 if any targeted file failed or the wave did not complete. --verify
        prints the aligned / no visible / partial tallies and ends on
        "problems: 0" when clean.
CALLS:  reads watches.json for the price bands the detectors reason about and
        shared.css for the legal glyph set. It runs no generator: nothing it
        writes is a generated page, so it does not join the gen_* run order.
NOTES:  THE ONE RULE: a file is touched exactly ONCE, and the HTML and the JSON
        are written in the SAME pass from ONE source string. Writing the schema in
        one run and generating HTML from it in another is precisely the mechanism
        that produced the drift this exists to fix. The invariant is asserted
        against the rendered text BEFORE the file is written, so a page that would
        ship a hidden answer never reaches disk at all.
        --verify walks every page under {lang}/. It used to walk {lang}/blog/
        alone, and that narrow scope is the only reason 18 broken service pages
        stayed invisible through the whole FAQ sweep: the icon half of the check
        was already sitewide and saw them, the alignment half was not. --blog-only
        restores the old scope and is kept for comparison, never for a routine
        run.
        "problems: 0" is the PASS line but it is NOT the whole exit condition:
        illegal faq-icons are counted separately and also exit 1, so the
        "faq-icons checked N, illegal: M" line has to be read too. Glyphs are
        derived from shared.css on every run and never hardcoded, because a
        re-subsetted font must fail the build rather than ship blank boxes.
        Never read_text/write_text in here: 15 of the 117 targets are LF-only and
        17 are mixed, and Python's text mode would silently rewrite every line
        ending in the file. The header below says "the repo root": that is the
        working root .../watch-repair-shop, not the git repo nested inside it.

faq-build.py — FAQ sweep part 2.

117 blog articles carry FAQPage JSON-LD but display no FAQ. Google requires the structured
data to correspond to content a visitor can see, so this builds the visible section from the
schema. Part 1 (commit 19fc489) already handled the opposite case, where a visible FAQ existed
and the schema disagreed.

The one rule that matters: a file is touched exactly once, and the HTML and the JSON are
written in the SAME pass from ONE source string. Writing the schema in one run and generating
HTML from it in another is precisely the mechanism that produced the drift being fixed here.

  python tools/gates/faq-build.py --screen           one row per answer, detector flags, wave split
  python tools/gates/faq-build.py --build --wave 1   build a wave (dry run)
  python tools/gates/faq-build.py --build --wave 1 --apply
  python tools/gates/faq-build.py --verify           all invariants, sitewide

Run from the repo root (…/watch-repair-shop).
"""
import argparse
import html as H
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
import corpus  # noqa: E402  - shared read cache, see [PERF-004]
# The authoring manifests stay OUTSIDE the repo, in the working root's scripts/.
# Moving them in made verify-contact flag faq-overrides.json: it legitimately carries all
# three languages' phone numbers, and inside the repo it became site content the contact
# gate scans. The gate was right; the file simply is not a page. --verify never reads
# these, so CI is unaffected; --build/--reapply/--screen still find them locally.
MANIFEST = Path(__file__).resolve().parents[3] / "scripts" / "faq-overrides.json"
BOM = b"\xef\xbb\xbf"

LD_RE = re.compile(r'(<script type="application/ld\+json"[^>]*>)(.*?)(</script>)', re.S)
ANCHOR_RE = re.compile(r'(?m)^([ \t]*)<(?:div|nav)\s+class="related-articles"')
FAQ_H2 = re.compile(r"<h2[^>]*>\s*(?:Frequently Asked Questions|Domande Frequenti|Pyetje t[eë&])", re.I)
JSON_STR = re.compile(r'"(?:[^"\\]|\\.)*"')

HEADING = {"en": "Frequently Asked Questions",
           "it": "Domande Frequenti",
           "sq": "Pyetje t&euml; Shpeshta"}


# ---------------------------------------------------------------- byte-safe IO
# Never read_text/write_text: 15 of the 117 are LF-only and 17 are mixed, and Python's text
# mode would silently rewrite every line ending in the file.
# [DB-020.a] read_html — decode a page, remembering whether it had a BOM
# NOTES:  Bytes in, str out, and the BOM is reported rather than stripped and
#         forgotten, so write_html can hand back exactly the shape it was given.
def read_html(f: Path):
    raw = corpus.raw(f)
    had_bom = raw.startswith(BOM)
    return (raw[len(BOM):] if had_bom else raw).decode("utf-8"), had_bom


# [DB-020.b] write_html — re-encode in the page's own byte shape
# NOTES:  The only writer in this file. Line endings survive because the text it
#         was handed came back from read_html without ever being normalized.
def write_html(f: Path, text: str, had_bom: bool):
    data = text.encode("utf-8")
    f.write_bytes(BOM + data if had_bom else data)


def norm(s):
    """[DB-020.c] Canonical form for comparison AND for storage, so both sides start already-normalised.
    NBSP and thin space fold to a plain space: existing FAQ blocks write the phone number as
    +355&thinsp;67&thinsp;636&thinsp;0510 where the JSON has plain spaces, and that difference
    must not fail the equality check."""
    s = unicodedata.normalize("NFC", s).replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", s).strip()


INLINE = ("a|abbr|b|bdi|bdo|cite|code|data|dfn|em|i|kbd|mark|q|s|samp|small|span|strong"
          "|sub|sup|time|u|var|wbr")
INLINE_RE = re.compile(rf"</?(?:{INLINE})\b[^>]*>", re.I)


def strip_tags(t):
    """[DB-020.d] Model what the browser renders: an inline tag disappears, a block tag becomes a break.
    Turning EVERY tag into a space invents whitespace, so an answer ending
    '...guarantee</a>. Try it' reads as 'guarantee . Try it' and fails a verbatim check that
    should pass. That matters most for answers carrying a product link."""
    t = INLINE_RE.sub("", t)
    return re.sub(r"<[^>]+>", " ", t)


# [DB-020.e] visible_text — what a reader can actually see on the page
# NOTES:  script and style bodies are dropped FIRST, then strip_tags, then norm.
#         Dropping script is load-bearing rather than tidy: the FAQPage JSON-LD is
#         itself inside a <script>, so without this every answer would trivially
#         "appear" on its own page and --verify would pass the exact corpus it was
#         written to catch.
def visible_text(t):
    t = re.sub(r"<script.*?</script>", "", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", "", t, flags=re.S)
    return norm(H.unescape(strip_tags(t)))


def article_body(t):
    """[DB-020.f] Visible text minus chrome, so link titles in nav/related do not read as claims."""
    t = re.sub(r"<script.*?</script>", "", t, flags=re.S)
    t = re.sub(r"<style.*?</style>", "", t, flags=re.S)
    t = re.sub(r"<(nav|header|footer)\b.*?</\1>", "", t, flags=re.S | re.I)
    t = re.sub(r'<(div|nav) class="related-articles".*?</\1>', "", t, flags=re.S)
    t = re.sub(r"<title>.*?</title>", "", t, flags=re.S)
    return norm(H.unescape(strip_tags(t)))


# [DB-020.g] has_visible_faq — does this page already show a FAQ
# NOTES:  Two signals because the corpus predates one convention: the faq-item
#         class this file emits, and a localized FAQ <h2> on pages written by hand
#         before it. Either one means hands off, this is not a target.
def has_visible_faq(t):
    return ("faq-item" in t) or bool(FAQ_H2.search(t))


def faq_block(text):
    """[DB-020.h] The single FAQPage JSON-LD block: (match, parsed). Asserts there is exactly one."""
    found = [(m, json.loads(m.group(2))) for m in LD_RE.finditer(text)
             if m.group(2).strip() and '"@type"' in m.group(2)
             and _safe_type(m.group(2)) == "FAQPage"]
    if not found:
        return None, None
    assert len(found) == 1, "more than one FAQPage block"
    return found[0]


# [DB-020.i] _safe_type — a JSON-LD block's @type, or None if it will not parse
# NOTES:  Swallows the parse error on purpose. faq_block is a filter, and one
#         broken block on an unrelated page must not stop a sweep; "this JSON-LD
#         is invalid" is owned by the gates ([ERR-007] check 7, [ERR-011]).
def _safe_type(body):
    try:
        d = json.loads(body)
    except Exception:
        return None
    return d.get("@type") if isinstance(d, dict) else None


def targets():
    """[DB-020.j] The 117: FAQPage schema, no visible FAQ."""
    out = []
    for lang in ("en", "it", "sq"):
        for f in sorted((BASE / lang / "blog").glob("*.html")):
            if f.name == "index.html":
                continue
            t, _ = read_html(f)
            m, d = faq_block(t)
            if d and not has_visible_faq(t):
                out.append((f, lang, d))
    return out


# ---------------------------------------------------------------- ground truth from the catalogue
# [DB-020.k] catalogue — per-brand price bands, sorted prices, and the empty gaps
# NOTES:  A gap is a stretch of more than 20 euro with no watch in it. The
#         detectors use it to flag a price written into an answer that nothing in
#         the shop could ever be sold at. All three are derived from watches.json
#         on every run, so a repricing moves the detectors with it instead of
#         stranding them.
def catalogue():
    w = json.loads(corpus.raw((BASE / "watches.json")).decode("utf-8"))
    bands = defaultdict(list)
    for x in w:
        bands[x["brand"]].append(x["price"])
    bands = {k: (min(v), max(v)) for k, v in bands.items()}
    prices = sorted({x["price"] for x in w})
    gaps = [(a, b) for a, b in zip(prices, prices[1:]) if b - a > 20]
    return bands, prices, gaps


def legal_icons():
    """[DB-020.l] Glyphs and their font family, derived from shared.css + repo usage. Never hardcoded:
    if the font is re-subsetted, the build must fail rather than ship blank boxes."""
    css = corpus.raw((BASE / "shared.css")).decode("utf-8-sig")
    glyphs = set(re.findall(r"\.(fa-[a-z0-9-]+)::before", css))
    fam = defaultdict(set)
    for f in corpus.html_files():
        t = corpus.raw(f).decode("utf-8", errors="replace")
        for m in re.finditer(r'class="([^"]*\bfa-[a-z0-9-]+[^"]*)"', t):
            cls = m.group(1).split()
            for g in [c for c in cls if c.startswith("fa-") and c not in ("fa-brands", "fa-solid")]:
                for k in [c for c in cls if c in ("fab", "fas", "fa-brands", "fa-solid")]:
                    fam[g].add("fab" if k in ("fab", "fa-brands") else "fas")
    bad = {g: s for g, s in fam.items() if len(s) > 1}
    assert not bad, f"glyph used with two families: {bad}"
    return {g: (fam[g].pop() if fam.get(g) else "fas") for g in glyphs}


# ---------------------------------------------------------------- detectors
DET = [
    ("EM",     lambda s: "—" in s),
    ("SAPPH",  lambda s: re.search(r"(?i)sapphire|zaffiro|safir", s)),
    ("LEATH",  lambda s: re.search(r"(?i)leather|pelle|cuoio|l[ëe]kur", s)),
    ("PREOWN", lambda s: re.search(r"(?i)pre-?owned|second[- ]hand|usat[oi]|dor[ëe] t[ëe] dyt", s)),
    ("AUTH",   lambda s: re.search(r"(?i)authoris|authoriz|autorizzat|autorizuar", s)),
]


def price_flags(s, bands, gaps):
    """[DB-020.m] GAP: a price inside an empty band. BRANDPRICE: a price beside a brand it cannot belong to."""
    flags = set()
    for lo, hi in gaps:
        for p in re.findall(r"€\s?(\d{2,3})", s):
            if lo < int(p) < hi:
                flags.add("GAP")
        # a range written across the empty band, e.g. "100-200" spanning 96..148
        for a, b in re.findall(r"€\s?(\d{2,3})\s*[-–—]\s*€?\s?(\d{2,3})", s):
            if int(a) <= lo and int(b) >= hi:
                flags.add("GAP")
    for brand, (lo, hi) in bands.items():
        for m in re.finditer(re.escape(brand) + r"[^.!?]{0,140}|[^.!?]{0,140}" + re.escape(brand), s):
            for p in re.findall(r"€\s?(\d{2,3})", m.group(0)):
                if not (lo <= int(p) <= hi):
                    flags.add("BRANDPRICE")
    if re.search(r"(?i)hislon", s) and re.search(r"(?i)navimarine", s):
        flags.add("PAIR")
    return flags


# [DB-020.n] flags_for — the keyword detectors unioned with the price detectors
# NOTES:  A flag is a request for judgement, never a verdict: all it decides is
#         which wave a file lands in.
def flags_for(s, bands, gaps):
    f = {name for name, fn in DET if fn(s)}
    return f | price_flags(s, bands, gaps)


# ---------------------------------------------------------------- icon proposal
TOPIC = [
    (r"(?i)safe|scam|fake|counterfeit|genuine|sicur|truff|fals|autentic|siguri|mashtrim|origjinal", "fa-shield-alt"),
    (r"(?i)batter|bateri", "fa-battery-three-quarters"),
    (r"(?i)\bwater|waterproof|swim|shower|acqua|impermeab|nuot|doccia|\buj[ëeit]|\bnot[io]|zhyt|dush", "fa-swimmer"),
    (r"(?i)fridge|freez|\bcold\b|humid|condensat|moistur|sauna|temperatur|frigo|umid|condens|lag[ëe]sht|ftoht|nxeht", "fa-tint"),
    (r"(?i)warrant|guarant|garanzia|garanci", "fa-shield-alt"),
    (r"(?i)crystal|glass|sapphire|cristall|vetro|zaffiro|xham|kristal|safir", "fa-gem"),
    (r"(?i)\bkey\b|chiav|çeles|celes", "fa-key"),
    (r"(?i)magnet", "fa-bolt"),
    (r"(?i)strap|bracelet|\bband\b|cinturin|brac[ci]al|\brrip|brez", "fa-link"),
    (r"(?i)quartz|mechanic|movement|quarzo|meccanic|moviment|kuarc|mekanik|l[ëe]vizj", "fa-cogs"),
    (r"(?i)clean|polish|puliz|lucid|pastr|l[ëe]moj", "fa-broom"),
    (r"(?i)stor(e|age|ing)|conserv|ruajt", "fa-store"),
    (r"(?i)repair|servic|fix|riparaz|revision|servis|rregull|ripar", "fa-tools"),
    (r"(?i)\bsize|\bmm\b|diamet|wrist|misur|polso|madh[ëe]si|kyç", "fa-ruler"),
    (r"(?i)gift|present|regal|dhurat", "fa-gift"),
    (r"(?i)where|durr|tiran|shop\b|\bdove\b|\bku\b|dyqan", "fa-map-marker-alt"),
    (r"(?i)how long|last|years|dura|quanto|sa zgjat|vite|vjet", "fa-clock"),
    (r"(?i)price|cost|cheap|budget|spend|expensive|prezzo|cost[ao]|çmim|kushton|buxhet", "fa-tag"),
    # inspection questions read as "buying" but are not contact questions
    (r"(?i)what should i check|should i check|inspect|ispezion|controllare|kontrolloj|verifik", "fa-search"),
    (r"(?i)\bbuy\b|buying|order|contact|whatsapp|compr|ordinar|blej|porosi|kontakt", "fab:fa-whatsapp"),
]

# When a topic repeats on consecutive rows, fall to a glyph in the SAME semantic family rather
# than dropping through the whole list, which used to strand unrelated questions on fa-whatsapp.
ALT = {"fa-battery-three-quarters": "fa-battery-half", "fa-tools": "fa-cog", "fa-cogs": "fa-cog",
       "fa-clock": "fa-hourglass-half", "fa-gem": "fa-search", "fa-tag": "fa-money-bill",
       "fa-map-marker-alt": "fa-map-pin", "fa-link": "fa-ruler", "fa-swimmer": "fa-tint",
       "fa-shield-alt": "fa-lock", "fa-store": "fa-shopping-bag", "fa-broom": "fa-oil-can",
       "fa-key": "fa-lock", "fa-gift": "fa-heart", "fa-bolt": "fa-compass",
       "fa-ruler": "fa-balance-scale", "fa-whatsapp": "fa-envelope",
       "fa-tint": "fa-exclamation-circle"}
NEUTRAL = ["fa-star", "fa-check-circle", "fa-clock", "fa-cog", "fa-search", "fa-circle"]


# [DB-020.o] propose_icon — a glyph per question, never the same one twice running
# NOTES:  First TOPIC match wins, and a collision with the row above falls to ALT,
#         a glyph in the SAME semantic family. Dropping through the rest of the
#         TOPIC list instead used to strand unrelated questions on fa-whatsapp,
#         because the buying pattern is the last and broadest entry. Every ALT
#         value is a Free-font solid glyph, which is why that branch can hardcode
#         "fas".
def propose_icon(q, is_last, prev):
    for pat, g in TOPIC:
        if re.search(pat, q):
            fam, glyph = g.split(":") if ":" in g else ("fas", g)
            if glyph != prev:
                return [fam, glyph]
            alt = ALT.get(glyph)
            if alt and alt != prev:
                return ["fas", alt]        # ALT entries are all Free-font
    for g in NEUTRAL:
        if g != prev:
            return ["fas", g]
    return ["fas", "fa-circle"]


# ---------------------------------------------------------------- screening
# [DB-020.p] cmd_screen — classify every target answer and split it into waves
# DOES:   one row per answer with its detector flags, a per-file union of them,
#         and the split: wave 1 is the files where nothing fired, wave 2 needs a
#         human.
# OUT:    scripts/faq-screen.json, which --build reads to decide what a wave IS.
# NOTES:  Screens each file's VISIBLE BODY as well as its schema. An article whose
#         prose already makes a claim the detectors distrust is not safe to
#         mass-build against even when its own answers look clean.
def cmd_screen():
    bands, prices, gaps = catalogue()
    tg = targets()
    print(f"target files: {len(tg)}   questions: {sum(len(d['mainEntity']) for _, _, d in tg)}")
    print(f"catalogue: {len(bands)} brands, empty bands {[(a + 1, b - 1) for a, b in gaps]}\n")

    rows, per_file, body_hits = [], {}, {}
    for f, lang, d in tg:
        rel = f.relative_to(BASE).as_posix()
        t, _ = read_html(f)
        bflags = flags_for(article_body(t), bands, gaps)
        if bflags:
            body_hits[rel] = bflags
        ff = set()
        for i, q in enumerate(d["mainEntity"]):
            s = norm(q["name"]) + " " + norm(q["acceptedAnswer"]["text"])
            fl = flags_for(s, bands, gaps)
            rows.append((rel, lang, i, sorted(fl), norm(q["name"])))
            ff |= fl
        per_file[rel] = ff

    clean = [r for r, f in per_file.items() if not f]
    dirty = {r: f for r, f in per_file.items() if f}
    print(f"WAVE 1 (no detector fires): {len(clean)} files, "
          f"{sum(len(d['mainEntity']) for f, _, d in tg if f.relative_to(BASE).as_posix() in clean)} questions")
    print(f"WAVE 2 (needs judgement):   {len(dirty)} files, "
          f"{sum(len(d['mainEntity']) for f, _, d in tg if f.relative_to(BASE).as_posix() in dirty)} questions\n")

    tally = defaultdict(int)
    for _, _, _, fl, _ in rows:
        for x in fl:
            tally[x] += 1
    print("answers per detector:", dict(sorted(tally.items(), key=lambda kv: -kv[1])))
    print(f"\nfiles whose VISIBLE BODY also trips a detector: {len(body_hits)}")
    for r, f in sorted(body_hits.items()):
        print(f"   {','.join(sorted(f)):<28} {r}")

    print("\n--- WAVE 1 FILE LIST ---")
    for r in sorted(clean):
        print("  ", r)
    Path(MANIFEST.parent / "faq-screen.json").write_bytes(json.dumps(
        {"rows": rows, "wave1": sorted(clean), "wave2": sorted(dirty),
         "body_hits": {k: sorted(v) for k, v in body_hits.items()}},
        ensure_ascii=False, indent=1).encode("utf-8"))
    print(f"\nwrote {MANIFEST.parent / 'faq-screen.json'}")


# ---------------------------------------------------------------- building
def esc(s):
    """[DB-020.q] Only &, < and > need escaping. Everything else stays literal UTF-8, which makes
    unescape(strip_tags(html)) == source exactly true rather than approximately true."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


ANCHOR = ('<a href="{href}" style="color:var(--accent-gold);'
          'text-decoration:underline;text-underline-offset:3px">{label}</a>')


def linkify(escaped, links, lang):
    """[DB-020.r] Wrap phrases in the house anchor, in the HTML only. The JSON-LD keeps plain prose, which
    is what Google wants, and the verbatim check still passes because the comparator deletes
    inline tags rather than spacing them out.
    A target containing a slash is a page path ("services/key-cutting"); otherwise it is a shop
    id. Service slugs differ per language, so each override names its own."""
    for phrase, target in links or []:
        rel = f"{target}.html" if "/" in target else f"shop/{target}.html"
        assert (BASE / lang / rel).exists(), f"no page {lang}/{rel}"
        ph = esc(phrase)
        assert escaped.count(ph) == 1, f"link phrase {phrase!r} appears {escaped.count(ph)}x"
        escaped = escaped.replace(ph, ANCHOR.format(href=f"/{lang}/{rel}", label=ph), 1)
    return escaped


# [DB-020.s] render — the visible <details> block, in the page's indent and EOL
# NOTES:  indent and nl are arguments rather than assumptions, both copied from
#         the related-articles anchor in the file being edited, because 32 of the
#         targets are LF-only or mixed and the block has to land in their shape.
def render(pairs, lang, indent, nl):
    L = [f"{indent}<!-- FAQ -->",
         f'{indent}<div style="margin:2.5rem 0 1.5rem">',
         f"{indent}  <h2>{HEADING[lang]}</h2>"]
    for q, a, (fam, glyph), links in pairs:
        L += [f'{indent}  <details class="faq-item">',
              f'{indent}    <summary class="faq-question"><span class="faq-q-label">'
              f'<i class="{fam} {glyph} faq-icon" aria-hidden="true"></i>{esc(q)}</span>'
              f'<i class="fas fa-chevron-down" aria-hidden="true"></i></summary>',
              f'{indent}    <div class="faq-answer"><p>{linkify(esc(a), links, lang)}</p></div>',
              f"{indent}  </details>"]
    L.append(f"{indent}</div>")
    return nl.join(L) + nl


def splice_json(payload, replacements):
    """[DB-020.t] Replace whole JSON string literals, matched on their DECODED value, leaving every
    other byte of the block untouched. Files store \\u2014 where json.dumps writes the
    character, so matching raw text would miss them."""
    out, shift = payload, 0
    for m in list(JSON_STR.finditer(payload)):
        try:
            dec = json.loads(m.group(0))
        except Exception:
            continue
        if dec in replacements:
            new = json.dumps(replacements[dec], ensure_ascii=False)
            out = out[:m.start() + shift] + new + out[m.end() + shift:]
            shift += len(new) - (m.end() - m.start())
    return out


def src_hash(q, a):
    """[DB-020.u] Guards an override against the answer it was authored from. If the schema text later
    changes, the override refuses to build rather than silently applying to different copy."""
    import hashlib
    return hashlib.sha256((norm(q) + "\x00" + norm(a)).encode()).hexdigest()[:16]


# [DB-020.v] build — the one pass: HTML and JSON-LD from ONE source string
# DOES:   per file, asserts a single related-articles anchor and no existing FAQ,
#         resolves each question through its hash-guarded override, renders the
#         block, splices the JSON string literals, then asserts that every
#         question and every answer is visible in the result BEFORE anything is
#         written.
# IN:     the wave number and the apply flag. Without --apply nothing touches
#         disk, and that is the mode to run first: the proposed-icon list is the
#         review artefact a human is supposed to read.
# NOTES:  Every failure is caught per file and reported, so one bad page cannot
#         abort a wave halfway and leave the corpus half-converted. Exits 1 if any
#         file failed or the wave did not build completely, because a partial wave
#         that reported success is how the drift got in the first time.
def build(wave, apply):
    bands, prices, gaps = catalogue()
    icons = legal_icons()
    screen = json.loads(corpus.raw((MANIFEST.parent / "faq-screen.json")).decode("utf-8"))
    overrides = json.loads(corpus.raw(MANIFEST).decode("utf-8")) if MANIFEST.exists() else {}
    waves = overrides.get("_waves", {})
    if str(wave) in waves:
        want = set(waves[str(wave)])
    else:
        want = set(screen["wave1"] if str(wave) == "1" else screen["wave2"])

    done, failed, total_q, icon_log = 0, [], 0, []
    for f, lang, d in targets():
        rel = f.relative_to(BASE).as_posix()
        if rel not in want:
            continue
        t, had_bom = read_html(f)
        try:
            ms = list(ANCHOR_RE.finditer(t))
            assert len(ms) == 1, f"{len(ms)} related-articles anchors"
            assert "faq-item" not in t, "already has a FAQ"
            m = ms[0]
            indent = m.group(1)
            eol = t.find("\n", m.start())
            nl = "\r\n" if eol > 0 and t[eol - 1] == "\r" else "\n"

            # one source string per Q and per A, used for BOTH sides
            pairs, repl, prev = [], {}, None
            for i, q in enumerate(d["mainEntity"]):
                key = f"{rel}#{i}"
                ov = overrides.get(key, {})
                src_q, src_a = norm(q["name"]), norm(q["acceptedAnswer"]["text"])
                if ov:
                    got = src_hash(src_q, src_a)
                    assert ov.get("src") == got, (
                        f"{key}: override was authored against different text "
                        f"(expected {ov.get('src')}, page has {got})")
                new_q = norm(ov["q"]) if ov.get("q") else src_q
                new_a = norm(ov["a"]) if ov.get("a") else src_a
                if new_q != q["name"]:
                    repl[q["name"]] = new_q
                if new_a != q["acceptedAnswer"]["text"]:
                    repl[q["acceptedAnswer"]["text"]] = new_a
                ic = ov.get("icon") or propose_icon(new_q, i == len(d["mainEntity"]) - 1, prev)
                assert ic[1] in icons, f"icon {ic[1]} not in the subsetted font"
                assert ic[0] == icons[ic[1]], f"{ic[1]} needs family {icons[ic[1]]}, got {ic[0]}"
                assert ic[1] != prev, f"icon {ic[1]} repeats consecutively"
                prev = ic[1]
                pairs.append((new_q, new_a, ic, ov.get("links")))
                icon_log.append((rel, i, ic[0], ic[1], new_q[:58]))
                assert "—" not in new_q + new_a, "em dash in answer text"

            # insertion point: above the <!-- ... --> comment if there is one
            at = m.start()
            head = t[:at].split("\n")
            if len(head) >= 2 and head[-2].strip().startswith("<!--"):
                at -= len(head[-2]) + 1
                head = t[:at].split("\n")
            block = render(pairs, lang, indent, nl)
            if len(head) >= 2 and head[-2].strip():
                block = nl + block          # keep a blank line above
            new_t = t[:at] + block + nl + t[at:]

            # the JSON side, spliced in the SAME pass from the SAME strings
            if repl:
                mj, _ = faq_block(new_t)
                fixed = splice_json(mj.group(2), repl)
                obj = json.loads(fixed)
                assert [x["name"] for x in obj["mainEntity"]] == [p[0] for p in pairs]
                assert [x["acceptedAnswer"]["text"] for x in obj["mainEntity"]] == [p[1] for p in pairs]
                assert not re.search(r"<[a-z/]", json.dumps(obj)), "markup leaked into JSON-LD"
                new_t = new_t[:mj.start(2)] + fixed + new_t[mj.end(2):]

            # the invariant, checked before the file is written
            vis = visible_text(new_t)
            for q, a, _, _lk in pairs:
                assert q in vis, f"question not visible: {q[:60]}"
                assert a in vis, f"answer not visible: {a[:60]}"
            for mm in LD_RE.finditer(new_t):
                if mm.group(2).strip():
                    json.loads(mm.group(2))

            if apply:
                write_html(f, new_t, had_bom)
            done += 1
            total_q += len(pairs)
        except Exception as e:
            failed.append((rel, str(e)))

    print(f"\n{'APPLIED' if apply else 'DRY RUN'}: built {done} of {len(want)} files, {total_q} questions")
    if failed:
        print(f"FAILURES: {len(failed)}")
        for r, e in failed:
            print(f"   {r}: {e}")
    print("\n--- proposed icons ---")
    for rel, i, fam, g, q in icon_log:
        print(f"  {fam:<4}{g:<28} {rel.split('/')[-1][:38]:<40} {q}")
    if done != len(want) or failed:
        sys.exit(1)


# ---------------------------------------------------------------- verification
# [DB-020.x] reapply — push an EDITED override onto a page that already shows its FAQ
# DOES:   for each "path#i" in the manifest, replaces mainEntity[i]'s answer in the
#         JSON-LD and the matching <p> in the visible block, from the same one
#         source string, exactly as build() does.
# WHY IT EXISTS: build() only walks targets(), which is "FAQPage schema AND NO
#         visible FAQ". Once a page has been built it stops being a target for
#         ever, so editing faq-overrides.json afterwards changed nothing at all
#         and reported success while doing it: three waves dry-ran as
#         "built 0 of 15 / 0 of 19 / 0 of 25 files". The manifest had become a
#         document nothing read. That is how the 92.25 repricing left corrected
#         answers sitting unused in a file (2026-08-25).
# NOTES:  src is NOT the guard here and must never be recomputed from a built
#         page. src hashes the text the override REPLACED, so on a built page it
#         matches nothing by design. The guard is the question: an override may
#         only rewrite an answer whose question is still the one at that index,
#         and the old answer must be found EXACTLY ONCE in the visible block.
#         Without --apply nothing is written and the before/after is printed,
#         which is the mode to run first.
def reapply(apply):
    overrides = json.loads(corpus.raw(MANIFEST).decode("utf-8")) if MANIFEST.exists() else {}
    by_file = {}
    for key, ov in overrides.items():
        if key.startswith("_") or "#" not in key:
            continue
        rel, idx = key.rsplit("#", 1)
        by_file.setdefault(rel, []).append((int(idx), key, ov))

    changed = skipped = failed = 0
    for rel in sorted(by_file):
        f = BASE / rel
        lang = rel.split("/", 1)[0]
        try:
            t, bom = read_html(f)
            m, d = faq_block(t)
            assert d, f"{rel}: no FAQPage block"
            ents = d["mainEntity"]
            payload = m.group(2)
            body = t
            local = 0
            for idx, key, ov in sorted(by_file[rel]):
                assert idx < len(ents), f"{key}: only {len(ents)} questions on the page"
                old = ents[idx]["acceptedAnswer"]["text"]
                new = ov["a"]
                if norm(old) == norm(new):
                    skipped += 1
                    continue
                # --- visible half: the <p> holding this exact answer ---
                want = norm(old)
                hit = [pm for pm in re.finditer(
                    r'<div class="faq-answer"><p>(.*?)</p></div>', body, re.S)
                    if norm(strip_tags(pm.group(1))) == want]
                assert len(hit) == 1, (f"{key}: the old answer appears {len(hit)}x in the "
                                       f"visible block, expected exactly 1")
                pm = hit[0]
                body = (body[:pm.start(1)]
                        + linkify(esc(new), ov.get("links"), lang)
                        + body[pm.end(1):])
                # --- schema half: same source string, no anchors ---
                payload = splice_json(payload, {old: new})
                local += 1
                print(f"  {key}")
                print(f"      - {norm(old)[:118]}")
                print(f"      + {norm(new)[:118]}")
            if not local:
                continue
            # splice the rewritten payload back into the (already edited) body
            m2, _ = faq_block(body)
            body = body[:m2.start(2)] + payload + body[m2.end(2):]
            # nothing is written until every answer is provably visible
            vis = visible_text(body)
            for idx, key, ov in by_file[rel]:
                assert norm(ov["a"]) in vis, f"{key}: rewritten answer is not visible"
            _, d2 = faq_block(body)
            for idx, key, ov in by_file[rel]:
                assert norm(d2["mainEntity"][idx]["acceptedAnswer"]["text"]) == norm(ov["a"]), \
                    f"{key}: schema half did not take"
            if apply:
                write_html(f, body, bom)
            changed += local
        except Exception as e:
            failed += 1
            print(f"  FAILED {rel}: {e}")

    head = "REAPPLIED" if apply else "DRY RUN (pass --apply to write)"
    print(f"\n{head}: {changed} answer(s) rewritten, {skipped} already current, {failed} file(s) failed")
    return 1 if failed else 0


def cmd_verify(blog_only=False):
    """[DB-020.w] Walks every page, not just {lang}/blog/.

    It used to walk the blog alone, which is the only reason 18 broken service pages stayed
    invisible through the whole FAQ sweep: the icon half of this check was already sitewide
    and saw them, the alignment half was not. Pass --blog-only to get the old scope back.
    """
    icons = legal_icons()
    aligned = novis = partial = 0
    rows = 0
    problems = []
    for lang in ("en", "it", "sq"):
        pages = ((BASE / lang / "blog").glob("*.html") if blog_only
                 else (BASE / lang).glob("**/*.html"))
        for f in sorted(pages):
            # the blog index is a listing page; every other index.html may carry a real FAQ
            if f.name == "index.html" and f.parent.name == "blog":
                continue
            t, _ = read_html(f)
            m, d = faq_block(t)
            if not d:
                continue
            vis = visible_text(t)
            miss = [q for q in d["mainEntity"]
                    if norm(q["acceptedAnswer"]["text"]) not in vis or norm(q["name"]) not in vis]
            rows += sum((norm(q["name"]) not in vis) + (norm(q["acceptedAnswer"]["text"]) not in vis)
                        for q in d["mainEntity"])
            if not miss:
                aligned += 1
            elif len(miss) == len(d["mainEntity"]):
                # this branch used to count and say nothing, so a page whose every question was
                # hidden still exited 0. That is the worst state there is, not an exempt one.
                novis += 1
                problems.append(f"NO VISIBLE FAQ {f.relative_to(BASE).as_posix()}: "
                                f"{len(d['mainEntity'])} declared, none shown")
            else:
                partial += 1
                problems.append(f"PARTIAL {f.relative_to(BASE).as_posix()}: {len(miss)}/{len(d['mainEntity'])}")
            if re.search(r"&[a-zA-Z#][a-zA-Z0-9]*;", m.group(2)):
                problems.append(f"ENTITY in JSON-LD: {f.relative_to(BASE).as_posix()}")
            if "—" in m.group(2) or "\\u2014" in m.group(2):
                problems.append(f"EM DASH in JSON-LD: {f.relative_to(BASE).as_posix()}")
    print(f"aligned {aligned} | no visible FAQ {novis} | partial {partial} | failing rows {rows}")

    bad_icon, n_icon = [], 0
    for f in corpus.html_files():
        t = corpus.raw(f).decode("utf-8", errors="replace")
        for mm in re.finditer(r'class="(fa[bsr]) (fa-[a-z0-9-]+) faq-icon"', t):
            n_icon += 1
            if mm.group(2) not in icons or icons[mm.group(2)] != mm.group(1):
                bad_icon.append(f"{f.relative_to(BASE).as_posix()}: {mm.group(1)} {mm.group(2)}")
    print(f"faq-icons checked {n_icon}, illegal: {len(bad_icon)}")
    for x in bad_icon[:10]:
        print("   ", x)
    for x in problems[:20]:
        print("   ", x)
    print(f"problems: {len(problems)}")
    return 1 if (problems or bad_icon) else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--screen", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--reapply", action="store_true",
                    help="push edited overrides onto pages that already show their FAQ")
    ap.add_argument("--wave", default="1")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--blog-only", action="store_true",
                    help="verify only {lang}/blog/, the pre-2026-08-05 scope")
    a = ap.parse_args()
    if a.screen:
        cmd_screen()
    elif a.build:
        build(a.wave, a.apply)
    elif a.reapply:
        sys.exit(reapply(a.apply))
    elif a.verify:
        sys.exit(cmd_verify(a.blog_only))
    else:
        ap.print_help()
