#!/usr/bin/env python3
"""[DB-008] gen_brand_pages.py — builds the 15 brand landing pages from the shop index.
DOES:   clones each {lang}/shop/index.html, swaps head metadata and <main> for
        brand-specific copy, a static brand-filtered grid, FAQ + matching JSON-LD;
        writes {en,it,sq}/shop/brand/{slug}.html, skipping byte-identical output.

gen_brand_pages.py
Builds brand landing pages at {en,it,sq}/shop/brand/{slug}.html.

Why: brand filtering only ever existed as `?brand=X` query strings, which Google does
not index as separate pages and which carry no unique content. Nothing on the site
could rank for "ore Daniel Klein Shqiperi" / "Navimarine Albania" / "orologi Hislon".

Each page clones {lang}/shop/index.html (so it inherits header, footer, nav and the
shop CSS) and replaces the head metadata and <main> with brand-specific content:
intro copy, a STATIC product grid for that brand, a visible FAQ mirrored exactly by
FAQPage JSON-LD, and CollectionPage + ItemList + BreadcrumbList schema.

shop.js is deliberately NOT loaded here: it hydrates #shopGrid from the full catalog
and would wipe the brand-filtered grid. The container is #brandGrid for the same reason.

Only owner-verified facts appear in the copy. Never claim a crystal type for Daniel
Klein, never state water resistance beyond what a model actually declares.

Run from the repo:  python gen_brand_pages.py
Idempotent.
"""
import json
import re
from pathlib import Path

from catalog_stats import lek, nfmt
from contact import phone  # [CFG-010] en/it reach the owner, sq reaches his father
from gen_shop_index import card, W as WATCHES  # same card markup as the shop grid

BASE = Path(__file__).parent
BOM = b"\xef\xbb\xbf"
SCRIPT_RE = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S)

BRANDS = [
    ("daniel-klein", "Daniel Klein"),
    ("navimarine", "Navimarine"),
    ("hislon", "Hislon"),
    ("philippe-lauren", "Philippe Lauren"),
    ("bigotti", "Bigotti"),
    ("cortebert", "Cortébert"),
    ("pulsar", "Pulsar"),
    ("polotime", "POLOTIME"),
]

# [CFG-010] built per language at the call site: en/it reach the owner, sq his father
def wa_base(lang):
    return f"https://api.whatsapp.com/send?phone={phone(lang)['wa']}&amp;text="

UI = {
    "en": dict(
        h1="{brand} Watches in Albania",
        title="{brand} Watches in Albania - from €{lo} | Iglisi Watch",
        desc="{brand} watches in stock in Durrës from €{lo}. 1-year guarantee, cash on "
             "delivery across Albania. Try them on or order on WhatsApp.",
        crumb_home="Home", crumb_shop="Shop",
        faq_h="{brand} questions",
        all_h="Every {brand} watch we sell",
        cta_h="Not sure which one?",
        cta_p="Send us a message and we will help you choose based on your style and your "
              "budget. There is no charge for the advice.",
        cta_btn="Ask on WhatsApp",
        back="See all watches",
        wa_msg="Hi, I am interested in your {brand} watches. Which do you have in stock?",
        trust=["Cash on delivery", "1-year guarantee", "Delivery across Albania"],
    ),
    "it": dict(
        h1="Orologi {brand} in Albania",
        title="Orologi {brand} in Albania - da €{lo} | Iglisi Watch",
        desc="Orologi {brand} disponibili a Durazzo da €{lo}. Garanzia 1 anno, pagamento "
             "alla consegna in tutta l'Albania. Provali o ordina su WhatsApp.",
        crumb_home="Home", crumb_shop="Negozio",
        faq_h="Domande su {brand}",
        all_h="Tutti gli orologi {brand} che vendiamo",
        cta_h="Non sai quale scegliere?",
        cta_p="Scrivici e ti aiutiamo a scegliere in base al tuo stile e al tuo budget. "
              "La consulenza è gratuita.",
        cta_btn="Chiedi su WhatsApp",
        back="Vedi tutti gli orologi",
        wa_msg="Salve, sono interessato agli orologi {brand}. Quali avete disponibili?",
        trust=["Pagamento alla consegna", "Garanzia 1 anno", "Consegna in tutta l'Albania"],
    ),
    "sq": dict(
        h1="Orë {brand} në Shqipëri",
        title="Orë {brand} në Shqipëri - nga €{lo} | Iglisi Watch",
        desc="Orë {brand} gjendje në Durrës nga €{lo}. Garanci 1 vit, pagesë në "
             "dorëzim në gjithë Shqipërinë. Provojini ose porositni në WhatsApp.",
        crumb_home="Kryefaqja", crumb_shop="Dyqani",
        faq_h="Pyetje për {brand}",
        all_h="Të gjitha orët {brand} që shesim",
        cta_h="Nuk jeni i sigurt cilën të zgjidhni?",
        cta_p="Na shkruani dhe ju ndihmojmë të zgjidhni sipas stilit dhe buxhetit tuaj. "
              "Këshilla është pa pagesë.",
        cta_btn="Pyesni në WhatsApp",
        back="Shiko të gjitha orët",
        wa_msg="Pershendetje, jam i interesuar per oret {brand}. Cilat keni ne gjendje?",
        trust=["Para në dorëzim", "Garanci 1 vit", "Dërgesa në gjithë Shqipërinë"],
    ),
}

