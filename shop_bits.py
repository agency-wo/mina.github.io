#!/usr/bin/env python3
"""[DB-014] shop_bits.py — shared HTML building blocks for the three shop generators.
DOES:   one definition each of the price strings (Lek-first for SQ), the visible
        shop breadcrumb + its BreadcrumbList, the delivery reassurance bar, the
        open-now indicator, and the retired-watch redirect stub.

shop_bits.py
Shared building blocks for the three shop generators (gen_product_pages.py,
gen_shop_index.py, gen_brand_pages.py).

Anything here that is also produced at runtime by shop.js / watch.js MUST be kept
byte-identical in both places, otherwise the static HTML and the rendered page
disagree (that bug was found and fixed in Session B and must not come back).

Kept here so there is exactly one definition of:
  * the Lek conversion and the price string, including the Albanian Lek-first order
  * the shop breadcrumb (labels, brand slugs, markup)
  * the "open now" walk-in indicator
"""

from catalog_stats import LEK_RATE, lek, nfmt  # one definition, see catalog_stats.py

# Brands that have a landing page. Others fall back to a breadcrumb without a
# brand level, because a non-final BreadcrumbList item needs a real URL.
# Watches marked Swiss Made on the physical watch, owner-verified with the case
# in hand, never inferred from a dial photo. Cortébert joined Hislon 2026-08-24.
# The three shop.js copies carry a hand-mirrored array of this set.
SWISS_BRANDS = {"Hislon", "Cortébert"}

BRAND_SLUGS = {
    "Daniel Klein": "daniel-klein",
    "Navimarine": "navimarine",
    "Hislon": "hislon",
    "Philippe Lauren": "philippe-lauren",
    "Bigotti": "bigotti",
    "Cortébert": "cortebert",
    "Pulsar": "pulsar",
    "POLOTIME": "polotime",
}

# Breadcrumb labels. watch.js carries the same strings; change both together.
CRUMBS = {
    "en": {"home": "Home", "shop": "Shop"},
    "it": {"home": "Home", "shop": "Negozio"},
    "sq": {"home": "Kryefaqja", "shop": "Dyqani"},
}


# A watch with no price yet. ONE home, because it is rendered in four places
# that must agree byte for byte: price_html and card_price_html below, the
# product-page template in scripts/make-new-watch-pages.py, and watchCard() in
# each {lang}/shop/shop.js. Both renderers here used to return the ENGLISH
# string in all three languages while shop.js returned the translated one, so an
# Albanian card said "Price on request" until hydration and "Çmimi me kërkesë"
# after it. Nothing caught it because no watch was priceless until the Cortébert
# rectangular arrived unpriced on 2026-08-25.
PRICE_ON_REQUEST = {
    "en": "Price on request",
    "it": "Prezzo su richiesta",
    "sq": "Çmimi me kërkesë",
}


def price_html(price, currency, lang, small="1.1rem"):
    """[DB-014.a] Product-page price line.

    Albanian customers judge the Lek figure, so SQ leads with Lek and shows EUR
    second. EN/IT keep EUR first. Mirrored in watch.js.
    """
    if not price:
        return PRICE_ON_REQUEST[lang]
    eur = f"€{price}"
    l = lek(price, currency)
    if not l:
        return eur
    sec = f'<span style="font-size:{small};color:#888;font-weight:500;margin-left:.5rem">'
    if lang == "sq":
        return f'{nfmt(l, lang)} L{sec}· {eur}</span>'
    return f'{eur}{sec}· {nfmt(l, lang)} L</span>'


def card_price_html(price, currency, lang):
    """[DB-014.b] Grid-card price line (smaller secondary text). Mirrored in shop.js."""
    if not price:
        # A span, not a bare string. The phrase must not inherit the tag's 1.45rem
        # display serif: at that size it runs ~190px in EN and ~220px in IT, which
        # overflows the 344px card footer in the 3-column desktop grid and wraps the
        # Enquire button onto its own row. Mirrored by fmt() in all three shop.js.
        return f'<span class="por">{PRICE_ON_REQUEST[lang]}</span>'
    eur = ("€" if currency == "EUR" else str(currency)) + nfmt(price, lang)
    l = lek(price, currency)
    if not l:
        return eur
    sec = '<span style="font-size:.78rem;color:#888;font-weight:400">'
    if lang == "sq":
        return f'{nfmt(l, lang)} L{sec} · {eur}</span>'
    return f'{eur}{sec} · {nfmt(l, lang)} L</span>'


CRUMB_CSS = (
    "<style>"
    ".shop-crumb{max-width:80rem;margin:0 auto;padding:1rem 1.5rem 0;font-size:.8rem;"
    "color:var(--text-secondary,#4a4a4a);display:flex;align-items:center;gap:.5rem;flex-wrap:wrap}"
    ".shop-crumb a{color:var(--accent-gold-accessible,#7a6240);text-decoration:underline;"
    "text-underline-offset:2px}"
    ".shop-crumb a:hover{color:var(--accent-gold,#b4945c)}"
    ".shop-crumb i{font-size:.65rem;color:#bbb}"
    ".shop-crumb [aria-current]{color:var(--text-primary,#2a2a2a);font-weight:600}"
    "</style>"
)


