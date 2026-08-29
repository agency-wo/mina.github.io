#!/usr/bin/env python3
"""[ERR-010] verify-stats.py — the gate that keeps catalogue numbers out of pages.
DOES:   six lettered checks. A every data-stat marker still renders what the
        catalogue says AND wraps a whole whitespace-delimited token; B no literal
        price FLOOR typed into the SOURCES (blog_index_data.py, brand_copy.py,
        shop_seo.py, llms.tpl); C shop.js carries the right SEP and no
        toLocaleString, and every reviewCount equals catalog_stats.REVIEWS; E
        G no page states how many watches, in a marker or in source copy;
        E every published price pair is arithmetically true and names a real
        catalogue price, in BOTH orders ("70 euro (6,800 L)" and the Albanian
        "6.800 L (70 euro)"); F no hand-typed {n}, {u10k}, {lo} or {hi} in the
        blog corpus outside a shrink-only allowlist; D no bare catalogue number
        sitting beside a catalogue noun in prose.
IN:     python tools/gates/verify-stats.py [--all], from the WORKING ROOT. --all is
        the only way to run check D. Waivers live in scripts/stats-allow.json,
        read from ROOT (the working root) rather than from the git repo.
        Read-only.
OUT:    "  FINDING: ..." per problem, a marker/review-count/price-pair/typed-
        aggregate tally, then "STATS GATE PASS" or "<n> FINDINGS". Exit 1 on
        findings.
CALLS:  catalog_stats (as C) for load/lek/SEP/REVIEWS, and gen_stats for SPAN_RE
        and render(), so the gate asks the generator what a marker should say
        rather than holding a second opinion about it.
NOTES:  Check D is WAIVED behind --all and runs LAST in the source despite its
        letter. It needs a taxonomy to tell a stale 57 from
        "a 57 percent increase", and the blog corpus is where the remaining
        hand-typed numbers still live, so switching it on by default would paint
        the gate red for a reason nobody could act on that day. The per-language
        NOUN table is the whole false-positive defence: a catalogue claim needs a
        catalogue noun within 60 characters.
        Check E reads BOTH orders. Albanian prose leads with Lek because
        card_price_html does, and that is deliberate: Lek is the currency
        Albanians shop in. 84 pairs were published in that order and invisible
        to this check until PAIR_LEK was added; the fix is to widen the gate,
        never to flip 84 correct sentences.
        Check E is the one nobody asked for and the one that pays. 631 published
        price pairs, and until it existed nothing on this site verified that the
        euro half and the Lek half of a sentence agreed, or that the euro figure
        was a price the shop actually charges. Both halves are checked: the
        arithmetic through catalog_stats.lek, and membership in the live price set
        read out of watches.json. With stock moving monthly a repricing is the
        common event, not the rare one, and one repricing silently invalidates
        prose in dozens of articles.
        scripts/stats-allow.json holds the waivers as page path -> allowed euro
        strings, plus a "_why" that has to justify every one of them (today: 123
        is the sum of a 59 and a 64 in the couples articles, not a single price).
        A waiver with no _why is somebody hiding a finding. The key is inert as
        data because no page path is ever named _why.
        Check F covers four keys in two families that need OPPOSITE tests.
        {n} and {u10k} are counts: a currency in front means the number is a
        price and check E owns it, so the hit is dropped. {lo} and {hi} ARE
        prices: a currency in front is the only thing that makes the hit real,
        and they additionally require a bound verb (F_BOUND) within reach.
        Without that verb a catalogue noun alone gives 50 findings of which
        effectively all are per-brand bands like 'the Hislon Classic runs from
        149 to 199 euro', which are correct prose; {hi} fires on them only
        because the dearest watch happens to be that Hislon. With F_BOUND and
        F_RANGE_CUR the same corpus gives 1, and that 1 was real. Note that
        adding {lo} to F_KEYS alone would be silent no-op coverage: render()
        returns the string with its currency, while F_NUM only ever yields
        digits, so f_targets keys on the digits and f_hits flips the test.
        Check F is check D with the scope cut until a finding always means
        something, and it runs by DEFAULT. Three cuts. Only the two aggregates
        that move when the catalogue moves, {n} and {u10k}; {b} was measured and
        left out, because 10 is also 10 ATM, 10x magnification, a 10-year battery
        and "10-15 minutes", and it produced 27 hits in 16 blog pages of which 27
        were false. Only {en,it,sq}/blog/*.html, because a generated shop or brand
        page heals itself on the next build while an article stays wrong forever.
        And only outside a data-stat span, which masked() already blanks.
        Measured on the corpus of 2026-08-09: 35 hits in 11 pages, 0 false
        positives, and dropping the NOUN requirement entirely changed neither
        number, so today the noun table costs no recall and is pure insurance for
        the day {u10k} lands on a value that reads like a unit.
        Check F does NOT detect a stale number. It matches the value the
        catalogue holds right now, which is a claim that will be a lie after the
        next watch is added; a page already reading 57 is invisible to it and
        belongs to check D. What it buys is that the claim can only be typed once.
        The allowlist under _check_f in stats-allow.json is a RATCHET: an entry
        whose page has no hit left is itself a finding, so a page that has been
        converted to markers can never quietly acquire a typed number again. It
        only ever shrinks. Every entry carries a reason and a date, the same
        standard the _why key sets for check E, and an entry with no reason is
        somebody hiding a finding. Known gap: a page already on the allowlist can
        gain a second typed number without the gate noticing, because the entry is
        per page rather than per hit. A per-hit ceiling was tried and rejected: it
        turns a partial cleanup, which is a good change, red.
        Check B reads the SOURCES, not the rendered output: llms.txt is generated
        from llms.tpl now, so a literal in the output is correct and only the
        template can leak. It flags a FLOOR claim alone, because
        "to a €199 Hislon" is naming a watch rather than stating a bound, and
        check E already owns that sentence.

verify-stats.py
Stops a catalogue number from being typed into a page again.

Run from repo parent:  python tools/gates/verify-stats.py [--all]

The owner's rule: the shop holds more stock than it publishes and it moves every
month, so a number typed into a page is wrong the moment it is typed. Generated
pages compute theirs; hand-written pages wrap theirs in a data-stat marker that
gen_stats.py refreshes. This proves both, and proves nothing new has crept in.

Checks A to C have no false positives at all. Check D needs a taxonomy, so it is
gated behind --all until the blog corpus is converted; the blog is where the
remaining hand-typed numbers live.

The most valuable check here is E, and nobody asked for it: 631 published price
pairs like "70 euro (6,800 L)" and not one thing on this site has ever verified
that the two halves agree, or that the euro figure is a price we actually charge.
A single repricing silently invalidates prose in dozens of articles, and with
stock moving monthly a repricing is the common event, not the rare one.
"""
import json
import re
import sys
from html import unescape
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
import corpus  # noqa: E402  - shared read cache, see [PERF-004]
ROOT = BASE.parent
sys.path.insert(0, str(BASE))
import catalog_stats as C  # noqa: E402