from brand_copy import COPY  # localized, owner-verified brand copy
from shop_bits import (crumb_html, crumb_jsonld, CRUMB_CSS, open_now_html,
                       delivery_bar_html, DELIVERY_CSS)


# [DB-008.a] esc — minimal HTML escaping for text landing in attributes/titles
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def brand_watches(brand):
    """[DB-008.b] Non-sold watches of a brand, cheapest first (a price ladder reads better)."""
    return sorted((w for w in WATCHES if w["brand"] == brand and not w.get("sold")),
                  key=lambda w: w["price"])


# [DB-008.c] fill — brand-page token substitution
# DOES:   replaces {brand}/{lo}/{hi}/{lolek}/{hilek} with values scoped to THIS
#         brand's items, so brand copy never quotes a sitewide number.
def fill(text, brand, items, lang='en'):
    # {n} is REFUSED here, not filled. This fill() is private to this module and
    # never consulted catalog_stats.TOKEN_RE, which is exactly how a per-brand
    # count survived the sitewide purge on all 45 brand pages, in <title> and the
    # meta description as well as the grid heading. No page states how many
    # watches: the shop stocks more than it lists.
    assert "{n}" not in text, (
        f"gen_brand_pages.fill: {{n}} is retired. No page states how many watches. "
        f"Rewrite the sentence: {text[:60]!r}")
    # Falsy prices are EXCLUDED, the same rule catalog_stats.load() uses. A watch
    # with no price yet is a real listing but not a bound: the Cortébert
    # rectangular arrived unpriced (2026-08-25) and an unfiltered min() published
    # "from €0" in the <title>, the meta description and the intro paragraph.
    prices = [w["price"] for w in items if w.get("price")]
    assert prices, f"{brand}: every listed watch is unpriced, so there is no range to state"
    return (text.replace("{brand}", brand)
                .replace("{lo}", str(min(prices)))
                .replace("{hi}", str(max(prices)))
                .replace("{lolek}", nfmt(lek(min(prices)), lang))
                .replace("{hilek}", nfmt(lek(max(prices)), lang)))


