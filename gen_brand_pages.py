#!/usr/bin/env python3
"""
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
]

WA = "https://api.whatsapp.com/send?phone=355676360510&amp;text="

UI = {
    "en": dict(
        h1="{brand} Watches in Albania",
        title="{brand} Watches in Albania - {n} models from €{lo} | Iglisi Watch",
        desc="{brand} watches in stock in Durrës from €{lo}. {n} models, 1-year guarantee, "
             "cash on delivery across Albania. Try them on or order on WhatsApp.",
        crumb_home="Home", crumb_shop="Shop",
        faq_h="{brand} questions",
        all_h="All {n} {brand} watches in stock",
        cta_h="Not sure which one?",
        cta_p="Send us a message and we will help you choose based on your wrist, your style and "
              "your budget. There is no charge for the advice.",
        cta_btn="Ask on WhatsApp",
        back="See all watches",
        wa_msg="Hi, I am interested in your {brand} watches. Which do you have in stock?",
        trust=["Cash on delivery", "1-year guarantee", "Delivery across Albania"],
    ),
    "it": dict(
        h1="Orologi {brand} in Albania",
        title="Orologi {brand} in Albania - {n} modelli da €{lo} | Iglisi Watch",
        desc="Orologi {brand} disponibili a Durazzo da €{lo}. {n} modelli, garanzia 1 anno, "
             "pagamento alla consegna in tutta l'Albania. Provali o ordina su WhatsApp.",
        crumb_home="Home", crumb_shop="Negozio",
        faq_h="Domande su {brand}",
        all_h="Tutti i {n} orologi {brand} disponibili",
        cta_h="Non sai quale scegliere?",
        cta_p="Scrivici e ti aiutiamo a scegliere in base al tuo polso, al tuo stile e al tuo "
              "budget. La consulenza è gratuita.",
        cta_btn="Chiedi su WhatsApp",
        back="Vedi tutti gli orologi",
        wa_msg="Salve, sono interessato agli orologi {brand}. Quali avete disponibili?",
        trust=["Pagamento alla consegna", "Garanzia 1 anno", "Consegna in tutta l'Albania"],
    ),
    "sq": dict(
        h1="Orë {brand} në Shqipëri",
        title="Orë {brand} në Shqipëri - {n} modele nga €{lo} | Iglisi Watch",
        desc="Orë {brand} gjendje në Durrës nga €{lo}. {n} modele, garanci 1 vit, pagesë në "
             "dorëzim në gjithë Shqipërinë. Provojini ose porositni në WhatsApp.",
        crumb_home="Kryefaqja", crumb_shop="Dyqani",
        faq_h="Pyetje për {brand}",
        all_h="Të gjitha {n} orët {brand} në gjendje",
        cta_h="Nuk jeni i sigurt cilën të zgjidhni?",
        cta_p="Na shkruani dhe ju ndihmojmë të zgjidhni sipas dorës, stilit dhe buxhetit tuaj. "
              "Këshilla është pa pagesë.",
        cta_btn="Pyesni në WhatsApp",
        back="Shiko të gjitha orët",
        wa_msg="Pershendetje, jam i interesuar per oret {brand}. Cilat keni ne gjendje?",
        trust=["Para në dorëzim", "Garanci 1 vit", "Dërgesa në gjithë Shqipërinë"],
    ),
}

from brand_copy import COPY  # localized, owner-verified brand copy
from shop_bits import crumb_html, crumb_jsonld, CRUMB_CSS, open_now_html


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def brand_watches(brand):
    """Non-sold watches of a brand, cheapest first (a price ladder reads better)."""
    return sorted((w for w in WATCHES if w["brand"] == brand and not w.get("sold")),
                  key=lambda w: w["price"])


def fill(text, brand, items):
    prices = [w["price"] for w in items]
    return (text.replace("{brand}", brand)
                .replace("{n}", str(len(items)))
                .replace("{lo}", str(min(prices)))
                .replace("{hi}", str(max(prices)))
                .replace("{lolek}", f"{lek(min(prices)):,}")
                .replace("{hilek}", f"{lek(max(prices)):,}"))


def build_main(slug, brand, lang, items):
    ui = {k: (fill(v, brand, items) if isinstance(v, str) else v) for k, v in UI[lang].items()}
    copy = COPY[slug][lang]
    paras = "".join(f"<p>{fill(p, brand, items)}</p>" for p in copy["paras"])
    faqs = "".join(
        '<details class="faq-item"><summary class="faq-question">'
        f'<span class="faq-q-label">{fill(q, brand, items)}</span>'
        '<i class="fas fa-chevron-down" aria-hidden="true"></i></summary>'
        f'<div class="faq-answer"><p>{fill(a, brand, items)}</p></div></details>'
        for q, a in copy["faq"])
    trust = " &middot; ".join(
        f'<span style="white-space:nowrap"><i class="fas {ic}" aria-hidden="true"></i> {t}</span>'
        for ic, t in zip(("fa-check-circle", "fa-shield-alt", "fa-map-marker-alt"), ui["trust"]))
    wa = WA + fill(UI[lang]["wa_msg"], brand, items).replace(" ", "%20").replace(",", "%2C")
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


def head_swaps(html, slug, brand, lang, items):
    ui = UI[lang]
    title = esc(fill(ui["title"], brand, items))
    desc = esc(fill(ui["desc"], brand, items))
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


def build_jsonld(slug, brand, lang, items):
    ui = UI[lang]
    url = f"https://watch.al/{lang}/shop/brand/{slug}.html"
    copy = COPY[slug][lang]
    collection = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": fill(ui["title"], brand, items).split(" | ")[0],
        "description": fill(ui["desc"], brand, items),
        "url": url, "inLanguage": lang,
        "mainEntity": {
            "@type": "ItemList", "name": fill(ui["all_h"], brand, items),
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
            {"@type": "Question", "name": fill(q, brand, items),
             "acceptedAnswer": {"@type": "Answer", "text": fill(a, brand, items)}}
            for q, a in copy["faq"]],
    }
    return "".join(
        '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>"
        for d in (collection, crumbs, faq))


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
    return html


def main():
    out = []
    for lang in ("en", "it", "sq"):
        (BASE / lang / "shop" / "brand").mkdir(parents=True, exist_ok=True)
        for slug, brand in BRANDS:
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