LANGS = ("en", "it", "sq")
ALL = "--all" in sys.argv
findings = []


# [ERR-010.a] flag — record one finding and print it as it is found ([ERR-007.a])
def flag(m):
    findings.append(m)
    print("  FINDING:", m)


MASK = [
    re.compile(r"<style\b.*?</style>", re.S | re.I),
    re.compile(r"<script\b.*?</script>", re.S | re.I),
    re.compile(r'\sstyle="[^"]*"'),
    re.compile(r'\s(?:href|src|class|id|srcset)="[^"]*"'),
    re.compile(r"<svg\b.*?</svg>", re.S | re.I),
    re.compile(r'<span data-stat="[^"]*">.*?</span>', re.S),
    # A PHONE NUMBER IS NOT A CATALOGUE FIGURE. Both shop numbers open +355 67,
    # and the moment the catalogue reached 67 watches (2026-08-25) check F read
    # that fragment as a hand-typed {n} on every page that prints a number
    # beside the word "stock" or "model": 46 findings, every one of them the
    # phone number. The count will pass 57 and 63 too, which are the other
    # groups in the two numbers. The separator is written four ways across the
    # corpus, so &thinsp;/&nbsp;/&#8201; are matched as well as a plain space,
    # which is the same normalisation verify-contact.py had to make.
    re.compile(r"\+\s*355(?:(?:\s|&nbsp;|&thinsp;|&#8201;|&#160;|-)*\d+)+"),
]


# [ERR-010.b] masked — blank out everything that is markup rather than prose
# NOTES:  Overwrites with NUL in place instead of deleting, so every offset into
#         the masked string still points at the same character of the original and
#         the 60-character context window printed with a finding stays truthful.
#         Masks style and script bodies, svg, the href/src/class/id/srcset
#         attributes and the inside of a data-stat span. Without it check D cannot
#         look at a bare number at all: a cache-bust query or a hex colour is full
#         of two- and three-digit numbers that were never claims.
def masked(t):
    out = list(t)
    for rx in MASK:
        for m in rx.finditer(t):
            for i in range(m.start(), m.end()):
                out[i] = "\x00"
    return "".join(out)


# a catalogue claim needs a catalogue noun nearby; that is what separates a stale
# 57 from "a 57 percent increase"
NOUN = {
    "en": r"watch|watches|model|models|brand|brands|counter|stock|in store",
    "it": r"orolog\w*|modell\w*|march\w*|banco|negozio|disponibil\w*",
    "sq": r"or[ëe]\w*|model\w*|mark\w*|banak\w*|dyqan\w*|gjendje",
}