# [DB-008.d] build_main — the whole <main> of one brand page
# DOES:   hero (h1, intro paras, trust row, open-now), crumb, static card grid,
#         FAQ, WhatsApp CTA and the page-local CSS, assembled from UI + brand COPY.
def build_main(slug, brand, lang, items):
    ui = {k: (fill(v, brand, items, lang) if isinstance(v, str) else v) for k, v in UI[lang].items()}
    copy = COPY[slug][lang]
    paras = "".join(f"<p>{fill(p, brand, items, lang)}</p>" for p in copy["paras"])
    faqs = "".join(
        '<details class="faq-item"><summary class="faq-question">'
        f'<span class="faq-q-label">{fill(q, brand, items, lang)}</span>'
        '<i class="fas fa-chevron-down" aria-hidden="true"></i></summary>'
        f'<div class="faq-answer"><p>{fill(a, brand, items, lang)}</p></div></details>'
        for q, a in copy["faq"])
    trust = " &middot; ".join(
        f'<span style="white-space:nowrap"><i class="fas {ic}" aria-hidden="true"></i> {t}</span>'
        for ic, t in zip(("fa-check-circle", "fa-shield-alt", "fa-map-marker-alt"), ui["trust"]))
    wa = wa_base(lang) + fill(UI[lang]["wa_msg"], brand, items, lang).replace(" ", "%20").replace(",", "%2C")
    cards = "".join(card(w, lang) for w in items)
    return (
        '<main id="main-content">'
        + CRUMB_CSS
        +         '<div class="shop-hero"><div class="max-w-7xl mx-auto px-6">'
        f'<h1>{ui["h1"]}</h1>'
        f'<div class="brand-intro">{paras}</div>'
        f'<p class="brand-trust">{trust}</p>'
        + open_now_html(lang)
        + 
        '</div></div>'
        # crumb sits on the LIGHT content area below the hero. Never above it: a pale
        # band between the dark sticky header and the dark hero cuts the page in half.
        + crumb_html(lang, brand=brand)
        # Same strip the shop index carries, in the same place: directly under the
        # crumb, above the grid. A brand hub is where someone chooses a watch, and
        # it was the one buying page that never told them delivery is free, that
        # they pay the courier, or that they have 30 days. Same component, so the
        # terms can never drift between the two pages.
        + DELIVERY_CSS + delivery_bar_html(lang)
        + '<div class="max-w-7xl mx-auto px-6">'
        f'<h2 class="brand-grid-h">{ui["all_h"]}</h2>'
        f'<div class="shop-grid" id="brandGrid" aria-label="{brand}">{cards}</div>'
        f'<section class="brand-faq"><h2>{ui["faq_h"]}</h2><div class="space-y-2">{faqs}</div></section>'
        f'<section class="brand-cta"><h2>{ui["cta_h"]}</h2><p>{ui["cta_p"]}</p>'
        f'<p><a class="btn-primary" href="{wa}" target="_blank" rel="noopener noreferrer">'
        f'<i class="fab fa-whatsapp" aria-hidden="true"></i> {ui["cta_btn"]}</a>'
        f'<a class="btn-secondary" style="margin-left:.75rem" href="/{lang}/shop/">{ui["back"]}</a></p>'
        '</section>'
        '</div>'
        f'{BRAND_CSS}'
        '</main>'
    )


BRAND_CSS = (
    "<style>"
    ".brand-intro{max-width:62ch;margin:1rem auto 0;display:flex;flex-direction:column;gap:.9rem;text-align:left}"
    ".brand-intro p{color:rgba(255,255,255,.82);line-height:1.65;font-size:.98rem}"
    ".brand-trust{margin:1.5rem auto 0;color:rgba(255,255,255,.7);font-size:.85rem}"
    ".brand-trust i{color:var(--accent-gold,#b4945c)}"
    ".brand-grid-h{font-size:1.5rem;margin:3rem 0 1.25rem}"
    ".brand-faq{margin:3.5rem 0 0}.brand-faq h2{font-size:1.6rem;margin-bottom:1rem}"
    ".brand-cta{margin:3rem 0 4rem;background:var(--bg-soft,#faf7f2);border:1px solid "
    "var(--border-light,#eaeaea);border-radius:1rem;padding:2rem;text-align:center}"
    ".brand-cta h2{font-size:1.5rem;margin-bottom:.6rem}"
    ".brand-cta p{color:var(--text-secondary,#4a4a4a);max-width:60ch;margin:0 auto 1.25rem}"
    "</style>"
)


