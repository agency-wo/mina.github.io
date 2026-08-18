#!/usr/bin/env python3
"""[DB-013] catalog_stats.py — the one home for catalogue-derived numbers + formatting.
DOES:   computes Stats (count, brands, price range, Lek bounds, under-10k count,
        per-brand tallies) from watches.json for internal use, owns the half-up
        Lek conversion, the per-language separator, the {token} vocabulary +
        fill() — which no longer knows any counting token —
        and the owner-reported Google review count.

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

COUNTS ARE NOT PUBLISHED AT ALL any more. {n}, {u10k} and {n:brand} are gone
from TOKEN_RE below: they reported how many watches are LISTED, the shop stocks
considerably more than it lists, so each one understated the shelf on every page
it touched. Stats still computes them because the gates and the generators need
to reason about the catalogue; nothing may print them. {b} and the prices stay.
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
    """[DB-013.a] Half-up, to match Math.round in shop.js (Python round() is banker's)."""
    if not price or currency != "EUR":
        return 0
    return int(price * LEK_RATE / 100 + 0.5) * 100


def nfmt(v, lang):
    """[DB-013.b] Thousands separator for the page's language."""
    return f"{v:,}".replace(",", SEP[lang])


# [DB-013.c] slugify — brand display name -> the slug used in tokens and URLs
def slugify(brand):
    return brand.lower().replace(" ", "-")


# [DB-013.d] Stats — slots-only value bag for the computed catalogue numbers
class Stats:
    __slots__ = ("n", "b", "lo", "hi", "lolek", "hilek", "u10k",
                 "per_brand", "brands_ranked", "brand_lo", "brand_hi")


# [DB-013.e] load — watches.json -> Stats, over LIVE watches only
# DOES:   excludes sold and deleted entries from every number (module docstring
#         explains why {n} is a stock claim); asserts the catalogue is non-empty.
def load(path=None):
    W = json.loads((path or BASE / "watches.json").read_text(encoding="utf-8-sig"))
    # [DB-006] deleted (retired) entries never reach a published number;
    # sold ones are excluded from "live" counts exactly as before
    live = [w for w in W if not w.get("sold") and not w.get("deleted")]
    assert live, "catalogue is empty"
    prices = [w["price"] for w in live if w.get("price")]
    s = Stats()
    s.n = len(live)
    s.lo, s.hi = min(prices), max(prices)
    s.lolek, s.hilek = lek(s.lo), lek(s.hi)
    s.u10k = sum(1 for w in live if w.get("price") and lek(w["price"]) < UNDER)
    s.per_brand = {}
    # Per-brand price bounds, so "Hislon runs 149 to 199 euro" can stop being
    # typed by hand in ~220 places. Same live-only rule as every other number:
    # a sold or deleted watch must not set a brand's floor or ceiling.
    s.brand_lo, s.brand_hi = {}, {}
    for w in live:
        slug = slugify(w["brand"])
        s.per_brand[slug] = s.per_brand.get(slug, 0) + 1
        p = w.get("price")
        if p:
            s.brand_lo[slug] = min(s.brand_lo.get(slug, p), p)
            s.brand_hi[slug] = max(s.brand_hi.get(slug, p), p)
    s.b = len(s.per_brand)
    s.brands_ranked = [b for b, _ in sorted(s.per_brand.items(),
                                            key=lambda kv: (-kv[1], kv[0]))]
    return s


# COUNTING TOKENS ARE RETIRED: {n}, {u10k} and the {n:brand} family are NOT in
# this vocabulary, so fill() raises "unfilled token" on any of them and a count
# left in copy fails the build instead of shipping. They published how many
# watches are LISTED, and the shop holds considerably more stock than it
# publishes, so every one of them understated the shelf. The owner raised it
# more than once. {b} stays, the brand count is accurate; prices stay, they are
# true and they sell. Do not add them back — rewrite the sentence instead.
#
# The per-brand family is lo:/hi:/lolek:/hilek: + a brand slug. Everything after
# the colon is validated against the live catalogue, so a brand that sells out
# raises instead of rendering a stale bound.
TOKEN_RE = re.compile(
    r"\{(b|lo|hi|lolek|hilek|(?:lo|hi|lolek|hilek):[a-z0-9-]+)\}")


# [DB-013.f] brand_value — one per-brand token's value, shared by fill() and
# gen_stats.render() so the generator and the gate cannot disagree about it.
# IN:     key like "lo:hislon"; s — a loaded Stats; lang — for the separator
# OUT:    the rendered string, euro sign included for lo:/hi: exactly as the
#         sitewide {lo}/{hi} do, so a marker still wraps a whole token.
# NOTES:  raises on an unknown brand rather than rendering something plausible.
def brand_value(key, s, lang):
    kind, slug = key.split(":", 1)
    table = {"n": s.per_brand, "lo": s.brand_lo, "hi": s.brand_hi,
             "lolek": s.brand_lo, "hilek": s.brand_hi}[kind]
    assert slug in table, f"unknown brand in token {{{key}}}"
    v = table[slug]
    if kind == "n":
        return str(v)
    if kind in ("lolek", "hilek"):
        return nfmt(lek(v), lang)
    return f"\u20ac{v}"


def fill(text, lang, s=None, brand_items=None):
    """[DB-013.g] Replace every {token}. Raises on an unknown token rather than shipping it.

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
        if ":" in k:
            return brand_value(k, s, lang)
        if k in local:
            return str(local[k])
        if k in ("lolek", "hilek"):
            return nfmt(getattr(s, k), lang)
        return str(getattr(s, k))

    out, n = TOKEN_RE.subn(sub, text)
    leftover = re.findall(r"\{[a-z][a-z0-9:_-]*\}", out)
    assert not leftover, f"unfilled token(s) {leftover} in {text[:70]!r}"
    return out
