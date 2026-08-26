#!/usr/bin/env python3
# [DB-021] gen_article_cta.py — the article shop-bridge button, derived not typed.
# DOES:   For every blog article carrying a data-shop-bridge box, picks the watch
#         that currently best fits the article's declared ROLE and rewrites the
#         box's button to point at that watch's product page in that language.
# IN:     watches.json, and one authored attribute per article:
#             <div class="info-box" data-shop-bridge data-cta-role="battery">
#         An article with a bridge box and no role is treated as role "entry".
# OUT:    Rewrites the button paragraph in place. Mirrors each file's own BOM and
#         EOL, writes only on change, prints a per-role tally.
# CALLS:  catalog_stats for nothing but the shared load discipline; the picking
#         rules live here because they are editorial, not arithmetic.
#
# WHY THIS EXISTS
#   Article prose is the ONE surface in this repo no generator owns, which is why
#   it rots: the shop, the brand pages, llms.txt and every data-stat marker heal
#   on a build and articles do not. The bridge box shipped in 38 articles per
#   language pointing at /{lang}/shop/, which is both a dead-flat CTA and a
#   standing breach of "every CTA links to an exact product page, never the shop
#   index".
#   The obvious fix, writing a watch id into each of the 114 boxes, would have
#   created 114 things to maintain by hand and 114 things to go stale the first
#   time one of those watches sold. The owner said it plainly: make them change
#   any time we add a watch, do not leave a hard coded number.
#   So an article declares a ROLE and never a watch. Same split as data-stat: the
#   argument around the fact is human, the fact is derived.
#
# NOTES:  A role that resolves to nothing is a BUILD FAILURE, not a quietly empty
#         box. Silence is how a broken CTA ships.
#         Roles are ordered predicates over live stock, so a sell-out re-points
#         the affected articles on the next build and an arrival can win a role
#         back. Verified by marking two watches sold and re-running: water,
#         sapphire, bracelet and entry all moved, the rest held.
#         Two predicates read description_en because there is no water-resistance
#         or crystal field on a watch. That is sound here: the sapphire predicate
#         matches exactly the 8 watches CLAUDE.md permits to claim it, the seven
#         Hislons plus romanson-bh3054gbr, so the description already IS the
#         source of truth for the claim.
#         The button carries no price, deliberately. The product page owns the
#         price and a price in a button is one more thing to go stale.
import hashlib
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
LANGS = ("en", "it", "sq")

watches = json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))


def _live():
    return [w for w in watches if not w.get("sold") and w.get("price")]


def _cheapest(rows):
    return min(rows, key=lambda w: (w["price"], w["id"])) if rows else None


def _dearest(rows):
    return max(rows, key=lambda w: (w["price"], w["id"])) if rows else None


def _desc(rx):
    return [w for w in _live() if re.search(rx, w["description_en"], re.I)]


def _style(s):
    return [w for w in _live() if s in w.get("styles", [])]


# Ordered fallbacks per role: the first list that is non-empty wins. Every role
# ends in a fallback that cannot be empty while the shop has any stock at all,
# so a role never dies just because one watch sold.
def _mid():
    """The band most sales actually come from: 56 of 66 priced watches sit at or
    below 100 euro and the median is 72, so a default offer drawn from the whole
    range would skew to the floor and never show the middle."""
    return [w for w in _live() if 55 <= w["price"] <= 110]


ROLES = {
    # deterministic: the name means "the cheapest" or "the dearest", so rotating
    # it would make the word wrong
    "entry":       lambda: [_live()],
    "top":         lambda: [_live()],
    # rotated: the name means "a watch of this kind", and there are many
    "popular":     lambda: [_mid(), _live()],
    "battery":     lambda: [_desc(r"\b\d+[- ]year battery"), _style("digital"), _live()],
    "water":       lambda: [_desc(r"\b\d+\s*(?:ATM|BAR)\b|\b\d{2,3}\s*m water"), _style("sport"), _live()],
    "sapphire":    lambda: [_desc(r"sapphire"), _live()],
    "bracelet":    lambda: [_desc(r"steel bracelet|five-link|three-link"), _mid(), _live()],
    "chronograph": lambda: [_style("chronograph"), _live()],
    "dress":       lambda: [_style("dress"), _mid(), _live()],
    "gold":        lambda: [_style("gold-tone"), _live()],
}
FIXED = {"entry", "top"}