# [DB-008.e] head_swaps — retarget the cloned head at the brand URL
# DOES:   rewrites title/description/OG/twitter/canonical and all four hreflang
#         alternates to the brand page, and re-relativizes asset paths one level
#         deeper (/shop/ -> /shop/brand/). The \s+ hreflang subtlety is inline.
def head_swaps(html, slug, brand, lang, items):
    ui = UI[lang]
    title = esc(fill(ui["title"], brand, items, lang))
    desc = esc(fill(ui["desc"], brand, items, lang))
    url = f"https://watch.al/{lang}/shop/brand/{slug}.html"
    img = "https://watch.al" + re.sub(r"\.jpe?g$", ".webp", items[0]["image"], flags=re.I)
    subs = [
        (r"<title>[^<]*</title>", f"<title>{title}</title>"),
        (r'(<meta name="description" content=")[^"]*(")', r"\g<1>" + desc + r"\g<2>"),
        (r'(<meta property="og:title" content=")[^"]*(")', r"\g<1>" + title + r"\g<2>"),
        (r'(<meta property="og:description" content=")[^"]*(")', r"\g<1>" + desc + r"\g<2>"),
        (r'(<meta property="og:url" content=")[^"]*(")', r"\g<1>" + url + r"\g<2>"),
        (r'(<meta property="og:image" content=")[^"]*(")', r"\g<1>" + img + r"\g<2>"),
        (r'(<meta name="twitter:title" content=")[^"]*(")', r"\g<1>" + title + r"\g<2>"),
        (r'(<meta name="twitter:description" content=")[^"]*(")', r"\g<1>" + desc + r"\g<2>"),
        (r'(<link rel="canonical" href=")[^"]*(")', r"\g<1>" + url + r"\g<2>"),
    ]
    for pat, rep in subs:
        html = re.sub(pat, rep, html, count=1)
    for lg in ("en", "it", "sq"):
        # \s+ rather than a single space: the EN and SQ shop indexes pad this attribute, so a
        # one-space pattern matched only the IT link and left en and sq pointing at /shop/.
        # Ten of the twelve brand pages shipped that way from July until 2026-08-04.
        html = re.sub(rf'(<link rel="alternate" hreflang="{lg}"\s+href=")[^"]*(")',
                      r"\g<1>" + f"https://watch.al/{lg}/shop/brand/{slug}.html" + r"\g<2>",
                      html, count=1)
    html = re.sub(r'(<link rel="alternate" hreflang="x-default"\s+href=")[^"]*(")',
                  r"\g<1>" + f"https://watch.al/en/shop/brand/{slug}.html" + r"\g<2>",
                  html, count=1)
    # asset paths move one level deeper: /shop/ -> /shop/brand/
    html = html.replace('src="shop.js', 'src="../shop.js').replace('href="watch.css', 'href="../watch.css')
    return html


# [DB-008.f] build_jsonld — CollectionPage(+ItemList) + BreadcrumbList + FAQPage
# DOES:   emits the three schema blocks from the same strings the visible page uses,
#         so schema and page can never diverge.
def build_jsonld(slug, brand, lang, items):
    ui = UI[lang]
    url = f"https://watch.al/{lang}/shop/brand/{slug}.html"
    copy = COPY[slug][lang]
    collection = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": fill(ui["title"], brand, items, lang).split(" | ")[0],
        "description": fill(ui["desc"], brand, items, lang),
        "url": url, "inLanguage": lang,
        "mainEntity": {
            "@type": "ItemList", "name": fill(ui["all_h"], brand, items, lang),
            "numberOfItems": len(items),
            "itemListElement": [
                {"@type": "ListItem", "position": i,
                 "url": f'https://watch.al/{lang}/shop/{w["id"]}.html',
                 "name": f'{w["brand"]} {w["model"]}'}
                for i, w in enumerate(items, 1)],
        },
    }
    crumbs = crumb_jsonld(lang, url, brand=brand)
    faq = {
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": fill(q, brand, items, lang),
             "acceptedAnswer": {"@type": "Answer", "text": fill(a, brand, items, lang)}}
            for q, a in copy["faq"]],
    }
    return "".join(
        '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>"
        for d in (collection, crumbs, faq))


