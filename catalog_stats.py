#!/usr/bin/env python3
"""
catalog_stats.py
The single source for every published number derived from watches.json, and the
single per-language number formatter.

Owner rule, 2026-08: "wherever numbers that are supposed to change continuously
need not have fixated numbers". The shop holds considerably more stock than is
published and it moves every month, so a number typed into a page is wrong the
moment it is typed. Everything here is computed at build time and written by a
generator; nothing is typed twice.

Kept here so there is exactly one definition of:
  * the half-up Lek conversion. There were SIX copies of that formula, one of
    them dead code, and they had already begun to disagree about whether a sold
    watch counts.
  * the thousands separator, which is a comma in English and a dot in Italian and
    Albanian. It was a comma everywhere in generated markup and a dot in most
    IT/SQ prose, so the same page printed 8,200 L in a price line and 8.200 L two
    paragraphs down.
  * the token vocabulary and fill()
  * the Google review count

{n} EXCLUDES SOLD. Every sentence it lands in is a stock claim ("{n} models in
stock in Durres"), itemlist() already excludes sold, and a sold watch keeps its
card only as a merchandising choice. Unified while nothing is sold, so the change
renders byte-identically.
"""
import json
import re
from pathlib import Path

BASE = Path(__file__).parent
LEK_RATE = 97

# Google reviews. ONE home. The owner reports this; nothing derives it.
# 107 -> 106 (2026-08-03) -> 104 (2026-08-05).
REVIEWS = 104

# Mirrored byte for byte by group() in {en,it,sq}/shop/shop.js. Never
# toLocaleString(): the browser's locale data decides the separator, so an
# Italian phone reflowed the grid from 18,300 L to 18.300 L after hydration and
# the static markup and the rendered page disagreed.
SEP = {"en": ",", "it": ".", "sq": "."}

UNDER = 10000  # the "watches under 10,000 Lek" threshold: a premise, not a catalogue value


def lek(price, currency="EUR"):
    """Half-up, to match Math.round in shop.js (Python round() is banker's)."""
    if not price or currency != "EUR":
        return 0
    return int(price * LEK_RATE / 100 + 0.5) * 100


def nfmt(v, lang):
    """Thousands separator for the page's language."""
    return f"{v:,}".replace(",", SEP[lang])


def slugify(brand):
    return brand.lower().replace(" ", "-")


class Stats:
    __slots__ = ("n", "b", "lo", "hi", "lolek", "hilek", "u10k",
                 "per_brand", "brands_ranked")


def load(path=None):
    W = json.loads((path or BASE / "watches.json").read_text(encoding="utf-8-sig"))
    live = [w for w in W if not w.get("sold")]
    assert live, "catalogue is empty"
    prices = [w["price"] for w in live if w.get("price")]
    s = Stats()
    s.n = len(live)
    s.lo, s.hi = min(prices), max(prices)
    s.lolek, s.hilek = lek(s.lo), lek(s.hi)
    s.u10k = sum(1 for w in live if w.get("price") and lek(w["price"]) < UNDER)
    s.per_brand = {}
    for w in live:
        s.per_brand[slugify(w["brand"])] = s.per_brand.get(slugify(w["brand"]), 0) + 1
    s.b = len(s.per_brand)
    s.brands_ranked = [b for b, _ in sorted(s.per_brand.items(),
                                            key=lambda kv: (-kv[1], kv[0]))]
    return s


TOKEN_RE = re.compile(r"\{(n|b|lo|hi|lolek|hilek|u10k|n:[a-z0-9-]+)\}")


def fill(text, lang, s=None, brand_items=None):
    """Replace every {token}. Raises on an unknown token rather than shipping it.

    brand_items scopes {n}/{lo}/{hi} to one brand, which is what the brand pages
    need; without it the tokens are sitewide.
    """
    s = s or load()
    if brand_items is not None:
        prices = [w["price"] for w in brand_items if w.get("price")]
        local = {"n": len(brand_items), "lo": min(prices), "hi": max(prices),
                 "lolek": nfmt(lek(min(prices)), lang),
                 "hilek": nfmt(lek(max(prices)), lang)}
    else:
        local = {}

    def sub(m):
        k = m.group(1)
        if k.startswith("n:"):
            slug = k[2:]
            assert slug in s.per_brand, f"unknown brand in token {{{k}}}"
            return str(s.per_brand[slug])
        if k in local:
            return str(local[k])
        if k in ("lolek", "hilek"):
            return nfmt(getattr(s, k), lang)
        return str(getattr(s, k))

    out, n = TOKEN_RE.subn(sub, text)
    leftover = re.findall(r"\{[a-z][a-z0-9:_-]*\}", out)
    assert not leftover, f"unfilled token(s) {leftover} in {text[:70]!r}"
    return out
