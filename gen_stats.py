#!/usr/bin/env python3
"""
gen_stats.py
Keeps every catalogue-derived number in hand-written pages in step with
watches.json.

The owner's rule: the shop holds considerably more stock than it publishes and it
moves every month, so a number typed into a page is wrong the moment it is typed.
Generated pages already computed theirs. These do not, because no generator owns
them, so the number is wrapped in a marker instead and this rewrites it:

    Browse our collection of <span data-stat="n">57</span> brand-new watches

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
    "n": lambda s, lang, ent: str(s.n),
    "b": lambda s, lang, ent: str(s.b),
    "u10k": lambda s, lang, ent: str(s.u10k),
    "lo": lambda s, lang, ent: f"{'&euro;' if ent else '€'}{s.lo}",
    "hi": lambda s, lang, ent: f"{'&euro;' if ent else '€'}{s.hi}",
    "lolek": lambda s, lang, ent: f"{C.nfmt(s.lolek, lang)} L",
    "lolek~": lambda s, lang, ent: f"~{C.nfmt(s.lolek, lang)} L",
    "hilek": lambda s, lang, ent: f"{C.nfmt(s.hilek, lang)} L",
}


def render(key, lang, s, ent):
    if key.startswith("n:"):
        slug = key[2:]
        assert slug in s.per_brand, f"unknown brand in data-stat={key!r}"
        return str(s.per_brand[slug])
    assert key in RENDER, f"unknown data-stat key {key!r}"
    return RENDER[key](s, lang, ent)


SPAN_RE = re.compile(r'(<span data-stat="([a-z0-9:~-]+)">)(.*?)(</span>)', re.S)


def read(p):
    raw = p.read_bytes()
    bom = raw.startswith(BOM)
    body = raw[3:] if bom else raw
    crlf = body.count(b"\r\n") == body.count(b"\n") and body.count(b"\n") > 0
    return body.decode("utf-8").replace("\r\n", "\n"), bom, crlf


def write(p, t, bom, crlf, raw_before):
    out = (BOM if bom else b"") + (t.replace("\n", "\r\n") if crlf else t).encode("utf-8")
    if out == raw_before:
        return False
    p.write_bytes(out)
    return True


def sweep(files=None):
    """Refresh every marker on disk. Idempotent by construction."""
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


def main():
    if "--seed" in sys.argv:
        import seed_stats
        seed_stats.run(BASE, read, write)
    sweep()


if __name__ == "__main__":
    main()