# "(?:euro|€)" after the digits so the Albanian order "52 € (5.000 L)" is read.
# The trailing "L" tolerates "Lek"/"Lekë" because the word is spelled three ways.
PAIR = re.compile(
    r"(?:€|&euro;|)\s?(\d{2,3})\s*(?:euro\s*|€\s*)?\((\d{1,3}[.,]\d{3})\s*L", re.I)

# The mirror form, Lek first: "8.100 L (84 euro)". This is NOT sloppy writing to
# be flipped -- card_price_html leads with Lek in Albanian on purpose, because
# that is the currency Albanians shop in, and the prose follows the cards. 84
# such pairs were published and invisible to this check until it learned the
# shape. Groups are (lek, eur), the reverse of PAIR, so the loop normalises.
PAIR_LEK = re.compile(
    r"(\d{1,3}[.,]\d{3})\s*L(?:ek[ëe]?)?\s*\(\s?(?:€|&euro;)?\s?(\d{2,3})\s*euro\s*\)", re.I)

# The SEPARATOR forms, which carry no parenthesis and so were invisible to both
# patterns above. Two live shapes:
#   shop_bits.card_price_html -> "€64<span style=...> · 6,200 L</span>"
#   a comparison table        -> "€52 &nbsp;/&nbsp; 5,000 L"
# ONE tag may sit between the halves, because that is exactly what the price
# renderers emit; more than one and it is not a single price line. This matters
# most for the three homepages, which carry 18 such figures and which NO
# generator owns -- the shop's own copies heal themselves, these never do.
# Groups match PAIR: (eur, lek).
_T = r"(?:<[^<>]{0,140}>)?"
# The currency word is spelled L, Lek and Lekë, so the tail cannot be a bare
# "L\b": \b does not match between the L and the e of "Lek", which made this
# pattern silently blind to "€75 / 7,300 Lek" -- 159 figures across 31 files
# that the 92.25 repricing left stale while this gate reported PASS.
_L = r"L(?:ek[ëe]?)?\b"
PAIR_SEP = re.compile(
    r"(?:€|&euro;)\s?(\d{2,3})\s*(?:euro\s*|€\s*)?" + _T +
    r"\s*[·/]\s*" + _T + r"\s*(\d{1,3}[.,]\d{3})\s*" + _L, re.I)

# Lek-first separator form: "19.300 L<span ...> · €199</span>", the Albanian
# card order. The euro sign is REQUIRED here; without it "5.000 L / 199" would
# read any nearby two-digit number as a price. Groups are (lek, eur).
PAIR_LEK_SEP = re.compile(
    r"(\d{1,3}[.,]\d{3})\s*" + _L + _T + r"\s*[·/]\s*" + _T +
    r"\s*(?:€|&euro;)\s?(\d{2,3})(?!\d)", re.I)

# --- check F's vocabulary ------------------------------------------------
# Only the aggregates that move when the catalogue moves. {b} is deliberately
# absent: see NOTES, it is 100% noise at its current value of 10.
F_KEYS = ("n", "u10k")

# The money aggregates, kept apart from F_KEYS because the currency test below
# has to run the OTHER WAY for them. {n} and {u10k} are counts, so a currency
# in front means "price, not count" and the hit is dropped. {lo} and {hi} ARE
# prices, so a currency in front is the only thing that makes the hit real: a
# bare 50 near a watch noun is a water rating or a percentage far more often
# than it is the shop's floor. Adding these to F_KEYS instead would have been
# silent no-op coverage, because gen_stats.render("lo") is "€50" while F_NUM
# only ever yields "50", so targets.get() could never match.
F_MONEY_KEYS = ("lo", "hi")

# Narrower than NOUN above on purpose. No brand words, because "10 brands" is
# check B's and check D's business, and every word is \b-anchored so "ore"
# inside "before" and "more" stops being a catalogue noun.
F_NOUN = {
    "en": r"\b(?:watch|watches|model|models|piece|pieces|stock|counter|in store)\b",
    "it": r"\b(?:orolog\w*|modell\w*|banco|negozio)\b",
    "sq": r"\b(?:or[ëe]\w*|model\w*|banak\w*|dyqan\w*)\b",
}

# A whole number token, separators included, so 1,058 and 58,000 and 10.000 are
# read as one number each and never as a bare 58 or a bare 10. Comparing the
# whole token is what "respecting the separator" means here; a lookaround on
# [.,] would also throw away a legitimate "58." at the end of a sentence.
F_NUM = re.compile(r"\d[\d.,]*\d|\d")