def crumb_html(lang, brand=None, leaf=None):
    """[DB-014.c] Visible breadcrumb for shop pages.

    Deliberately NOT class="breadcrumb": shared.css force-hides that
    (`.breadcrumb{display:none!important}`) sitewide, so reusing it would render nothing.
    """
    c = CRUMBS[lang]
    sep = '<i class="fas fa-chevron-right" aria-hidden="true"></i>'
    parts = [f'<a href="/{lang}/">{c["home"]}</a>', sep,
             f'<a href="/{lang}/shop/">{c["shop"]}</a>']
    slug = BRAND_SLUGS.get(brand or "")
    if brand and slug and leaf:
        parts += [sep, f'<a href="/{lang}/shop/brand/{slug}.html">{brand}</a>']
    tail = leaf if leaf else brand
    if tail:
        parts += [sep, f'<span aria-current="page">{tail}</span>']
    return ('<nav class="shop-crumb" aria-label="Breadcrumb">' + "".join(parts) + "</nav>")


# --- delivery reassurance bar ---------------------------------------------------
# The three objections a buyer outside Durres has before they will click a card:
# what does delivery cost, when do I pay, and what if it is wrong. All three are
# answered in full on {lang}/shop/delivery.html, which this bar links to.
# Icons are limited to the 64 glyphs in the subsetted font (fa-truck is not one).
DELIVERY_CSS = (
    "<style>"
    ".shop-deliv{max-width:80rem;margin:.75rem auto 0;padding:.7rem 1.5rem;font-size:.82rem;"
    "display:flex;align-items:center;gap:.5rem 1.4rem;flex-wrap:wrap;"
    "color:var(--text-secondary,#4a4a4a)}"
    ".shop-deliv-in{display:flex;align-items:center;gap:.5rem 1.4rem;flex-wrap:wrap;"
    "background:#f7f5f0;border-left:3px solid var(--accent-gold,#b4945c);border-radius:0 .5rem .5rem 0;"
    "padding:.6rem 1rem;width:100%}"
    ".shop-deliv span{display:inline-flex;align-items:center;gap:.4rem}"
    ".shop-deliv i{color:var(--accent-gold-accessible,#7a6240);font-size:.8rem}"
    ".shop-deliv a{color:var(--accent-gold-accessible,#7a6240);text-decoration:underline;"
    "text-underline-offset:2px;font-weight:600;margin-left:auto;display:inline-flex;"
    "align-items:center;gap:.35rem;white-space:nowrap}"
    ".shop-deliv a:hover{color:var(--accent-gold,#b4945c)}"
    "@media(max-width:640px){.shop-deliv a{margin-left:0}}"
    "</style>"
)

# Wording is a summary of {lang}/shop/delivery.html and must not outrun it: free
# delivery, pay the courier, 30 days. No figure that is not on that page.
DELIVERY_BAR = {
    "en": (("fas fa-store", "Free delivery anywhere in Albania"),
           ("fas fa-money-bill", "Pay the courier when it arrives"),
           ("fas fa-arrow-left", "30 days to return it"),
           "How ordering works"),
    "it": (("fas fa-store", "Consegna gratuita in tutta l&rsquo;Albania"),
           ("fas fa-money-bill", "Pagate il corriere alla consegna"),
           ("fas fa-arrow-left", "30 giorni per il reso"),
           "Come funziona l&rsquo;ordine"),
    "sq": (("fas fa-store", "D&euml;rges&euml; falas kudo n&euml; Shqip&euml;ri"),
           ("fas fa-money-bill", "Paguani korrierin kur mb&euml;rrin"),
           ("fas fa-arrow-left", "30 dit&euml; p&euml;r ta kthyer"),
           "Si funksionon porosia"),
}


def delivery_bar_html(lang):
    """[DB-014.d] Slim reassurance strip linking to the delivery, payment and returns page."""
    *points, link = DELIVERY_BAR[lang]
    items = "".join(
        f'<span><i class="{icon}" aria-hidden="true"></i>{text}</span>' for icon, text in points)
    return ('<div class="shop-deliv"><div class="shop-deliv-in">' + items
            + f'<a href="/{lang}/shop/delivery.html">{link}'
              '<i class="fas fa-chevron-right" aria-hidden="true"></i></a></div></div>')


def crumb_jsonld(lang, page_url, brand=None, leaf=None):
    """[DB-014.e] BreadcrumbList matching crumb_html exactly. watch.js builds the same shape."""
    c = CRUMBS[lang]
    items = [
        {"@type": "ListItem", "position": 1, "name": c["home"],
         "item": f"https://watch.al/{lang}/"},
        {"@type": "ListItem", "position": 2, "name": c["shop"],
         "item": f"https://watch.al/{lang}/shop/"},
    ]
    slug = BRAND_SLUGS.get(brand or "")
    if brand and slug and leaf:
        items.append({"@type": "ListItem", "position": 3, "name": brand,
                      "item": f"https://watch.al/{lang}/shop/brand/{slug}.html"})
    tail = leaf if leaf else brand
    if tail:
        items.append({"@type": "ListItem", "position": len(items) + 1, "name": tail,
                      "item": page_url})
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": items}


