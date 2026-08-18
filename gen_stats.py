#!/usr/bin/env python3
"""[DB-011] gen_stats.py — refreshes catalogue numbers embedded in hand-written pages.
DOES:   sweeps every HTML file for <span data-stat="..."> markers and rewrites
        their contents from watches.json via catalog_stats. Counting markers are
        REFUSED, not refreshed: no page states how many watches. Also regenerates
        llms.txt from llms.tpl. --seed delegates the one-off marker insertion
        to seed_stats.py.

gen_stats.py
Keeps every catalogue-derived number in hand-written pages in step with
watches.json.

The owner's rule: the shop holds considerably more stock than it publishes and it
moves every month, so a number typed into a page is wrong the moment it is typed.
Generated pages already computed theirs. These do not, because no generator owns
them, so the number is wrapped in a marker instead and this rewrites it:

    Watches from <span data-stat="lo">&euro;50</span>, each with a 1-year guarantee

Why a marker span rather than a token in the source, or a phrase-anchored regex:
  * the static HTML keeps a correct value, so a crawler sees a number rather than
    a placeholder, and a missed build degrades to stale instead of broken
  * span is in faq-build.py's inline-tag list, so strip_tags() removes it without
    inserting whitespace and the FAQ verbatim comparator still matches
  * a regex anchored on the current value works exactly once and then silently
    matches nothing, which is how scripts/fix-reviews.py rotted

HARD RULE: the span must wrap a whitespace-delimited whole token, never a
fragment glued to punctuation. gen_shop_index.py's FAQ visibility probe turns
every tag into a space, so "&euro;<span>50</span>" becomes "&euro; 50" and fails
the probe, while "<span>&euro;50</span>" survives it. That is why data-stat="lo"
renders the currency symbol too.

    python gen_stats.py --seed    insert markers at known anchors (once per page)
    python gen_stats.py           refresh every marker from watches.json
"""
import re
import sys
from pathlib import Path

import catalog_stats as C

BASE = Path(__file__).parent
LANGS = ("en", "it", "sq")
BOM = b"\xef\xbb\xbf"

# How each key renders. The euro keys include the symbol so the span stays a
# whole token; the "~" variants keep the approximation sign inside.
RENDER = {
    # No "n" and no "u10k": counting markers are retired, see render() below.
    "b": lambda s, lang, ent: str(s.b),
    "lo": lambda s, lang, ent: f"{'&euro;' if ent else '€'}{s.lo}",
    "hi": lambda s, lang, ent: f"{'&euro;' if ent else '€'}{s.hi}",
    "lolek": lambda s, lang, ent: f"{C.nfmt(s.lolek, lang)} L",
    "lolek~": lambda s, lang, ent: f"~{C.nfmt(s.lolek, lang)} L",
    "hilek": lambda s, lang, ent: f"{C.nfmt(s.hilek, lang)} L",
}


# [DB-011.a] render — one marker's new text
# DOES:   resolves a data-stat key (including per-brand n:slug) through RENDER;
#         unknown keys/brands are hard errors, never silently left stale.
# IN:     key; lang for the separator; s — Stats; ent — keep &euro; entity form
FORBIDDEN_KEYS = ("n", "u10k")


def render(key, lang, s, ent):
    # Counting markers are retired. data-stat="n", "u10k" and the "n:brand"
    # family published how many watches are LISTED, and the shop stocks more
    # than it lists, so each one understated the shelf every time it rendered.
    # Raising here is the second lock; the first is that catalog_stats.TOKEN_RE
    # no longer knows the tokens, and the third is the check in verify-stats.
    if key in FORBIDDEN_KEYS or key.startswith("n:"):
        raise KeyError(
            f"gen_stats.render: data-stat={key!r} is retired. No page states how "
            f"many watches; the shop stocks more than it lists. Rewrite the "
            f"sentence rather than reviving the marker.")
    # The per-brand family (lo:/hi:/lolek:/hilek: + slug) resolves through
    # catalog_stats so this generator and verify-stats hold one opinion of it.
    if ":" in key:
        v = C.brand_value(key, s, lang)
        # brand_value returns a literal euro sign; a page that writes entities
        # needs &euro; instead, the same swap RENDER["lo"] makes.
        return v.replace("\u20ac", "&euro;") if ent else v
    assert key in RENDER, f"unknown data-stat key {key!r}"
    return RENDER[key](s, lang, ent)


SPAN_RE = re.compile(r'(<span data-stat="([a-z0-9:~-]+)">)(.*?)(</span>)', re.S)


# [DB-011.b] read — decode a page while remembering its BOM and CRLF-ness
# OUT:    (LF-normalized text, had_bom, was_crlf) so write() can restore both.
def read(p):
    raw = p.read_bytes()
    bom = raw.startswith(BOM)
    body = raw[3:] if bom else raw
    crlf = body.count(b"\r\n") == body.count(b"\n") and body.count(b"\n") > 0
    return body.decode("utf-8").replace("\r\n", "\n"), bom, crlf


# [DB-011.c] write — re-encode in the page's own byte form; write only on change
# OUT:    True when the file was actually rewritten (drives the sweep counter).
def write(p, t, bom, crlf, raw_before):
    out = (BOM if bom else b"") + (t.replace("\n", "\r\n") if crlf else t).encode("utf-8")
    if out == raw_before:
        return False
    p.write_bytes(out)
    return True


def sweep(files=None):
    """[DB-011.d] Refresh every marker on disk. Idempotent by construction."""
    s = C.load()
    written = hits = 0
    for p in sorted(files or BASE.rglob("*.html")):
        raw = p.read_bytes()
        if b'data-stat="' not in raw:
            continue
        lang = p.relative_to(BASE).parts[0]
        lang = lang if lang in LANGS else "en"
        t, bom, crlf = read(p)
        n = 0

        def sub(m):
            nonlocal n
            n += 1
            # keep whichever encoding the file already used, so a rewrite never
            # churns the byte form of a page that uses entities
            ent = "&euro;" in m.group(3) or "&euro;" in t[:m.start()][-400:]
            return m.group(1) + render(m.group(2), lang, s, ent) + m.group(4)

        t = SPAN_RE.sub(sub, t)
        hits += n
        if write(p, t, bom, crlf, raw):
            written += 1
    print(f"  markers refreshed: {hits} | files rewritten: {written}")
    return hits



def render_llms():
    """[DB-011.e] llms.txt introduces the shop to language models and was the least accurate
    page on the site: it claimed 75 guides for months. It is a template now."""
    s = C.load()
    n_art = len([f for f in (BASE / "en" / "blog").glob("*.html")
                 if f.stem != "index"
                 and "noindex" not in f.read_bytes().decode("utf-8-sig").lower()])
    tpl = (BASE / "llms.tpl").read_text(encoding="utf-8")
    # {articles} is not a catalogue token, so it is resolved before fill() runs;
    # fill() refuses to ship a token it does not recognise.
    out = C.fill(tpl.replace("{articles}", str(n_art)), "en", s)
    tgt = BASE / "llms.txt"
    if tgt.read_bytes() != out.encode("utf-8"):
        tgt.write_bytes(out.encode("utf-8"))
        print("  WROTE llms.txt")
    else:
        print("  SKIP llms.txt")


# [DB-011.f] main — optional --seed migration, then llms.txt, then the sweep
def main():
    if "--seed" in sys.argv:
        import seed_stats
        seed_stats.run(BASE, read, write)
    render_llms()
    sweep()


if __name__ == "__main__":
    main()