# A number carrying a unit is a measurement, not a stock claim. This costs no
# recall at today's values, and it is most of the reason the check stays quiet
# when {n} or {u10k} drifts onto a value that also reads like a measurement.
# The   is written as an escape on purpose: an invisible non-breaking space
# inside a character class is unreviewable.
#
# NEVER EDIT THESE PATTERNS THROUGH A SHELL HEREDOC. Every \b below, and in
# F_RANGE_R, F_CUR and F_BOUND, spent an unknown time as a literal backspace
# byte (0x08), which is what \b becomes in a NON-raw Python string written
# through a heredoc. A backspace matches a backspace, which never occurs in
# HTML, so "mm", "ATM", "bar", "euro", "to", "deri", "da" and "nga" were all
# dead alternatives and this check's false-positive defences were simply off.
# Nothing noticed, because check F only fires when a target VALUE collides with
# prose, and none did until the catalogue reached 67 watches and {n} met both
# the shop phone number and the real EUR 67 Casio on the same day. 30 of them
# were repaired on 2026-08-25. Edit this file with an editor, not a heredoc.
F_UNIT = re.compile(
    r"[\s ]{0,2}(?:%|×|°|x\b|mm\b|cm\b|m\b|ATM\b|bar\b|Hz\b|L\b|"
    r"lek\w*|euro\b|€|degree\w*|grad\w*|min\w*|sec\w*|hour\w*|or[ëe]sh\b|"
    r"day\w*|dit[ëe]\w*|giorn\w*|month\w*|mes[ei]\b|muaj\w*|"
    r"year\w*|ann[oi]\b|vje\w*|vit\w*|fish\b|volte\b|times\b|her[ëe]\b)", re.I)

# Either end of a range is a range, not a count: "50-70% of retail value",
# "40-50 ore", "41 - 50 ore", "50 ne 199 euro". The word forms are kept short
# and deliberately EXCLUDE "nga", "dei" and "of", because "51 nga 58 oret" and
# "51 dei nostri 58 orologi" are the two sentences this whole check exists for.
F_RANGE_R = re.compile(r"[\s ]{0,2}(?:[-–—]|to\b|n[ëe]\b|deri\b|fino\b)"
                       r"[\s ]{0,2}\d")
F_RANGE_L = re.compile(r"\d[\s ]{0,2}(?:[-–—]|to|n[ëe]|deri|fino a)"
                       r"[\s ]{0,2}$", re.I)

# "€58" is a price and check E already owns whether it is a real one.
# "'58" is a decade, and there are articles here about the 1950s and 1960s.
F_CUR = re.compile(r"(?:€|&euro;|\bEUR|['’‘])[\s ]?$")


# For the money keys ONLY, a catalogue noun nearby is not enough. "Hislon
# Classic at 199 euro" and "from 149 to 199 euro" both sit beside one, and
# both are per-BRAND facts that are correct and must not be flagged; {hi}
# fires on them only because the dearest watch happens to be that Hislon.
# What separates a shop-wide bound from a price mention is a bound verb
# pointing at the shop, so a money hit additionally needs one of these in
# the characters just before it. Measured on this corpus the noun-only rule
# gave 50 findings and effectively all of them were per-brand bands, well
# under the "a finding always means something" bar this check is held to.
# The right-hand end of a range that carries its own currency symbol:
# "from 149 to EUR199". F_RANGE_L stops at the symbol, so this catches
# what it cannot. Money keys only.
# Check G: a retired counting token. Applied to published COPY DATA only,
# never to raw file text, so a docstring or an assert that names a retired
# token in order to forbid it is not itself a finding.
FORBIDDEN_IN_TEXT = re.compile('[{](n|u10k|n:[a-z0-9-]+)[}]')

F_RANGE_CUR = re.compile(r"\d[\s ]{0,2}(?:[-–—]|to|a|n[ëe]|deri|fino a)"
                         r"[\s ]{0,2}(?:€|&euro;|EUR)?[\s ]?$", re.I)

F_BOUND = re.compile(
    r"(?:watch\w*|stock|price\w*|range|counter|orolog\w*|prezz\w*|gamma|banco|"
    r"negozio|or[ëe]\w*|model\w*|banak\w*|dyqan\w*|gjendj\w*)"
    r"[^.!?]{0,45}?"
    r"(?:from|start\w*|run\w*\s+to|up\s+to|"
    r"\bda\b|parton\w*|\bparte\b|vanno|arrivano|fino\s+a|"
    r"\bnga\b|fillo\w*|shkoj\w*|deri)"
    r"[^.!?]{0,12}$", re.I)