# --- open-now walk-in indicator -------------------------------------------------
# Mon-Sat 08:30-20:30, closed Sunday (matches the LocalBusiness openingHoursSpecification).
# Uses Europe/Tirane so a visitor abroad still sees the shop's real state, and degrades
# to the plain hours line when JS is unavailable.
OPEN_NOW_TEXT = {
    "en": {"fallback": "Mon to Sat, 8:30 to 20:30",
           "open": "Open now, until 20:30", "soon": "Opens today at 8:30",
           "tomorrow": "Opens tomorrow at 8:30", "monday": "Opens Monday at 8:30"},
    "it": {"fallback": "Lun-Sab, 8:30-20:30",
           "open": "Aperto ora, fino alle 20:30", "soon": "Apre oggi alle 8:30",
           "tomorrow": "Apre domani alle 8:30", "monday": "Apre lunedì alle 8:30"},
    "sq": {"fallback": "Hën-Sht, 8:30-20:30",
           "open": "Hapur tani, deri 20:30", "soon": "Hapet sot në 8:30",
           "tomorrow": "Hapet nesër në 8:30", "monday": "Hapet të hënën në 8:30"},
}


def open_now_html(lang):
    """[DB-014.f] Walk-in indicator. The strings ride on data attributes and shared.js does the
    work.

    It used to carry its own inline <script>, which never ran once: these pages set
    script-src 'self' with no unsafe-inline and no nonce, so the browser refused it
    on all 186 pages that had it. A page cannot fix that itself; the logic has to
    live in a file the CSP already trusts.
    """
    t = OPEN_NOW_TEXT[lang]
    data = " ".join(f'data-on-{k}="{v}"' for k, v in t.items() if k != "fallback")
    return (
        f'<p class="open-now" id="openNow" data-open-now {data}>'
        f'<span class="open-dot" aria-hidden="true"></span>'
        f'<span class="open-txt">{t["fallback"]}</span></p>'
        "<style>"
        ".open-now{display:inline-flex;align-items:center;gap:.5rem;font-size:.85rem;"
        "font-weight:600;color:var(--text-secondary,#4a4a4a);margin:.35rem 0 0}"
        ".open-dot{width:.5rem;height:.5rem;border-radius:50%;background:#bbb;flex:none}"
        ".open-now.is-open .open-dot{background:#2a9d5c;box-shadow:0 0 0 3px rgba(42,157,92,.18)}"
        ".open-now.is-open{color:#1a7a3f}"
        ".open-now.is-shut .open-dot{background:#c0392b}"
        "</style>"
    )


# [DB-006] the retired-watch stub (P125 W4) — lives HERE because
# gen_product_pages runs its page loop at module level and cannot be imported
# without regenerating every page; tests import this module instead.
STUB_TEXT = {
    "en": ("This watch is no longer available.", "Browse the shop"),
    "it": ("Questo orologio non è più disponibile.", "Vai al negozio"),
    "sq": ("Kjo orë nuk është më në katalog.", "Shiko dyqanin"),
}


def stub_html(w, lang):
    """[DB-014.g] noindex + instant refresh + canonical to the shop (the watch-29 pattern).
    gen_sitemap drops noindex pages by its own generic rule; the data never
    leaves watches.json, and clearing the flag regenerates the full page."""
    name = f'{w.get("brand", "")} {w.get("model", "")}'.strip() or w["id"]
    text, link = STUB_TEXT[lang]
    target = f"/{lang}/shop/"
    return (
        f'<!DOCTYPE html>\n<html lang="{lang}" dir="ltr">\n<head>\n'
        '  <meta charset="UTF-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'  <title>{name} | Iglisi Watch</title>\n'
        '  <meta name="robots" content="noindex, follow">\n'
        f'  <meta http-equiv="refresh" content="0; url={target}">\n'
        f'  <link rel="canonical" href="https://watch.al{target}">\n'
        '</head>\n<body>\n'
        f'  <p>{text} <a href="{target}">{link}</a>.</p>\n'
        '</body>\n</html>\n'
    )


# [DB-014.e] BRANDS — slug to display name for every brand with a hub page.
# Lives here rather than in gen_brand_pages because shop_seo needs it too, to
# link the hubs from the shop index, and gen_brand_pages imports gen_shop_index,
# which imports shop_seo. Two copies of this list would drift the day a brand is
# added and only one of them was edited.
BRANDS = [
    ("daniel-klein", "Daniel Klein"),
    ("navimarine", "Navimarine"),
    ("hislon", "Hislon"),
    ("philippe-lauren", "Philippe Lauren"),
    ("bigotti", "Bigotti"),
    ("cortebert", "Cortébert"),
    ("pulsar", "Pulsar"),
    ("polotime", "POLOTIME"),
    ("casio", "Casio"),
    ("citizen", "Citizen"),
]