# [DB-008.g] build_page — one complete brand page from the cloned shop index
# DOES:   strips the clone's JSON-LD, installs ours, swaps head + <main>, removes
#         shop.js and watch-effects (they would fight the static grid), and makes
#         sure stock-live.js IS loaded; every removal/addition is asserted.
def build_page(slug, brand, lang):
    items = brand_watches(brand)
    assert items, f"no watches for {brand}"
    src = (BASE / lang / "shop" / "index.html").read_text(encoding="utf-8-sig")

    # strip every JSON-LD block from the cloned shop index, then add ours
    html = SCRIPT_RE.sub("", src)
    html = html.replace("</head>", build_jsonld(slug, brand, lang, items) + "</head>", 1)
    html = head_swaps(html, slug, brand, lang, items)

    # replace <main>...</main> wholesale
    i, j = html.index("<main"), html.index("</main>") + len("</main>")
    html = html[:i] + build_main(slug, brand, lang, items) + html[j:]

    # shop.js would hydrate the grid from the FULL catalog and wipe the brand filter
    html = re.sub(r'\s*<script src="\.\./shop\.js[^>]*></script>', "", html)
    assert "shop.js" not in html, f"{lang}/{slug}: shop.js still referenced"

    # watch-effects is a shop-index-only feature. Any [data-balance-wheel] div it
    # would have driven is left empty, and the :empty CSS hides it.
    html = re.sub(r'\s*<script src="/watch-effects[^"]*"[^>]*></script>', "", html)
    assert '<script src="/watch-effects' not in html, f"{lang}/{slug}: watch-effects still referenced"

    # The cloned shop index ends with a "Need help choosing?" panel that names ONE
    # brand and links to that brand's buying guide. Inherited unchanged it put a
    # Navimarine guide on the Bigotti, Hislon, Daniel Klein and Philippe Lauren
    # pages. A brand page already carries its own "Not sure which one?" CTA inside
    # <main>, so the panel is a duplicate as well as a wrong-brand link: drop it.
    html, n_panel = re.subn(
        r'\s*<section style="text-align:center[^"]*"[^>]*>(?:(?!</section>).)*?'
        r'blog-nudge-btn(?:(?!</section>).)*?</section>', "", html, flags=re.S)
    assert n_panel == 1, f"{lang}/{slug}: need-help panel not found to strip (got {n_panel})"
    assert "blog-nudge-btn" not in html, f"{lang}/{slug}: need-help panel survived"

    # [UI-001] brand grids are static cards — stock-live.js flips them from the
    # CRM feed. The cloned shop index deliberately does NOT carry the tag
    # (shop.js merges live stock into its own data), so it is added here.
    # The anchor matches ANY ?v=, deliberately. It was pinned to v=23 and the
    # 2026-08-25 bump to v=24 broke it; the assert below caught that, but a
    # cache-bust sweep must not be able to reach in here at all.
    if '<script src="/stock-live.js' not in html:
        html = re.sub(r'(<script src="/shared\.js\?v=\d+" defer></script>)',
                      r'\1\n  <script src="/stock-live.js?v=2" defer></script>',
                      html, count=1)
    assert '<script src="/stock-live.js' in html, f"{lang}/{slug}: stock-live.js missing"
    return html


# [DB-008.h] main — build all lang x brand pages, write only what changed
# OUT:    prints SKIP (no change) / OK per page and a final Written: N count.
def main():
    out = []
    # [DB-008.i] P128: a brand whose every watch is sold (or retired) has no
    # page to build — brand_watches() returns [] and build_page asserts. That
    # assert used to kill the WHOLE run, and since this generator is a step of
    # the stock-sync Action, one ordinary sale wedged the CRM→site sync for
    # good: the static pages froze and only a red Action log said so. Bigotti
    # has four watches; selling four is a normal week. Now the sold-out brand
    # is skipped, its existing page is left standing (stock-live.js flips its
    # cards to Sold at runtime, and the shop index still lists the brand), and
    # the run continues for everyone else.
    empty = [b for _, b in BRANDS if not brand_watches(b)]
    if empty:
        print(f"  NOTE: no unsold watches for {', '.join(empty)} — "
              f"leaving those brand pages as they are (runtime marks them Sold)")
    for lang in ("en", "it", "sq"):
        (BASE / lang / "shop" / "brand").mkdir(parents=True, exist_ok=True)
        for slug, brand in BRANDS:
            if not brand_watches(brand):
                continue
            p = BASE / lang / "shop" / "brand" / f"{slug}.html"
            html = build_page(slug, brand, lang)
            old = p.read_text(encoding="utf-8-sig") if p.exists() else None
            if old == html:
                print(f"  SKIP (no change): {lang}/shop/brand/{slug}.html")
                continue
            p.write_bytes(BOM + html.encode("utf-8"))
            n = html.count('<article class="watch-card')
            out.append(str(p))
            print(f"  OK: {lang}/shop/brand/{slug}.html ({n} watches)")
    print(f"\nDone. Written: {len(out)}")


if __name__ == "__main__":
    main()