# [ERR-010.c] main — A, B, C, E, then D, plus G and H, and the exit code
# DOES:   walks the pages once per check family rather than once overall; the
#         letters are how these findings are named, and E deliberately sits before
#         D in the source because D is the conditional one.
# NOTES:  Check A asserts twice about the same span: that it renders the current
#         value, and that it is not glued to a neighbouring character. The second
#         one is not cosmetic. The FAQ visibility probe in gen_shop_index.py turns
#         every tag into a space, so a marker wrapping half a token turns "€50"
#         into "€ 50" and the answer stops matching its schema twin.
def main():
    s = C.load()
    spans = 0

    # --- G. no page states how many watches --------------------------------
    # The shop holds considerably more stock than it publishes, so a published
    # count understates the shelf. The owner raised it more than once, and it
    # had reached 65 markers plus the copy in four source files before it was
    # taken out. This runs BEFORE check A on purpose: gen_stats.render now
    # RAISES on these keys, so without it check A would crash on the exception
    # instead of naming the page. {b} and every price are deliberately allowed.
    g_hits = 0
    for p in corpus.html_files():
        raw = corpus.raw(p)
        if b'data-stat="' not in raw:
            continue
        rel = p.relative_to(BASE).as_posix()
        for m in re.finditer(r'<span data-stat="(n|u10k|n:[a-z0-9-]+)">', raw.decode("utf-8-sig")):
            g_hits += 1
            flag(f"{rel}: data-stat={m.group(1)!r} is a watch count and is retired. "
                 f"No page states how many watches; the shop stocks more than it "
                 f"lists. Rewrite the sentence, do not revive the marker.")
    # The Python sources are inspected as DATA, not as text: brand_copy and
    # shop_seo both carry an assert and a docstring that name the retired tokens
    # in order to say they are retired, and a text scan reports those as
    # findings. Walking the published structures instead asks the only question
    # that matters — does any string a READER will see carry a count.
    def walk(v):
        if isinstance(v, str):
            yield v
        elif isinstance(v, dict):
            for x in v.values():
                yield from walk(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                yield from walk(x)

    for src, attr in (("brand_copy.py", "COPY"), ("shop_seo.py", "COPY"),
                      ("blog_index_data.py", "ARTICLES")):
        if not (BASE / src).exists():
            continue
        ns = {}
        exec(compile(corpus.sig((BASE / src)), src, "exec"), ns)
        for text in walk(ns.get(attr)):
            for m in FORBIDDEN_IN_TEXT.finditer(text):
                g_hits += 1
                flag(f"{src}: {{{m.group(1)}}} is a watch count and is retired, in "
                     f"published copy: {text[:70]!r}")
    tpl = BASE / "llms.tpl"
    if tpl.exists():
        for m in FORBIDDEN_IN_TEXT.finditer(corpus.sig(tpl)):
            g_hits += 1
            flag(f"llms.tpl: {{{m.group(1)}}} is a watch count and is retired")

    # --- H. no count assembled at RUNTIME -----------------------------------
    # G above reads static HTML, and so do the other two layers that enforce this
    # rule (catalog_stats.TOKEN_RE and gen_stats.render). shop.js used to write
    # "<n> watches available" into #shopCount on every render. The served HTML
    # leaves that element empty, so the number existed only after JavaScript ran
    # and no text scan could ever see it, while every visitor could.
    #
    # This matches the SHAPE of that bug, a .length reaching a visible sink, and
    # not the English words: Italian and Albanian carried the same count in their
    # own wording, so a word list would have caught one copy of three.
    # [^\n] and NOT [^;\n]. The line this exists to catch is
    #     var avail = filtered.filter(function(w){ return !w.sold; }).length;
    # and the semicolon inside that callback ended the old character class
    # before it ever reached .length, so the first version of this check went
    # green over the reintroduced bug. Proven by putting the count back and
    # watching the gate go red.
    LEN_VAR = re.compile(r"\bvar\s+(\w+)\s*=\s*[^\n]*\.length\s*;")
    SINK = re.compile(r"\.(?:textContent|innerHTML|innerText)\s*=\s*([^\n]+)")
    for js in sorted(BASE.glob("*/shop/*.js")):
        src = corpus.sig(js)
        counters = set(LEN_VAR.findall(src))
        if not counters:
            continue
        for m in SINK.finditer(src):
            rhs = m.group(1)
            hit = sorted(c for c in counters
                         if re.search(r"\b" + re.escape(c) + r"\b", rhs))
            if hit:
                g_hits += 1
                flag(f"{js.relative_to(BASE).as_posix()}: writes {hit[0]!r}, which is a "
                     f".length, into the page: {rhs.strip()[:60]!r}. No page states how "
                     f"many watches, and a number built at runtime is invisible to check "
                     f"G. Say it without the number.")

    # #shopCount is the element that carried it and now holds a fixed sentence,
    # so a digit in it means a count returned by some other route.
    for p in sorted(BASE.glob("*/shop/index.html")):
        m = re.search(r'id="shopCount"[^>]*>(.*?)</p>',
                      corpus.sig(p), re.S)
        if m and re.search(r"\d", m.group(1)):
            g_hits += 1
            flag(f"{p.relative_to(BASE).as_posix()}: #shopCount contains a digit: "
                 f"{m.group(1).strip()[:60]!r}")

    # --- A. every marker resolves ------------------------------------------
    import gen_stats
    for p in corpus.html_files():
        raw = corpus.raw(p)
        if b'data-stat="' not in raw:
            continue
        lang = p.relative_to(BASE).parts[0]
        lang = lang if lang in LANGS else "en"
        t = raw.decode("utf-8-sig")
        for m in gen_stats.SPAN_RE.finditer(t):
            spans += 1
            key, got = m.group(2), m.group(3)
            ent = "&euro;" in got
            want = gen_stats.render(key, lang, s, ent)
            if got != want:
                flag(f"{p.relative_to(BASE).as_posix()}: data-stat={key} says {got!r}, "
                     f"catalogue says {want!r} (rerun gen_stats.py)")
        # a marker must wrap a whole whitespace-delimited token, or the FAQ
        # visibility probe in gen_shop_index.py turns "€50" into "€ 50"
        for m in gen_stats.SPAN_RE.finditer(t):
            before = t[m.start() - 1] if m.start() else " "
            after = t[m.end()] if m.end() < len(t) else " "
            for ch, side in ((before, "before"), (after, "after")):
                if ch not in " \r\n\t<>&;(,.!?\"":
                    flag(f"{p.relative_to(BASE).as_posix()}: marker glued to {ch!r} "
                         f"{side} it, which breaks the FAQ visibility probe")

    # --- B. no literal leak in the sources ---------------------------------
    live = {s.n, s.b, s.lo, s.hi, s.u10k}
    # the SOURCES, not the rendered output: llms.txt is generated from llms.tpl now,
    # so a literal in the output is correct and only the template can leak
    for name in ("blog_index_data.py", "brand_copy.py", "shop_seo.py", "llms.tpl"):
        f = BASE / name
        if not f.exists():
            continue
        txt = f.read_text(encoding="utf-8")
        # Only a FLOOR claim. A price naming one watch is validated by check E
        # instead, and "to a €199 Hislon" is naming a watch, not stating a bound.
        floor = re.compile(r"(?:from|starting at|a partire da|da|nga)\s*(?:€|&euro;)(\d{2,3})",
                           re.I)
        for m in floor.finditer(txt):
            if int(m.group(1)) == s.lo:
                flag(f"{name}: literal €{m.group(1)} floor where a token belongs "
                     f"({txt[max(0,m.start()-40):m.end()+20].strip()[:60]!r})")

    # --- C. generated surfaces agree with the catalogue --------------------
    for lang in LANGS:
        js = (BASE / lang / "shop" / "shop.js").read_text(encoding="utf-8")
        if ".toLocaleString(" in js:
            flag(f"{lang}/shop/shop.js: toLocaleString is back, the separator "
                 f"is the browser's again")

        # The rate lives in catalog_stats and is copied into four JavaScript
        # files that no import can reach. Moving it from 97 to 92.25 meant
        # editing eight places by hand, and a half-landed change is silent:
        # the Python would price a watch one way and the browser another, only
        # on the client, only after hydration. Now it is loud.
        mr = re.search(r"var EUR_TO_LEK = ([\d.]+);", js)
        if not mr:
            flag(f"{lang}/shop/shop.js: EUR_TO_LEK is gone")
        elif float(mr.group(1)) != float(C.LEK_RATE):
            flag(f"{lang}/shop/shop.js: EUR_TO_LEK {mr.group(1)} != "
                 f"catalog_stats.LEK_RATE {C.LEK_RATE}")

        # The comment above says the rate is copied into FOUR JavaScript files.
        # This loop only ever read three of them. admin.js is the fourth, it
        # previews the Lek price while a watch is being added, and its own comment
        # claimed this check guarded it. It did not, so the one copy nobody was
        # watching could drift and quote a stale price back at the owner.
        if lang == LANGS[0]:
            aj = corpus.sig((BASE / "admin.js"))
            am = re.search(r"var EUR_TO_LEK = ([\d.]+);", aj)
            if not am:
                flag("admin.js: EUR_TO_LEK is gone")
            elif float(am.group(1)) != float(C.LEK_RATE):
                flag(f"admin.js: EUR_TO_LEK {am.group(1)} != "
                     f"catalog_stats.LEK_RATE {C.LEK_RATE}")

        # The price slider must SPAN the catalogue. renderWatches drops anything
        # outside [currentMinPrice, currentMaxPrice], so a watch above the top
        # stop is unreachable by the filter rather than merely mispositioned,
        # and it also vanishes from the pre-rendered grid on hydration. shop.js
        # derives the bounds from WATCHES; the static markup is the pre-hydration
        # and no-JS fallback and has to be checked separately, because no
        # generator owns it.
        if "PRICE_MAX = Math.ceil(" not in js:
            flag(f"{lang}/shop/shop.js: slider bounds are not derived from the "
                 f"catalogue, so a new price outside them would be unfilterable")
        idx = corpus.sig((BASE / lang / "shop" / "index.html"))
        for h, want in (("handleMin", s.lo), ("handleMax", s.hi)):
            mh = re.search(rf'id="{h}"[^>]*aria-valuemin="(\d+)" aria-valuemax="(\d+)"', idx)
            if not mh:
                flag(f"{lang}/shop/index.html: {h} has no aria range")
                continue
            vmin, vmax = int(mh.group(1)), int(mh.group(2))
            if vmin > s.lo or vmax < s.hi:
                flag(f"{lang}/shop/index.html: {h} range {vmin}-{vmax} does not "
                     f"span the catalogue {s.lo}-{s.hi}; a watch outside it "
                     f"cannot be reached by the filter")
        m = re.search(r"var SEP = '(.)'", js)
        if not m or m.group(1) != C.SEP[lang]:
            flag(f"{lang}/shop/shop.js: SEP {m and m.group(1)!r} != {C.SEP[lang]!r}")
    n_rev = 0
    for p in corpus.html_files():
        t = corpus.raw(p).decode("utf-8-sig")
        for m in re.finditer(r'"reviewCount"\s*:\s*"?(\d+)"?|data-review-count>(\d+)<', t):
            v = int(m.group(1) or m.group(2))
            n_rev += 1
            if v != C.REVIEWS:
                flag(f"{p.relative_to(BASE).as_posix()}: reviewCount {v} != {C.REVIEWS}")

    # --- E. every published price pair is arithmetically true --------------
    prices = {w["price"] for w in json.loads(
        corpus.sig((BASE / "watches.json"))) if w.get("price")}
    allow = {}
    af = Path(__file__).resolve().parent / "stats-allow.json"
    if af.exists():
        allow = json.loads(af.read_text(encoding="utf-8"))
    n_pairs = 0
    for p in corpus.html_files():
        t = unescape(corpus.raw(p).decode("utf-8-sig"))
        rel = p.relative_to(BASE).as_posix()
        pairs = [(m, m.group(1), m.group(2)) for m in PAIR.finditer(t)]
        pairs += [(m, m.group(2), m.group(1)) for m in PAIR_LEK.finditer(t)]
        pairs += [(m, m.group(1), m.group(2)) for m in PAIR_SEP.finditer(t)]
        pairs += [(m, m.group(2), m.group(1)) for m in PAIR_LEK_SEP.finditer(t)]
        for m, eur_s, lek_s in pairs:
            eur, lk = int(eur_s), int(lek_s.replace(",", "").replace(".", ""))
            n_pairs += 1
            if C.lek(eur) != lk:
                flag(f"{rel}: {eur} euro is {C.lek(eur):,} L, page says {lek_s}")
            elif eur not in prices and str(eur) not in allow.get(rel, []):
                flag(f"{rel}: {eur} euro is not a price in the catalogue "
                     f"({m.group(0).strip()[:40]!r})")

    # --- F. no hand-typed {n}/{u10k} in the blog corpus ---------------------
    # The allowlist lives under an underscore key, which is inert to check E
    # above for the same reason _why is: no page path is ever named _check_f.
    fallow = allow.get("_check_f") or {}
    seeded = {k for k in fallow if not k.startswith("_")}
    f_pages = f_hits_n = 0
    f_dirty = set()
    for lang in LANGS:
        targets, money = f_targets(lang, s)
        for p in sorted((BASE / lang / "blog").glob("*.html")):
            # blog/index.html is BUILD OUTPUT: gen_blog_index renders the cards
            # from the {lo}/{hi} tokens in blog_index_data.py, so its numbers
            # heal on the next build exactly like a shop or brand page, which is
            # the same reason those are out of scope. It was carried on the
            # allowlist instead until 2026-08-17; excluding it is the honest
            # version and it needs no waiver.
            if p.stem == "index":
                continue
            rel = p.relative_to(BASE).as_posix()
            f_pages += 1
            hits = f_hits(p, lang, targets, money)
            if not hits:
                continue
            f_hits_n += len(hits)
            f_dirty.add(rel)
            if rel in seeded:
                continue
            for key, val, near in hits:
                flag(f"{rel}: hand-typed catalogue {val} ({{{key}}}) beside a "
                     f"catalogue noun. Wrap it as "
                     f'<span data-stat="{key}">{val}</span> and rerun gen_stats.py, '
                     f"or add a dated reason to _check_f in stats-allow.json: "
                     f"{near!r}")
    # the ratchet: an allowlisted page with nothing left to allow is a finding
    for rel in sorted(seeded - f_dirty):
        why = fallow[rel].get("reason") if isinstance(fallow[rel], dict) else None
        flag(f"stats-allow.json _check_f: {rel} no longer carries a live "
             f"catalogue number, so its entry is stale. DELETE the entry if the "
             f"page was cleaned; if instead the catalogue moved and the page now "
             f"prints an OUT OF DATE number, fix the prose first and then delete "
             f"the entry. This allowlist only ever shrinks."
             + (f" (entry said: {why})" if why else ""))
    for rel in sorted(seeded):
        if not (isinstance(fallow[rel], dict) and fallow[rel].get("reason")
                and fallow[rel].get("date")):
            flag(f"stats-allow.json _check_f: {rel} has no reason/date. An "
                 f"unexplained waiver is somebody hiding a finding.")

    # --- D. no bare catalogue number in prose (blog waived until converted) --
    if ALL:
        for lang in LANGS:
            for p in sorted((BASE / lang).rglob("*.html")):
                t = unescape(masked(corpus.raw(p).decode("utf-8-sig")))
                for m in re.finditer(r"(?<![\d.,])(\d{2,3})(?![\d.,])", t):
                    v = int(m.group(1))
                    if v not in live:
                        continue
                    near = t[max(0, m.start() - 60):m.end() + 60]
                    if re.search(NOUN[lang], near, re.I):
                        flag(f"{p.relative_to(BASE).as_posix()}: bare {v} beside a "
                             f"catalogue noun: {near.strip()[:70]!r}")

    print(f"\n  {spans} markers | {n_rev} review counts | {n_pairs} price pairs checked"
          f" | {f_hits_n} typed aggregates in {len(f_dirty)}/{f_pages} blog pages"
          f" ({len(seeded)} allowlisted)"
          + ("" if ALL else " | check D waived, run --all after the blog corpus"))
    print("STATS GATE PASS" if not findings else f"{len(findings)} FINDINGS")
    sys.exit(1 if findings else 0)


# [ERR-010.d] f_targets — what gen_stats would print for the four F keys here
# DOES:   asks the GENERATOR for the string a marker would carry, so the gate
#         holds no second opinion about it; keyed by the DIGITS of that string
#         -> key name, because F_NUM only ever yields digits.
# OUT:    (targets, money) — money is the subset of key names that are prices,
#         which f_hits needs so it can flip the currency test for them.
# NOTES:  lang is passed through because render() takes it for the separator.
#         All four keys are three digits or fewer today, so the separator never
#         appears, but reading the value out of render() rather than str(s.n) is
#         what keeps this true if that ever stops being so.
#         The digit strip is why {lo} works at all: render("lo") is "€50" and a
#         raw rendered-text key could never match the "50" F_NUM produces.
#         Sits below main() so the .a .b .c .d .e letters stay in source order;
#         Python resolves the name when main() runs, not when it is defined.
def f_targets(lang, s):
    import gen_stats
    out = {}
    # Count keys are read straight off Stats, NOT through render(), which now
    # raises on them. Check G forbids the MARKER; this is what still catches a
    # count typed as bare digits in prose, where there is no marker to see.
    for k in F_KEYS:
        out.setdefault(str(getattr(s, k)), k)
    for k in F_MONEY_KEYS:
        digits = re.sub(r"[^\d.,]", "", gen_stats.render(k, lang, s, False))
        # a count and a price that render the same string would make the hit
        # ambiguous; counts win, because dropping a real {lo} is quieter than
        # flagging every price on the page.
        out.setdefault(digits, k)
    return out, set(F_MONEY_KEYS)


# [ERR-010.e] f_hits — one blog page's hand-typed catalogue aggregates
# IN:     p — the page; lang — for the noun table; targets — from f_targets
# OUT:    [(key, value, 120-char context)], empty when the page is clean
# NOTES:  masked() first, which is what blanks a number already living inside a
#         <span data-stat="..."> so a converted page reads clean, along with
#         script, style, svg and the href/src/class/id/srcset attributes.
#         unescape() after masking rather than before, because the offsets
#         masked() writes have to keep pointing at the same characters.
def f_hits(p, lang, targets, money=frozenset()):
    t = unescape(masked(corpus.raw(p).decode("utf-8-sig")))
    out = []
    for m in F_NUM.finditer(t):
        key = targets.get(m.group())
        if not key:
            continue
        if F_UNIT.match(t, m.end()) or F_RANGE_R.match(t, m.end()):
            continue
        before = t[max(0, m.start() - 12):m.start()]
        if F_RANGE_L.search(before):
            continue
        # The currency test runs both ways. A count behind a euro sign is a
        # price and check E owns it; a price NOT behind one is some other 50.
        # bool() is load-bearing: search() returns a Match or None, so an
        # identity or "is not" comparison against a bool is always true.
        if bool(F_CUR.search(before)) != (key in money):
            continue
        # A money key needs a bound verb as well, or every mention of the
        # dearest watch's own price reads as a claim about the whole shop.
        if key in money and not F_BOUND.search(t[max(0, m.start() - 90):m.start()]):
            continue
        # "from 149 to 199 euro" is a per-brand band whose top happens to be
        # the dearest watch. F_RANGE_L cannot see it because the currency sits
        # between the range word and the number, so match that shape here. The
        # low end of a genuine shop range still fires on its own {lo}, which is
        # what keeps this from hiding a real bound claim.
        if key in money and F_RANGE_CUR.search(before):
            continue
        near = t[max(0, m.start() - 60):m.end() + 60]
        if re.search(F_NOUN[lang], near, re.I):
            # masked() left NUL where the markup was; collapse it to whitespace
            # so the quoted context is readable rather than a wall of \x00
            out.append((key, m.group(), " ".join(near.replace("\x00", " ").split())))
    return out


if __name__ == "__main__":
    main()