def pick(role, seed=""):
    """[DB-021.a] The current best watch for a role. Raises rather than returns None.

    Everything except entry and top is ROTATED by a hash of the article slug. The
    first cut was not, and 96 of 114 boxes resolved to the single cheapest watch,
    which is the exact failure related_for's own docstring records: "Nothing on any
    page ever pointed at the 149 to 199 end of the counter, so a shop with a top
    tier never once offered it." Rotating on the slug rather than on list order
    keeps the choice stable across runs and independent of how watches.json is
    sorted, while spreading the offer across the range.
    """
    assert role in ROLES, f"unknown cta role {role!r}; known: {sorted(ROLES)}"
    for cands in ROLES[role]():
        if not cands:
            continue
        if role in FIXED:
            return _dearest(cands) if role == "top" else _cheapest(cands)
        # Hash the ARTICLE to a stable price point, then take the live candidate
        # nearest it. Indexing into the candidate list instead (hash % len) is
        # stable across runs but NOT across stock changes: selling one watch
        # shifts every later index, and a test selling a single watch moved 30
        # articles. That would rewrite ~90 files and move 90 sitemap lastmod
        # dates every time stock changed, which tells Google those pages changed
        # when only the shop did. Anchoring on price means selling a watch moves
        # only the articles it was actually nearest to.
        lo = min(w["price"] for w in cands)
        hi = max(w["price"] for w in cands)
        frac = int(hashlib.md5(f"{role}:{seed}".encode()).hexdigest(), 16) % 1000 / 1000
        target = lo + frac * (hi - lo)
        return min(cands, key=lambda w: (abs(w["price"] - target), w["id"]))
    raise AssertionError(f"role {role!r} resolved to no watch; is anything in stock?")



_EN_SLUG = {}


def en_slug_of(lang, stem):
    """[DB-021.b] Map any language's slug back to the family's EN slug, so the
    rotation seed is the FAMILY. Seeding on the local filename would offer three
    different watches for one article."""
    if not _EN_SLUG:
        for q in (BASE / "en" / "blog").glob("*.html"):
            if q.name == "index.html":
                continue
            src = q.read_text(encoding="utf-8-sig")
            _EN_SLUG[("en", q.stem)] = q.stem
            for lg in ("it", "sq"):
                m = re.search(rf'hreflang="{lg}" href="https://watch\.al/{lg}/blog/([\w-]+)\.html"', src)
                if m:
                    _EN_SLUG[(lg, m.group(1))] = q.stem
    return _EN_SLUG.get((lang, stem), stem)


LABEL = {"en": "See the {n}", "it": "Vedi il {n}", "sq": "Shihni {n}"}
ARIA = {"en": "See the {n} in the shop", "it": "Vedi il {n} nel negozio",
        "sq": "Shihni {n} në dyqan"}

# the box's button paragraph, which is the only part this generator owns
BTN_RE = re.compile(
    r'(<div class="info-box" data-shop-bridge[^>]*>.*?)'
    r'(<p style="margin-top:1rem"><a href=")([^"]*)("[^>]*class="btn-secondary"[^>]*>)([^<]*)(</a></p>)',
    re.S)
ROLE_RE = re.compile(r'<div class="info-box" data-shop-bridge(?:\s+data-cta-role="([a-z-]+)")?')


def style_of(raw):
    return ("\r\n" if b"\r\n" in raw else "\n", raw.startswith(b"\xef\xbb\xbf"))


def main():
    tally, written, skipped, offered = {}, 0, 0, set()
    for lang in LANGS:
        for p in sorted((BASE / lang / "blog").glob("*.html")):
            if p.name == "index.html":
                continue
            raw = p.read_bytes()
            eol, bom = style_of(raw)
            # assert the file is internally consistent rather than a fixed shape:
            # core.autocrlf with no .gitattributes means the correct EOL depends on
            # which machine checked out, so a writer mirrors and a check asserts
            # consistency. A mixed file is the real bug.
            assert raw.count(b"\r\n") in (0, raw.count(b"\n")), f"{p}: mixed line endings"
            t = (raw[3:] if bom else raw).decode("utf-8")
            if "data-shop-bridge" not in t:
                continue
            role = (ROLE_RE.search(t).group(1) or "popular")
            # seed on the family, not the file, so the three languages of one
            # article all offer the same watch
            w = pick(role, en_slug_of(lang, p.stem))
            name = f'{w["brand"]} {w["model"]}'.strip()
            href = f'/{lang}/shop/{w["id"]}.html'
            assert (BASE / href.lstrip("/")).exists(), f"{p}: {href} does not exist"

            def sub(m):
                return (m.group(1) + m.group(2) + href
                        + f'" class="btn-secondary" aria-label="{ARIA[lang].format(n=name)}">'
                        + LABEL[lang].format(n=name) + m.group(6))

            new, n = BTN_RE.subn(sub, t, count=1)
            assert n == 1, f"{p}: shop-bridge button not matched"
            tally[role] = tally.get(role, 0) + 1
            offered.add(w['id'])
            if new != t:
                # `t` was decoded from the file's own bytes, so it already carries
                # that file's line endings. Re-applying eol here would double them.
                p.write_bytes((b"\xef\xbb\xbf" if bom else b"") + new.encode("utf-8"))
                written += 1
            else:
                skipped += 1
    print("  roles used: " + ", ".join(f"{r}={n}" for r, n in sorted(tally.items())))
    print(f"  distinct watches offered: {len(offered)}")
    print(f"  bridge buttons: {written} rewritten, {skipped} unchanged")


if __name__ == "__main__":
    main()
