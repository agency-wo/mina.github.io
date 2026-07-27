#!/usr/bin/env python3
"""
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

LEK_RATE = 97

# Brands that have a landing page. Others fall back to a breadcrumb without a
# brand level, because a non-final BreadcrumbList item needs a real URL.
BRAND_SLUGS = {
    "Daniel Klein": "daniel-klein",
    "Navimarine": "navimarine",
    "Hislon": "hislon",
    "Philippe Lauren": "philippe-lauren",
}

# Breadcrumb labels. watch.js carries the same strings; change both together.
CRUMBS = {
    "en": {"home": "Home", "shop": "Shop"},
    "it": {"home": "Home", "shop": "Negozio"},
    "sq": {"home": "Kryefaqja", "shop": "Dyqani"},
}


def lek(price, currency="EUR"):
    """Half-up, to match Math.round in shop.js / watch.js (Python round() is banker's)."""
    if not price or currency != "EUR":
        return 0
    return int(price * LEK_RATE / 100 + 0.5) * 100


def price_html(price, currency, lang, small="1.1rem"):
    """Product-page price line.

    Albanian customers judge the Lek figure, so SQ leads with Lek and shows EUR
    second. EN/IT keep EUR first. Mirrored in watch.js.
    """
    if not price:
        return ""
    eur = f"€{price}"
    l = lek(price, currency)
    if not l:
        return eur
    sec = f'<span style="font-size:{small};color:#888;font-weight:500;margin-left:.5rem">'
    if lang == "sq":
        return f'{l:,} L{sec}· {eur}</span>'
    return f'{eur}{sec}· {l:,} L</span>'


def card_price_html(price, currency, lang):
    """Grid-card price line (smaller secondary text). Mirrored in shop.js."""
    if not price:
        return "Price on request"
    eur = ("€" if currency == "EUR" else str(currency)) + f"{price:,}"
    l = lek(price, currency)
    if not l:
        return eur
    sec = '<span style="font-size:.78rem;color:#888;font-weight:400">'
    if lang == "sq":
        return f'{l:,} L{sec} · {eur}</span>'
    return f'{eur}{sec} · {l:,} L</span>'


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
    """Visible breadcrumb for shop pages.

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


def crumb_jsonld(lang, page_url, brand=None, leaf=None):
    """BreadcrumbList matching crumb_html exactly. watch.js builds the same shape."""
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
    t = OPEN_NOW_TEXT[lang]
    return (
        f'<p class="open-now" id="openNow" data-open-now>'
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
        "<script>(function(){var e=document.getElementById('openNow');if(!e)return;"
        "var T=" + _js_texts(t) + ";"
        "try{var p=new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Tirane',weekday:'short',"
        "hour:'2-digit',minute:'2-digit',hour12:false}).formatToParts(new Date());"
        "var g=function(k){for(var i=0;i<p.length;i++)if(p[i].type===k)return p[i].value;return ''};"
        "var d=g('weekday'),m=parseInt(g('hour'),10)*60+parseInt(g('minute'),10);"
        "var sun=d==='Sun',sat=d==='Sat',open=!sun&&m>=510&&m<1230;"
        "var s=e.querySelector('.open-txt');"
        "if(open){e.className='open-now is-open';s.textContent=T.open}"
        "else{e.className='open-now is-shut';"
        "s.textContent=sun?T.monday:(m<510?T.soon:(sat?T.monday:T.tomorrow))}"
        "}catch(x){}})();</script>"
    )


def _js_texts(t):
    import json as _j
    return _j.dumps({k: v for k, v in t.items() if k != "fallback"}, ensure_ascii=False)
