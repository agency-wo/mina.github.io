#!/usr/bin/env python3
"""[DB-017] gen_product_pages.py — static product-page renderer (RUNS ON IMPORT).
DOES:   rewrites every {lang}/shop/{watch-id}.html in place from watches.json:
        hero div, specs/buy/related sections, crumb, titles/metas/JSON-LD,
        WhatsApp deep links; deleted watches become redirect stubs.
NOTES:  the page loop at the bottom is MODULE-LEVEL — importing this file
        regenerates all pages. Edit comments/docstrings only, never structure.

gen_product_pages.py
Pre-renders product page body content (H1, price, description, CTA, trust row)
into static HTML so AI crawlers and non-JS environments see real content.

watch.js continues to run for real users (progressive enhancement):
it overwrites #watch-content at runtime, so there is no functional change
for browsers — only crawlers and view-source benefit.

Run from repo root:  python gen_product_pages.py
Idempotent: safe to run multiple times.
"""
import hashlib
import json
import re
import urllib.parse
from pathlib import Path

from catalog_stats import REVIEWS, lek, nfmt
from contact import phone  # [CFG-010] en/it reach the owner, sq reaches his father
from shop_bits import (PRICE_ON_REQUEST, SWISS_BRANDS, crumb_html, crumb_jsonld,
                       CRUMB_CSS, open_now_html,
                       price_html as shared_price_html, stub_html)

BASE = Path(__file__).parent

watches = json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))


# brand+model is not unique for the Hislon Classic / Classic Queen families, so those
# titles get the reference appended to stay distinct.
DUP_NAMES = {}
for _w in watches:
    _n = f'{_w["brand"]} {_w["model"]}'.strip()
    DUP_NAMES[_n] = DUP_NAMES.get(_n, 0) + 1

LANGS = {
    "en": {
        "desc_key": "description_en",
        # must equal what watch.js builds at runtime (see its `var desc = ...`)
        "meta_tail": " Available at Iglisi Watch, Durrës, Albania.",
        "swiss_desc_prefix": "Swiss watch by {brand}. ",
        "back_href": "/en/shop/",
        "back_label": "Back to shop",
        "ref_label": "Ref.",
        "sold_text": "This watch has been sold.",
        "was_label": "Was",
        "cta_label": "Order on WhatsApp",
        "ig_label": "Instagram",
        "swiss_label": "Swiss Brand",
        "trust": [
            ('<span class="trust-item" style="color:#1a7a3f;font-weight:600">'
             '<i class="fas fa-money-bill" aria-hidden="true" style="color:#1a7a3f"></i>'
             " Cash on delivery</span>"),
            ('<span class="trust-item">'
             '<i class="fas fa-shield-alt" aria-hidden="true"></i>'
             " 1-year guarantee</span>"),
            ('<span class="trust-item">'
             '<i class="fas fa-star" aria-hidden="true"></i>'
             " Brand new &amp; genuine</span>"),
            ('<span class="trust-item">'
             '<i class="fas fa-clock" aria-hidden="true"></i>'
             " Mon–Sat 8:30–20:30</span>"),
        ],
        "title_tail": "Buy in Durrës, Albania",
        "specs_h": "Details",
        "spec_brand": "Brand",
        "spec_ref": "Reference",
        "spec_cond": "Condition",
        "spec_price": "Price",
        "spec_avail": "Availability",
        "avail_val": "In stock in Durrës",
        "buy_h": "Delivery, payment and guarantee",
        "buy_items": [
            "1-year guarantee on every watch we sell.",
            "Cash on delivery anywhere in Albania, including Tirana.",
            "Free delivery, normally 3 to 7 days.",
            "30 days to return it in store if it is not right.",
            "Try it on first at our workshop on Rruga Aleksander Goga, Durrës.",
        ],
        "related_h": "What else we would show you at the counter",
    },
    "it": {
        "desc_key": "description_it",
        "meta_tail": " Disponibile da Iglisi Watch, Durazzo, Albania.",
        "swiss_desc_prefix": "Orologio svizzero {brand}. ",
        "back_href": "/it/shop/",
        "back_label": "Torna al negozio",
        "ref_label": "Rif.",
        "sold_text": "Questo orologio è stato venduto.",
        "was_label": "Prima",
        "cta_label": "Ordina su WhatsApp",
        "ig_label": "Instagram",
        "swiss_label": "Marchio Svizzero",
        "trust": [
            ('<span class="trust-item" style="color:#1a7a3f;font-weight:600">'
             '<i class="fas fa-money-bill" aria-hidden="true" style="color:#1a7a3f"></i>'
             " Pagamento alla consegna</span>"),
            ('<span class="trust-item">'
             '<i class="fas fa-shield-alt" aria-hidden="true"></i>'
             " Garanzia 1 anno</span>"),
            ('<span class="trust-item">'
             '<i class="fas fa-star" aria-hidden="true"></i>'
             " Nuovo &amp; originale</span>"),
            ('<span class="trust-item">'
             '<i class="fas fa-clock" aria-hidden="true"></i>'
             " Lun–Sab 8:30–20:30</span>"),
        ],
        "title_tail": "Orologi a Durazzo",
        "specs_h": "Dettagli",
        "spec_brand": "Marca",
        "spec_ref": "Riferimento",
        "spec_cond": "Condizione",
        "spec_price": "Prezzo",
        "spec_avail": "Disponibilità",
        "avail_val": "Disponibile a Durazzo",
        "buy_h": "Consegna, pagamento e garanzia",
        "buy_items": [
            "Garanzia di 1 anno su ogni orologio che vendiamo.",
            "Pagamento alla consegna in tutta l’Albania, Tirana inclusa.",
            "Consegna gratuita, normalmente da 3 a 7 giorni.",
            "30 giorni per restituirlo in negozio se non va bene.",
            "Provalo prima nel nostro laboratorio in Rruga Aleksander Goga, Durazzo.",
        ],
        "related_h": "Cosa vi mostreremmo al banco",
    },
    "sq": {
        "desc_key": "description_sq",
        "meta_tail": " E disponueshme tek Iglisi Watch, Durrës, Shqipëri.",
        "swiss_desc_prefix": "Orë zvicerane {brand}. ",
        "back_href": "/sq/shop/",
        "back_label": "Kthehu në dyqan",
        "ref_label": "Ref.",
        "sold_text": "Kjo orë është shitur.",
        "was_label": "Ishte",
        "cta_label": "Porosit në WhatsApp",
        "ig_label": "Instagram",
        "swiss_label": "Markë Zvicerane",
        "trust": [
            ('<span class="trust-item" style="color:#1a7a3f;font-weight:600">'
             '<i class="fas fa-money-bill" aria-hidden="true" style="color:#1a7a3f"></i>'
             " Para në dorëzim</span>"),
            ('<span class="trust-item">'
             '<i class="fas fa-shield-alt" aria-hidden="true"></i>'
             " Garanci 1 vit</span>"),
            ('<span class="trust-item">'
             '<i class="fas fa-star" aria-hidden="true"></i>'
             " E re &amp; origjinale</span>"),
            ('<span class="trust-item">'
             '<i class="fas fa-clock" aria-hidden="true"></i>'
             " Hën–Sht 8:30–20:30</span>"),
        ],
        "title_tail": "Blej Orë në Durrës",
        "specs_h": "Detaje",
        "spec_brand": "Marka",
        "spec_ref": "Referenca",
        "spec_cond": "Gjendja",
        "spec_price": "Çmimi",
        "spec_avail": "Disponueshmëria",
        "avail_val": "Gjendje në Durrës",
        "buy_h": "Dërgesa, pagesa dhe garancia",
        "buy_items": [
            "Garanci 1-vjeçare për çdo orë që shesim.",
            "Pagesë në dorëzim kudo në Shqipëri, përfshirë Tiranën.",
            "Dërgesa falas, zakonisht 3 deri në 7 ditë.",
            "30 ditë për ta kthyer në dyqan nëse nuk ju përshtatet.",
            "Provojeni fillimisht në punishten tonë në Rrugën Aleksander Goga, Durrës.",
        ],
        "related_h": "Çfarë do t’ju tregonim te banaku",
    },
}


def title_for(w, lang):
    """[DB-017.a] Product <title>. MUST stay byte-identical to the string watch.js builds at runtime.
    The reference is included only when brand+model is not unique, which is the only
    thing separating watch-1/3/8 (Hislon Classic) and watch-2/5 (Hislon Classic Queen)."""
    cfg = LANGS[lang]
    name = f'{w["brand"]} {w["model"]}'.strip()
    ref = w.get("reference", "")
    if ref and DUP_NAMES.get(name, 0) > 1:
        name += f" {ref}"
    price = w.get("price")
    price_part = f" - €{price}" if price else ""
    return f'{name}{price_part} | {cfg["title_tail"]}'


def replace_watch_content(html: str, new_div: str) -> str:
    """[DB-017.b] Replace <div id="watch-content"...>...</div> with new_div.
    Uses depth-counting so it correctly handles nested divs (idempotent)."""
    m = re.search(r'<div id="watch-content"[^>]*>', html)
    if not m:
        return html
    start = m.start()
    pos = m.end()
    depth = 1
    end = pos
    while depth > 0 and pos < len(html):
        next_open = html.find("<div", pos)
        next_close = html.find("</div>", pos)
        if next_close == -1:
            break
        if next_open != -1 and next_open < next_close:
            depth += 1
            pos = next_open + 4
        else:
            depth -= 1
            end = next_close + 6  # len("</div>") == 6
            pos = next_close + 6
    return html[:start] + new_div + html[end:]


def build_price_html(price, currency, lang="en"):
    """[DB-017.c] SQ leads with Lek, EN/IT with EUR. Mirrored by watch.js."""
    if not price:
        return PRICE_ON_REQUEST[lang]
    return shared_price_html(price, currency, lang)


# [DB-017.d] build_img_html — the hero <picture> with condition badge + sale ribbon
# DOES:   webp source with jpg fallback, eager/high-priority load (it is the LCP),
#         Sold overrides the condition badge, and the discount ribbon logic below.
def build_img_html(w, cfg):
    image = w.get("image", "")
    if not image:
        return ""
    webp = image
    jpg = re.sub(r"\.webp$", ".jpg", image, flags=re.IGNORECASE)
    alt = f'{w["brand"]} {w["model"]}'
    sold = w.get("sold", False)
    badge = "Sold" if sold else w.get("condition", "New")
    # The catalogue's discounts were invisible here: the old renderer injected the
    # CSS for a sale ribbon and then never emitted one. Pinned top-RIGHT so it can
    # never sit on top of the condition badge, which is top-left on this page.
    sale = ""
    op, p = w.get("originalPrice"), w.get("price")
    if op and p and op > p:
        sale = f'<span class="sale-badge">-{round((op - p) / op * 100)}%</span>'
    return (
        f'<div class="watch-img-wrap">'
        f"<picture>"
        f'<source srcset="{webp}" type="image/webp">'
        f'<img src="{jpg}" alt="{alt}" fetchpriority="high" loading="eager">'
        f"</picture>"
        f'<span class="watch-badge-pg">{badge}</span>{sale}'
        f"</div>"
    )


# Risk reversal. Every line compresses that language's own shop/delivery.html and must
# never outrun it. Glyphs are the three shop_bits.DELIVERY_BAR already uses, so the site
# speaks one visual language; fa-truck and fa-undo are NOT in the subsetted font.
RISK = {
    "en": {"points": [("fas fa-store", "Free delivery anywhere in Albania, 3 to 7 days"),
                      ("fas fa-money-bill", "Pay the courier at the door, in cash"),
                      ("fas fa-arrow-left", "Not right? Hand it back without paying")],
           "link": "How ordering works"},
    "it": {"points": [("fas fa-store", "Consegna gratuita in tutta l&rsquo;Albania, da 3 a 7 giorni"),
                      ("fas fa-money-bill", "Pagate il corriere alla porta, in contanti"),
                      ("fas fa-arrow-left", "Non va bene? Restituitelo senza pagare")],
           "link": "Come funziona l&rsquo;ordine"},
    "sq": {"points": [("fas fa-store", "D&euml;rges&euml; falas kudo n&euml; Shqip&euml;ri, 3 deri n&euml; 7 dit&euml;"),
                      ("fas fa-money-bill", "Paguani korrierin te dera, me para n&euml; dor&euml;"),
                      ("fas fa-arrow-left", "Nuk ju p&euml;rshtatet? Kthejani pa paguar")],
           "link": "Si funksionon porosia"},
}

# The watchmaker and the aftercare, which is the part no Instagram seller can copy.
# Every claim is already made somewhere in this repo: the bench-checked line restates
# the shop index banner, the battery price and the free bracelet sizing come from
# delivery.html, the strap materials from the strap-replacement service page. Straps
# are leather, steel and rubber; NATO is not stocked and must never be claimed.
MAKER = {
    "en": {"h": "Bought from the watchmaker",
           "p": ("We have run the repair bench in Durr&euml;s since 2009 and repaired more than "
                 "350,000 watches. Every watch here is checked on that bench before it is listed. "
                 "Afterwards you keep the workshop: we size the bracelet free at the counter, fit a "
                 '<a href="/en/services/strap-replacement.html">leather, steel or rubber strap</a>'
                 " when you want a change, and put in a "
                 '<a href="/en/services/battery-replacement.html">new battery for 200 to 600 Lek</a>'
                 " while you wait, whether or not you bought the watch from us.")},
    "it": {"h": "Comprato dall&rsquo;orologiaio",
           "p": ("Gestiamo il banco di riparazione a Durazzo dal 2009 e abbiamo riparato oltre "
                 "350.000 orologi. Ogni orologio qui viene controllato su quel banco prima di essere "
                 "messo in vendita. Dopo, l&rsquo;officina resta vostra: regoliamo il bracciale gratis "
                 "al banco, montiamo un "
                 '<a href="/it/services/sostituzione-cinturino.html">cinturino in pelle, acciaio o gomma</a>'
                 " quando volete cambiare, e mettiamo una "
                 '<a href="/it/services/sostituzione-batteria.html">pila nuova per 200-600 Lek</a>'
                 " mentre aspettate, anche se l&rsquo;orologio non l&rsquo;avete comprato da noi.")},
    "sq": {"h": "Bler&euml; nga mjeshtri i or&euml;ve",
           "p": ("E mbajm&euml; banakun e riparimeve n&euml; Durr&euml;s që nga viti 2009 dhe kemi "
                 "riparuar mbi 350.000 or&euml;. &Ccedil;do or&euml; k&euml;tu kontrollohet n&euml; at&euml; "
                 "banak p&euml;rpara se t&euml; listohet. Pas blerjes, punishtja mbetet e juaja: e "
                 "rregullojm&euml; byzylykun falas te banaku, montojm&euml; nj&euml; "
                 '<a href="/sq/services/nderrimi-rripit.html">rrip l&euml;kure, &ccedil;eliku ose gome</a>'
                 " kur doni ndryshim, dhe vendosim nj&euml; "
                 '<a href="/sq/services/nderrimi-baterise.html">bateri t&euml; re p&euml;r 200 deri n&euml; 600 Lek&euml;</a>'
                 " nd&euml;rsa prisni, edhe nëse or&euml;n nuk e keni bler&euml; te ne.")},
}

# The 5.0 rating is real and verifiable, and it has never once been visible
# on a phone anywhere on this site: shared.css hides .review-badge below 768px in two
# separate rules. A fresh class avoids fighting them with !important.
GRATING = {
    "en": (f"Iglisi Watch on Google, rated 5.0 from {REVIEWS} reviews", "Google 5.0"),
    "it": (f"Iglisi Watch su Google, 5.0 su {REVIEWS} recensioni", "Google 5.0"),
    "sq": (f"Iglisi Watch n&euml; Google, 5.0 nga {REVIEWS} vler&euml;sime", "Google 5.0"),
}
REVIEWS_URL = ("https://search.google.com/local/reviews"
               "?placeid=ChIJU3JyAljB0RMRdoAB2vYR5oo")
CALL_BAR_ARIA = {"en": "Quick call", "it": "Chiamata rapida", "sq": "Telefonat&euml; e shpejt&euml;"}


# WhatsApp is the whole checkout, so the message is the order form. Three changes from
# what these buttons used to send:
#   * intent, not a question. "can you confirm it is still available?" invites a yes and
#     ends the conversation; "I would like to order" starts a sale.
#   * the price, in that language's currency order, so there is nothing to negotiate
#     back and forth about before the shop can act.
#   * the page it came from. That is the attribution: the owner reads the inbox and
#     knows which page earned the message, with no analytics and no consent gate, and
#     the link opens the exact watch with its photo.
# The Albanian used to open "Pershendetje, jam i interesuar per oren" with the
# diacritics stripped out, in the shop's primary market language.
WA = {
    "en": {"order": "Hi, I would like to order the {name}{ref}, {price}. From {url}",
           "ask": "Hi, I have a question about the {name}{ref}, {price}. From {url}",
           "help": "Hi, I am not sure which watch to choose. Budget: . It is for: . From {url}",
           # [DB-003] the sold page keeps capturing demand — same channel,
           # same wording family as stock-live.js's runtime notify link
           "notify": "Hi! The {name}{ref} on {url} is sold out - please let me know when it is back."},
    "it": {"order": "Salve, vorrei ordinare l’orologio {name}{ref}, {price}. Da {url}",
           "ask": "Salve, ho una domanda sull’orologio {name}{ref}, {price}. Da {url}",
           "help": "Salve, non so quale orologio scegliere. Budget: . È per: . Da {url}",
           "notify": "Ciao! L’orologio {name}{ref} su {url} è esaurito - avvisatemi quando torna disponibile."},
    "sq": {"order": "Përshëndetje, dua të porosis orën {name}{ref}, {price}. Nga {url}",
           "ask": "Përshëndetje, kam një pyetje për orën {name}{ref}, {price}. Nga {url}",
           "help": "Përshëndetje, nuk jam i sigurt cilën orë të zgjedh. Buxheti: . Është për: . Nga {url}",
           "notify": "Përshëndetje! Ora {name}{ref} në {url} është shitur - më njoftoni kur të kthehet ju lutem."},
}
NOTIFY_LABEL = {"en": "Tell me when it’s back", "it": "Avvisami quando torna",
                "sq": "Më njofto kur të kthehet"}
REF_WORD = {"en": "Ref.", "it": "Rif.", "sq": "Ref."}
HELP = {
    "en": ("Not sure which one? Tell us the budget and who it is for, and we will send "
           "two or three from what is in the shop.", "Ask on WhatsApp"),
    "it": ("Non sapete quale scegliere? Diteci il budget e per chi &egrave;, e ve ne "
           "mandiamo due o tre tra quelli in negozio.", "Chiedete su WhatsApp"),
    "sq": ("Nuk jeni t&euml; sigurt cil&euml;n t&euml; zgjidhni? Na thoni buxhetin dhe p&euml;r k&euml; "
           "&euml;sht&euml;, dhe ju d&euml;rgojm&euml; dy ose tre nga ato q&euml; kemi n&euml; dyqan.",
           "Pyesni n&euml; WhatsApp"),
}


def wa_url(kind, w, lang):
    """[DB-017.e] Build one WhatsApp deep link. Never emits a placeholder for a missing reference:
    the whole parenthetical is dropped instead."""
    name = f'{w["brand"]} {w["model"]}'.strip()
    ref = f' ({REF_WORD[lang]} {w["reference"]})' if w.get("reference") else ""
    price = ""
    if w.get("price"):
        eur = f'€{w["price"]}'
        l = lek(w["price"], w.get("currency", "EUR"))
        price = (f"{nfmt(l, lang)} L / {eur}" if lang == "sq" else f"{eur} / {nfmt(l, lang)} L") if l else eur
    url = f'watch.al/{lang}/shop/{w["id"]}.html'
    msg = WA[lang][kind].format(name=name, ref=ref, price=price, url=url)
    assert "—" not in msg
    return (f"https://api.whatsapp.com/send?phone={phone(lang)['wa']}&amp;text="
            + urllib.parse.quote(msg))


def rewrite_ambient_wa(html: str, w, lang: str) -> str:
    """[DB-017.f] The floating bubble and the header button opened an empty chat, on the one page
    type where the site knows exactly what the visitor is looking at. They now carry the
    watch, with question intent rather than order intent so the two stay distinguishable
    in the inbox."""
    url = wa_url("ask", w, lang)
    out, n1 = re.subn(r'(<a href=")[^"]*(" class="whatsapp-float")',
                      lambda m: m.group(1) + url + m.group(2), html, count=1)
    out, n2 = re.subn(r'(<a href=")[^"]*(" target="_blank" rel="noopener noreferrer" '
                      r'class="btn-primary wa-hdr")',
                      lambda m: m.group(1) + url + m.group(2), out, count=1)
    assert n1 == 1 and n2 == 1, f"ambient WhatsApp anchors not found ({n1},{n2})"
    out = out.replace('class="whatsapp-float" target="_blank" rel="noopener noreferrer" '
                      'data-fb-contact="1"',
                      'class="whatsapp-float" target="_blank" rel="noopener noreferrer" '
                      'data-fb-contact="pdp-float"')
    out = out.replace('class="btn-primary wa-hdr" data-fb-contact="1"',
                      'class="btn-primary wa-hdr" data-fb-contact="pdp-header"')
    return out


def build_help_html(w, lang):
    """[DB-017.g] delivery.html says in all three languages that "I do not know which one" is the
    most common message the shop gets. Until now the product page had no way to send it."""
    text, label = HELP[lang]
    return (f'<div class="pdp-help"><p>{text}</p>'
            f'<a href="{wa_url("help", w, lang)}" target="_blank" rel="noopener noreferrer" '
            f'data-fb-contact="pdp-help"><i class="fab fa-whatsapp" aria-hidden="true"></i> '
            f'{label}</a></div>')


# [DB-017.h] build_risk_html — the risk-reversal box under the buy button
def build_risk_html(lang):
    r = RISK[lang]
    pts = "".join(f'<span><i class="{i}" aria-hidden="true"></i>{t}</span>'
                  for i, t in r["points"])
    return (f'<div class="pdp-risk">{pts}'
            f'<a href="/{lang}/shop/delivery.html">{r["link"]}'
            f'<i class="fas fa-chevron-right" aria-hidden="true"></i></a></div>')


# [DB-017.i] build_maker_html — the "bought from the watchmaker" aftercare section
def build_maker_html(lang):
    m = MAKER[lang]
    return f'<section class="pdp-maker"><h2>{m["h"]}</h2><p>{m["p"]}</p></section>'


# [DB-017.j] build_rating_html — the Google 5.0 pill linking to the real reviews
def build_rating_html(lang):
    aria, label = GRATING[lang]
    return (f'<a class="pdp-rating" href="{REVIEWS_URL}" target="_blank" '
            f'rel="noopener noreferrer" aria-label="{aria}">'
            f'<span class="stars" aria-hidden="true">&#9733;&#9733;&#9733;&#9733;&#9733;</span>'
            f'<span>{label}</span></a>')


# Product-page styles. Same reasoning as EXTRA_CSS: page-local so shared.css, which is
# referenced by 475 files, never needs a cache-bust for a change to 171 of them.
#
# The mobile block exists to get the price, the buy button and the whole risk-reversal
# box above the fold on a 390x844 phone. The button used to start around y=909, i.e.
# below it, so the page asked people to decide before showing them anything reassuring.
# Note what is NOT here: a shorter image box. The image is object-fit:contain, so a
# shorter box makes the watch smaller, not the page tighter. Halving the padding makes
# the watch about a tenth larger and costs no height at all; the room comes from moving
# the description below the button and dropping the back-link the breadcrumb duplicates.
PDP_CSS = "<style id=\"pdp-css\">" + (
    ".pdp-idrow{display:flex;align-items:baseline;gap:.25rem .7rem;flex-wrap:wrap;margin:0 0 .15rem}"
    ".pdp-idrow .watch-ref-pg{margin:0}"
    ".pdp-swiss{font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;"
    "color:#8a9abf;font-weight:600}"
    ".pdp-pricerow{display:flex;align-items:baseline;justify-content:space-between;"
    "gap:.4rem .9rem;flex-wrap:wrap}"
    ".pdp-pricerow .watch-price-pg{margin:0}"
    ".pdp-rating{display:inline-flex;align-items:center;gap:.35rem;font-size:.74rem;"
    "white-space:nowrap;background:#f4f1ea;border:1px solid #e6e0d4;border-radius:9999px;"
    "padding:.18rem .6rem;color:#5a5a5a;text-decoration:none}"
    ".pdp-rating .stars{color:var(--accent-gold,#b4945c);letter-spacing:.5px}"
    ".pdp-rating:hover{border-color:var(--accent-gold,#b4945c)}"
    ".was-price-pg{font-size:.9rem;color:#aaa;text-decoration:line-through;margin:0}"
    ".sale-badge{position:absolute;top:1.15rem;right:-2.1rem;width:7.5rem;text-align:center;"
    "background:var(--btn-start,#06153b);color:var(--accent-gold,#b4945c);font-size:.62rem;"
    "font-weight:700;letter-spacing:.12em;padding:.32rem 0;transform:rotate(45deg);z-index:3;"
    "box-shadow:0 2px 8px rgba(0,0,0,.28)}"
    ".pdp-risk{background:#f7f5f0;border-left:3px solid var(--accent-gold,#b4945c);"
    "border-radius:0 .5rem .5rem 0;padding:.7rem .9rem;display:flex;flex-direction:column;"
    "gap:.4rem;font-size:.82rem;line-height:1.45;color:var(--text-secondary,#4a4a4a)}"
    ".pdp-risk span{display:flex;align-items:flex-start;gap:.5rem}"
    ".pdp-risk i{color:var(--accent-gold-accessible,#7a6240);font-size:.8rem;margin-top:.2em;"
    "flex:none;width:1em;text-align:center}"
    ".pdp-risk a{color:var(--accent-gold-accessible,#7a6240);text-decoration:underline;"
    "text-underline-offset:2px;font-weight:600;display:inline-flex;align-items:center;gap:.35rem}"
    ".pdp-risk a:hover{color:var(--accent-gold,#b4945c)}"
    ".pdp-maker{border-top:1px solid var(--border-light,#eaeaea);padding-top:1rem}"
    ".pdp-maker h2{font-size:1rem;margin:0 0 .4rem;color:var(--btn-start,#06153b)}"
    ".pdp-maker p{font-size:.86rem;line-height:1.6;color:var(--text-secondary,#4a4a4a);margin:0}"
    ".pdp-maker a{color:var(--accent-gold-accessible,#7a6240);text-decoration:underline;"
    "text-underline-offset:2px}"
    ".pdp-secondary{display:flex;align-items:center;gap:.5rem 1.25rem;flex-wrap:wrap;font-size:.82rem}"
    ".pdp-ig{display:inline-flex;align-items:center;gap:.4rem;"
    "color:var(--accent-gold-accessible,#7a6240);text-decoration:underline;text-underline-offset:2px}"
    ".pdp-ig:hover{color:var(--accent-gold,#b4945c)}"
    # shared.css never defined .md-flex, so the header phone icon was invisible at
    # every width on these pages.
    "@media(min-width:769px){.solid-header a.md-flex{display:inline-flex!important;"
    "align-items:center}}"
    "@media(max-width:768px){"
    ".watch-page{padding:.75rem 1rem 4rem;gap:1rem}"
    ".watch-img-wrap img{padding:1rem}"
    ".watch-info{gap:.85rem}"
    ".watch-info>.back-link{display:none}"
    ".watch-cta-main{width:100%;justify-content:center;font-size:1rem;padding:.85rem 1.5rem}"
    "}"
) + "</style>"


# [DB-017.k] replace_pdp_css — refresh the pdp-css style block, or install it once
def replace_pdp_css(html: str, new: str) -> str:
    if '<style id="pdp-css">' in html:
        out, n = re.subn(r'<style id="pdp-css">.*?</style>', lambda _: new, html,
                         count=1, flags=re.S)
    else:
        out, n = re.subn(r'(?=<div id="watch-crumb")', lambda _: new, html, count=1)
    assert n == 1, "pdp-css anchor not found"
    return out


def add_call_bar(html: str, lang: str) -> str:
    """[DB-017.l] The sticky phone bar exists on the homepage and the delivery page but never on
    a product page, though shared.css already styles it and pixel.js already lifts the
    consent banner 40px assuming it is there."""
    if 'class="call-bar"' in html:
        return html
    bar = (f'<div class="call-bar" role="complementary" aria-label="{CALL_BAR_ARIA[lang]}">'
           f'<a href="tel:{phone(lang)["tel"]}">'
           f'<i class="fas fa-phone-alt" aria-hidden="true"></i> '
           f'{phone(lang)["text"]}</a></div>')
    out, n = re.subn(r'(?=<a href="[^"]*" class="whatsapp-float")', lambda _: bar, html, count=1)
    assert n == 1, "whatsapp-float anchor not found for call bar"
    return out


# Styles for the sections below the product hero. Emitted inline with the block so the
# generator owns them end to end: putting them in shared.css would force a ?v= cache-bust
# on every page of the site.
EXTRA_CSS = (
    "<style>"
    ".watch-extra{max-width:80rem;margin:0 auto;padding:0 1.5rem 4rem;"
    "display:grid;grid-template-columns:1fr 1fr;gap:2.5rem;align-items:start}"
    ".watch-extra h2{font-size:1.35rem;margin:0 0 1rem}"
    ".watch-extra section{background:var(--card-bg,#fff);border:1px solid var(--border-light,#eaeaea);"
    "border-radius:1rem;padding:1.5rem}"
    ".watch-related{grid-column:1/-1}"
    ".spec-list{margin:0}"
    ".spec-row{display:flex;justify-content:space-between;gap:1rem;padding:.55rem 0;"
    "border-bottom:1px solid var(--border-light,#eaeaea)}"
    ".spec-row:last-child{border-bottom:0}"
    ".spec-row dt{color:var(--text-secondary,#4a4a4a);font-size:.88rem}"
    ".spec-row dd{margin:0;font-weight:600;text-align:right;font-size:.88rem}"
    ".buy-list{margin:0;padding:0;list-style:none;display:flex;flex-direction:column;gap:.6rem}"
    ".buy-list li{position:relative;padding-left:1.5rem;font-size:.9rem;"
    "color:var(--text-secondary,#4a4a4a);line-height:1.5}"
    ".buy-list li::before{content:'';position:absolute;left:0;top:.45em;width:.5rem;height:.5rem;"
    "border-radius:50%;background:var(--accent-gold,#b4945c)}"
    ".pdp-help{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;"
    "gap:1rem;flex-wrap:wrap;background:var(--btn-start,#06153b);border-radius:1rem;"
    "padding:1.1rem 1.5rem}"
    ".pdp-help p{margin:0;color:rgba(255,255,255,.85);font-size:.9rem;line-height:1.5;max-width:52ch}"
    ".pdp-help a{display:inline-flex;align-items:center;gap:.5rem;white-space:nowrap;"
    "background:var(--accent-gold,#b4945c);color:#18110a;font-weight:700;font-size:.85rem;"
    "border-radius:2rem;padding:.6rem 1.3rem;text-decoration:none}"
    ".pdp-help a:hover{background:#c9a86a}"
    "@media(max-width:600px){.pdp-help a{width:100%;justify-content:center}}"
    ".rel-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}"
    ".rel-card{display:flex;flex-direction:column;gap:.4rem;text-decoration:none;color:inherit;"
    "border:1px solid var(--border-light,#eaeaea);border-radius:.75rem;padding:.75rem;"
    "transition:border-color .2s,transform .2s}"
    ".rel-card:hover{border-color:var(--accent-gold,#b4945c);transform:translateY(-3px)}"
    ".rel-card img{width:100%;height:auto;border-radius:.5rem;background:#f7f5f0}"
    ".rel-role{font-size:.62rem;letter-spacing:.09em;text-transform:uppercase;font-weight:700;"
    "color:var(--accent-gold-accessible,#7a6240)}"
    ".rel-name{font-size:.82rem;font-weight:600;line-height:1.35}"
    ".rel-price{font-size:.82rem;color:var(--text-secondary,#4a4a4a)}"
    "@media(max-width:900px){.watch-extra{grid-template-columns:1fr;gap:1.5rem;padding:0 1rem 3rem}"
    ".rel-grid{grid-template-columns:repeat(2,1fr)}}"
    "</style>"
)


STEP_UP = 1.25    # what "a step up" has to mean to be worth showing
NEAR_BAND = 0.30  # a cross-brand alternative must be within this much of the price,
                  # so a 199 euro Hislon never advertises a 95 euro Navimarine

ROLE = {
    "en": {"same_brand": "Same brand", "same_price": "Same price",
           "step_up": "A step up", "top": "Top of the range"},
    "it": {"same_brand": "Stessa marca", "same_price": "Stesso prezzo",
           "step_up": "Un gradino sopra", "top": "Il top della gamma"},
    "sq": {"same_brand": "E nj&euml;jta mark&euml;", "same_price": "I nj&euml;jti &ccedil;mim",
           "step_up": "Nj&euml; shkall&euml; m&euml; lart", "top": "Maja e gam&euml;s"},
}


def related_for(w, n=4):
    """[DB-017.m] Four watches with four different jobs, read left to right as a price ladder.

    The old rule was "same brand, nearest price", which on a Navimarine page, and 22 of
    the 57 watches are Navimarines, showed four more Navimarines within five euro of
    each other. Nothing on any page ever pointed at the 149 to 199 end of the counter,
    so a shop with a top tier never once offered it.
    """
    others = [x for x in watches if x["id"] != w["id"] and not x.get("sold")]
    p = w.get("price") or 0
    picks, roles = [], []

    def take(cands, role):
        for x in cands:
            if all(x["id"] != y["id"] for y in picks):
                picks.append(x)
                roles.append(role)
                return

    near = lambda x: (abs((x.get("price") or 0) - p), x["id"])
    take(sorted([x for x in others if x["brand"] == w["brand"]], key=near), "same_brand")
    take(sorted([x for x in others if x["brand"] != w["brand"]
                 and abs((x.get("price") or 0) - p) <= NEAR_BAND * p], key=near), "same_price")
    take(sorted([x for x in others if (x.get("price") or 0) >= STEP_UP * p],
                key=lambda x: (x.get("price") or 0, x["id"])), "step_up")
    # Rotate the top-tier pick by a hash of the id, so 50-odd pages do not all send
    # everyone to the same watch, without depending on the order of watches.json.
    ceiling = max((x.get("price") or 0) for x in others)
    top = sorted([x for x in others if (x.get("price") or 0) >= 0.75 * ceiling],
                 key=lambda x: (-(x.get("price") or 0), x["id"]))
    if top:
        i = int(hashlib.md5(w["id"].encode()).hexdigest(), 16) % len(top)
        take([top[(i + k) % len(top)] for k in range(len(top))], "top")
    for x in sorted(others, key=near):  # fall-through, deliberately unlabelled
        if len(picks) >= n:
            break
        if all(x["id"] != y["id"] for y in picks):
            picks.append(x)
            roles.append("")

    out = sorted(zip(picks[:n], roles[:n]), key=lambda t: t[0].get("price") or 0)
    # A label must never lie: drop "top of the range" when the card is not dearer.
    return [(x, "" if r == "top" and (x.get("price") or 0) <= p else r) for x, r in out]


# [DB-017.n] build_specs_html — the Details definition list (empty values dropped)
# NOTES:  the nfmt(l, lang) call reads the MODULE-LEVEL loop variable `lang`, not a
#         parameter — correct only because this runs inside that loop; keep it so.
def build_specs_html(w, cfg):
    rows = [(cfg["spec_brand"], w.get("brand", ""))]
    if w.get("reference"):
        rows.append((cfg["spec_ref"], w["reference"]))
    rows.append((cfg["spec_cond"], w.get("condition", "")))
    price, currency = w.get("price"), w.get("currency", "EUR")
    if price:
        l = lek(price, currency)
        rows.append((cfg["spec_price"], f"€{price}" + (f" · {nfmt(l, lang)} L" if l else "")))
    if not w.get("sold"):
        rows.append((cfg["spec_avail"], cfg["avail_val"]))
    items = "".join(
        f'<div class="spec-row"><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows if v
    )
    return (f'<section class="watch-specs"><h2>{cfg["specs_h"]}</h2>'
            f'<dl class="spec-list">{items}</dl></section>')


def build_buy_html(cfg):
    """[DB-017.o] Renders delivery/returns/guarantee that until now existed only inside JSON-LD."""
    lis = "".join(f"<li>{t}</li>" for t in cfg["buy_items"])
    return (f'<section class="watch-buyinfo"><h2>{cfg["buy_h"]}</h2>'
            f'<ul class="buy-list">{lis}</ul></section>')


# [DB-017.p] build_related_html — the four related_for() picks as role-labelled cards
def build_related_html(w, lang, cfg):
    cards = []
    for r, role in related_for(w):
        price = r.get("price")
        l = lek(price, r.get("currency", "EUR")) if price else 0
        price_html = (f'<span class="rel-price">€{price}'
                      + (f' · {nfmt(l, lang)} L' if l else "") + "</span>") if price else ""
        img = r.get("image", "")
        img_html = (f'<img src="{re.sub(r".webp$", ".jpg", img, flags=re.I)}" alt="{r["brand"]} {r["model"]}"'
                    f' loading="lazy" width="300" height="300">') if img else ""
        role_html = (f'<span class="rel-role">{ROLE[lang][role]}</span>' if role else "")
        cards.append(
            f'<a class="rel-card" href="/{lang}/shop/{r["id"]}.html">{img_html}{role_html}'
            f'<span class="rel-name">{r["brand"]} {r["model"]}</span>{price_html}</a>'
        )
    return (f'<section class="watch-related"><h2>{cfg["related_h"]}</h2>'
            f'<div class="rel-grid">{"".join(cards)}</div></section>')


# [DB-017.q] build_watch_div — the whole #watch-content hero
# DOES:   image column + info column (identity row, price+rating row, CTA or the
#         sold/notify state, risk box, description, maker section, open-now + IG,
#         trust row) in the argument order the layout comment below explains.
def build_watch_div(w, lang, cfg):
    brand = w.get("brand", "")
    model = w.get("model", "")
    ref = w.get("reference", "")
    price = w.get("price")
    currency = w.get("currency", "EUR")
    sold = w.get("sold", False)
    desc = w.get(cfg["desc_key"]) or w.get("description_en", "")

    # WhatsApp URL
    wa_href = wa_url("order", w, lang)

    img_html = build_img_html(w, cfg)
    price_html = build_price_html(price, currency, lang)

    # Hislon's Swiss tag rides inline in the identity row rather than taking a line of
    # its own, so it costs no height above the fold.
    swiss_html = ""
    if brand in SWISS_BRANDS:
        swiss_html = f'<span class="pdp-swiss">{cfg["swiss_label"]}</span>'

    if sold:
        # [DB-003] statically-sold pages keep the notify capture. P128: they
        # now carry the EXACT contract stock-live.js toggles — the badge, the
        # real order CTA (CSS-hidden by .stock-oos) and the notify link marked
        # .stock-notify. Before this the sold page held ONLY a notify anchor,
        # so a restock could never un-flip it: the runtime layer removed the
        # class and revealed nothing, leaving one page saying "sold" while the
        # shop index across the site said it was for sale.
        cta_html = (
            f'<p class="stock-oos-badge">{cfg["sold_text"]}</p>'
            f'<div class="watch-cta-wrap">'
            f'<a href="{wa_href}" target="_blank" rel="noopener noreferrer" '
            f'class="watch-cta-main" data-fb-contact="pdp-cta">'
            f'<i class="fab fa-whatsapp" aria-hidden="true"></i> {cfg["cta_label"]}</a>'
            f'<a href="{wa_url("notify", w, lang)}" target="_blank" rel="noopener noreferrer" '
            f'class="watch-cta-main stock-notify" data-fb-contact="pdp-notify">'
            f'<i class="fab fa-whatsapp" aria-hidden="true"></i> {NOTIFY_LABEL[lang]}</a></div>'
        )
        risk_html = build_risk_html(lang)
    else:
        cta_html = (
            f'<div class="watch-cta-wrap">'
            f'<a href="{wa_href}" target="_blank" rel="noopener noreferrer" '
            f'class="watch-cta-main" data-fb-contact="pdp-cta">'
            f'<i class="fab fa-whatsapp" aria-hidden="true"></i> {cfg["cta_label"]}</a>'
            f"</div>"
        )
        risk_html = build_risk_html(lang)

    trust_html = '<div class="trust-row">' + "".join(cfg["trust"]) + "</div>"

    was_html = ""
    op = w.get("originalPrice")
    if op and price and op > price:
        was_html = f'<p class="was-price-pg">{cfg["was_label"]} &euro;{op}</p>'

    # Instagram moves out of the buy row. It was a saturated gradient pill sitting
    # beside the only button that earns money, which made the clearest exit from the
    # page compete with the one action worth taking.
    ig_html = (f'<a class="pdp-ig" href="https://instagram.com/iglisiwatch" target="_blank" '
               f'rel="noopener noreferrer">'
               f'<i class="fab fa-instagram" aria-hidden="true"></i> {cfg["ig_label"]}</a>')

    # Order is the argument: what it is, what it costs, how to get it, why it is safe
    # to, then the detail, then who is selling it.
    info_html = (
        f'<div class="watch-info">'
        f'<a href="{cfg["back_href"]}" class="back-link">'
        f'<i class="fas fa-arrow-left" aria-hidden="true"></i> {cfg["back_label"]}</a>'
        f"<div>"
        f'<p class="pdp-idrow"><span class="watch-brand-pg">{brand}</span>{swiss_html}'
        + (f'<span class="watch-ref-pg">{cfg["ref_label"]} {ref}</span>' if ref else "")
        + f"</p>"
        f'<h1 class="watch-title-pg">{brand} {model}</h1>'
        f"</div>"
        f'<div class="pdp-pricerow"><div>{was_html}'
        f'<p class="watch-price-pg">{price_html}</p></div>'
        f"{build_rating_html(lang)}</div>"
        f"{cta_html}"
        f"{risk_html}"
        f'<p class="watch-desc-pg">{desc}</p>'
        f"{build_maker_html(lang)}"
        f'<div class="pdp-secondary">' + open_now_html(lang) + ig_html + "</div>"
        f"{trust_html}"
        f"</div>"
    )

    # P128: `stock-oos` is the ONE class the runtime layer toggles. Rendering
    # it here means the static page and stock-live.js speak the same contract
    # in both directions: sold out on arrival, purchasable again the moment
    # the CRM says the shelf has one.
    return (
        f'<div id="watch-content" class="watch-page pre-rendered{" stock-oos" if sold else ""}">'
        f"{img_html}"
        f"{info_html}"
        f"</div>"
    )


def fix_footer_year(html: str) -> str:
    """[DB-017.r] #footerYear was filled by watch.js. shared.js fills [data-year] on every other
    page, so switch to that rather than keep a script alive for one number."""
    out, n = re.subn(r'<span id="footerYear"></span>', '<span data-year></span>', html)
    assert n <= 1
    return out


def strip_runtime_renderer(html: str) -> str:
    """[DB-017.s] Remove watch.js and the 63 KB watches-data.js it existed to feed.

    watch.js re-rendered #watch-content on every load, over static markup that was
    already correct, and every difference it introduced was damage: a NaN Lek price
    (render() ran before `var EUR_TO_LEK` was assigned), the sale price dropped,
    the open-now block deleted, an em dash where a reference was empty, and a
    toLocaleString() with no locale so an Albanian phone printed 6.800 L against
    Python's 6,800 L. Its reason to exist, the legacy shop/watch.html?id= template,
    is now a redirect stub that does not even load it.

    One renderer means the static and runtime versions of a page cannot disagree,
    which is the whole bug class.
    """
    out, n = re.subn(r'\n?<script src="[^"]*watches-data\.js[^"]*" defer></script>'
                     r'|\n?<script src="watch\.js" defer></script>', "", html)
    assert n in (0, 2), f"expected 0 or 2 script tags to strip, removed {n}"
    assert "watch.js" not in out and "watches-data.js" not in out
    return out


def pre_render_twitter(html: str, title: str, desc: str, w) -> str:
    """[DB-017.t] twitter:title/description/image were set only by watch.js, so every product
    link shared to a chat app rendered bare. Emit them next to twitter:card."""
    img = f'https://watch.al{w["image"]}'
    block = (f'<meta name="twitter:card" content="summary_large_image">\n'
             f'  <meta name="twitter:title" id="tw-title" content="{title}">\n'
             f'  <meta name="twitter:description" id="tw-desc" content="{desc}">\n'
             f'  <meta name="twitter:image" id="tw-image" content="{img}">')
    out, n = re.subn(r'<meta name="twitter:card" content="summary_large_image">'
                     r'(?:\n\s*<meta name="twitter:(?:title|description|image)"[^>]*>)*',
                     lambda _: block, html, count=1)
    assert n == 1, f"twitter:card block not found ({n})"
    return out


def rewrite_image_refs(html: str, w) -> str:
    """[DB-017.u] og:image and the Product JSON-LD image were written once by
    make-new-watch-pages.py and owned by nobody afterwards, while twitter:image
    above was regenerated every run. So an image RENAME propagated to the body
    picture and to twitter:image and left og:image and the schema pointing at a
    file that no longer exists: a 404 in every social preview, silently, because
    the page still rendered fine. Found when gen_sitemap refused to build after
    the 2026-08-17 hash rename. These two now regenerate with everything else."""
    img = f'https://watch.al{w["image"]}'
    out, n1 = re.subn(r'(<meta property="og:image" id="og-image" content=")[^"]*(">)',
                      lambda m: m.group(1) + img + m.group(2), html, count=1)
    out, n2 = re.subn(r'("image":")https://watch\.al/images/watches/[^"]*(")',
                      lambda m: m.group(1) + img + m.group(2), out, count=1)
    assert n1 == 1, f"og:image tag not found ({n1})"
    assert n2 == 1, f"product JSON-LD image not found ({n2})"
    return out



def build_biz_ld(lang):
    """[DB-017.v] The 5.0 rating as structured data, on a LocalBusiness node.

    Deliberately NOT aggregateRating inside the Product: these are reviews of a repair
    shop, not of a Navimarine NM181-03, and Google treats a business rating dressed up
    as a product rating as a policy violation. The @id is the one the shop index already
    uses, so this reads as the same business rather than 171 of them.
    """
    return ('<script type="application/ld+json" id="ld-biz">' + json.dumps({
        "@context": "https://schema.org", "@type": ["Store", "LocalBusiness"],
        "@id": "https://watch.al/#business", "name": "Iglisi Watch",
        "url": f"https://watch.al/{lang}/shop/", "telephone": phone(lang)["tel"],
        "email": "iglisi@watch.al", "image": "https://watch.al/og-image.png?v=2",
        "priceRange": "€€",
        "address": {"@type": "PostalAddress", "streetAddress": "Rruga Aleksander Goga",
                    "addressLocality": "Durrës", "postalCode": "2001",
                    "addressCountry": "AL"},
        # No aggregateRating here on purpose. The 5.0 rating is a real Google
        # Business Profile rating, but Google does not permit a business to mark up
        # ratings collected on a third-party platform as its own aggregateRating:
        # ineligible for rich results, manual-action risk. The visible badge linking
        # to the Google reviews page stays, and is honest.
    }, ensure_ascii=False, separators=(",", ":")) + "</script>")


# [DB-017.w] replace_biz_ld — refresh the ld-biz block, or install it before </head>
def replace_biz_ld(html: str, lang: str) -> str:
    new = build_biz_ld(lang)
    if 'id="ld-biz"' in html:
        out, n = re.subn(r'<script type="application/ld\+json" id="ld-biz">.*?</script>',
                         lambda _: new, html, count=1, flags=re.S)
    else:
        out, n = re.subn(r"(?=</head>)", lambda _: new + "\n", html, count=1)
    assert n == 1, "ld-biz anchor not found"
    return out


def build_crumb_div(w, lang):
    """[DB-017.x] Visible breadcrumb, placed ABOVE #watch-content as a sibling: watch.js
    replaces watch-content.innerHTML wholesale, so anything inside it is lost."""
    leaf = f'{w["brand"]} {w["model"]}'.strip()
    return (f'<div id="watch-crumb">{CRUMB_CSS}'
            + crumb_html(lang, brand=w.get("brand"), leaf=leaf) + "</div>")


def replace_crumb(html, new_div):
    """[DB-017.y] Replace #watch-crumb, else insert just before #watch-content."""
    m = re.search(r'<div id="watch-crumb">.*?</nav></div>', html, re.S)
    if m:
        return html[:m.start()] + new_div + html[m.end():]
    i = html.find('<div id="watch-content"')
    return html if i == -1 else html[:i] + new_div + "\n  " + html[i:]


def build_extra_div(w, lang, cfg):
    """[DB-017.z] Specs / delivery / related products.

    This lives as a SIBLING of #watch-content, never inside it: watch.js replaces
    watch-content.innerHTML wholesale at runtime, so anything nested there is destroyed
    for real users and for Google's rendered view.
    """
    return (
        f'<div id="watch-extra" class="watch-extra">'
        f"{EXTRA_CSS}"
        f"{build_specs_html(w, cfg)}"
        f"{build_buy_html(cfg)}"
        f"{build_help_html(w, lang)}"
        f"{build_related_html(w, lang, cfg)}"
        f"</div>"
    )


def replace_extra(html: str, new_div: str) -> str:
    """[DB-017.aa] Replace an existing #watch-extra, else insert it right before </main>."""
    m = re.search(r'<div id="watch-extra"[^>]*>', html)
    if m:
        start = m.start()
        pos, depth, end = m.end(), 1, m.end()
        while depth > 0 and pos < len(html):
            nxt_o, nxt_c = html.find("<div", pos), html.find("</div>", pos)
            if nxt_c == -1:
                break
            if nxt_o != -1 and nxt_o < nxt_c:
                depth += 1
                pos = nxt_o + 4
            else:
                depth -= 1
                end = nxt_c + 6
                pos = nxt_c + 6
        return html[:start] + new_div + html[end:]
    i = html.find("</main>")
    if i == -1:
        return html
    return html[:i] + new_div + "\n" + html[i:]


updated = []
skipped_missing = []
unchanged = []
stub_relink = []   # P128: un-retired watches whose page is still a redirect stub

# [DB-017] THE MODULE-LEVEL PAGE LOOP — runs on import, see the module docstring.
# DOES:   per watch x language: read the page preserving BOM/CRLF; deleted watches
#         become redirect stubs; live ones get hero + extra + crumb rebuilt, then
#         BreadcrumbList / title / og / description / Product-LD availability /
#         pdp-css / ambient WhatsApp / ld-biz / call bar / footer year / runtime
#         renderer strip / twitter metas — and the file is written only on change.
for w in watches:
    wid = w["id"]
    for lang, cfg in LANGS.items():
        path = BASE / lang / "shop" / f"{wid}.html"
        if not path.exists():
            skipped_missing.append(f"{lang}/shop/{wid}.html")
            continue

        raw = path.read_bytes()
        bom = raw.startswith(b"\xef\xbb\xbf")
        body = raw[3:] if bom else raw
        crlf = body.count(b"\r\n") == body.count(b"\n") and body.count(b"\n") > 0
        html = body.decode("utf-8").replace("\r\n", "\n")

        # P128: soft delete on the site was ONE-WAY. Retiring a watch replaces
        # its page with a 12-line noindex stub; clearing the flag then sent the
        # stub down the patching path, which needs #watch-content, #watch-extra
        # and </main> — none of which a stub has. The run died, so the whole
        # rebuild leg (and every other watch in it) stopped. Now the stub is
        # recognised, skipped loudly, and named with the command that restores
        # it — the Action stays green and the fix is one line away.
        if not w.get("deleted") and 'id="watch-content"' not in html:
            stub_relink.append(f"{lang}/shop/{wid}.html")
            print(f"  SKIP (stub, needs a full page): {lang}/shop/{wid}.html")
            continue

        if w.get("deleted"):
            stub = stub_html(w, lang)
            out = (b"\xef\xbb\xbf" if bom else b"") + (
                stub.replace("\n", "\r\n") if crlf else stub).encode("utf-8")
            if out == raw:
                unchanged.append(f"{lang}/shop/{wid}.html")
                print(f"  SKIP (stub, no change): {lang}/shop/{wid}.html")
            else:
                path.write_bytes(out)
                updated.append(f"{lang}/shop/{wid}.html")
                print(f"  STUB (deleted): {lang}/shop/{wid}.html")
            continue

        new_html = replace_watch_content(html, build_watch_div(w, lang, cfg))
        new_html = replace_extra(new_html, build_extra_div(w, lang, cfg))
        new_html = replace_crumb(new_html, build_crumb_div(w, lang))

        # BreadcrumbList must match the visible crumb AND what watch.js rebuilds
        bc = crumb_jsonld(lang, f'https://watch.al/{lang}/shop/{wid}.html',
                          brand=w.get('brand'), leaf=f'{w["brand"]} {w["model"]}'.strip())
        new_html = re.sub(r'(<script type="application/ld\+json" id="ld-breadcrumb">)(.*?)(</script>)',
                          lambda m: m.group(1) + json.dumps(bc, ensure_ascii=False) + m.group(3),
                          new_html, count=1, flags=re.S)

        # <title> + og:title, localized and commercial. Must equal what watch.js
        # rebuilds at runtime (see title_for), or static and rendered pages disagree.
        t = title_for(w, lang)
        new_html = re.sub(r'(<title id="page-title">)[^<]*(</title>)',
                          lambda m: m.group(1) + t + m.group(2), new_html, count=1)
        new_html = re.sub(r'(<meta property="og:title" id="og-title" content=")[^"]*(")',
                          lambda m: m.group(1) + t + m.group(2), new_html, count=1)

        # meta description + og:description + Product JSON-LD description. Same rule as the
        # title: these are pre-rendered for crawlers and watch.js overwrites them at runtime,
        # so the static value must equal the runtime one or the two disagree.
        raw_desc = (w.get(cfg["desc_key"]) or w.get("description_en", "")).strip()
        # The Swiss prefix NAMES THE BRAND, and it has to be the watch's own.
        # It was the literal "Swiss watch by Hislon." because Hislon was the only
        # Swiss brand when it was written. The moment Cortébert joined
        # SWISS_BRANDS (2026-08-25) every Cortébert page told crawlers and every
        # social preview that the watch was a Hislon: 9 pages, three languages,
        # wrong brand, and no gate could see it because the sentence was
        # perfectly well-formed.
        meta_desc = ((cfg["swiss_desc_prefix"].format(brand=w["brand"])
                      if w.get("brand") in SWISS_BRANDS else "")
                     + raw_desc + cfg["meta_tail"])
        assert '"' not in meta_desc and "&" not in meta_desc, f"{wid}: description needs escaping"
        new_html = re.sub(r'(<meta name="description" id="page-desc" content=")[^"]*(")',
                          lambda m: m.group(1) + meta_desc + m.group(2), new_html, count=1)
        new_html = re.sub(r'(<meta property="og:description" id="og-desc" content=")[^"]*(")',
                          lambda m: m.group(1) + meta_desc + m.group(2), new_html, count=1)

        def _set_ld_desc(m):
            ld = json.loads(m.group(2))
            ld["description"] = raw_desc
            # [DB-003] availability follows the CRM-driven sold flag — a sold
            # watch must tell crawlers OutOfStock, never evergreen InStock
            # A watch with no price ships a Product with NO Offer at all rather
            # than an Offer quoting 0, which would publish a false price in
            # structured data. schema.org does not require offers, and
            # verify-product-pages skips the price check when price is falsy.
            # Every PRICED watch must still carry one: an Offer that went
            # missing is how a sold watch would keep advertising InStock.
            if not w.get("price"):
                assert "offers" not in ld, f"{wid}: unpriced watch still has an Offer"
            else:
                assert isinstance(ld.get("offers"), dict), f"{wid}: Product LD without offers"
                off = ld["offers"]
                off["availability"] = ("https://schema.org/OutOfStock" if w.get("sold")
                                       else "https://schema.org/InStock")
                # PRICES ARE REWRITTEN EVERY RUN, not just at page creation.
                # They used to be written once by make-new-watch-pages.py and
                # then owned by nobody, so the 97 -> 92.25 rate change left the
                # ALL figure stale in the head JSON-LD of every existing page:
                # 192 audit findings, all of them "ALL price != N", on pages the
                # generator had just reported as updated. Deriving them here
                # means the next rate change heals itself.
                off["price"] = str(w["price"])
                off["priceCurrency"] = w.get("currency", "EUR")
                for spec in off.get("priceSpecification", []):
                    if spec.get("priceCurrency") == "ALL":
                        spec["price"] = str(lek(w["price"], w.get("currency", "EUR")))
                    elif spec.get("priceCurrency") == "EUR":
                        spec["price"] = str(w["price"])
            return m.group(1) + json.dumps(ld, ensure_ascii=False, separators=(",", ":")) + m.group(3)

        new_html = re.sub(r'(<script type="application/ld\+json" id="ld-json">)(.*?)(</script>)',
                          _set_ld_desc, new_html, count=1, flags=re.S)

        new_html = replace_pdp_css(new_html, PDP_CSS)
        new_html = rewrite_ambient_wa(new_html, w, lang)
        new_html = replace_biz_ld(new_html, lang)
        new_html = add_call_bar(new_html, lang)
        new_html = fix_footer_year(new_html)
        new_html = strip_runtime_renderer(new_html)
        new_html = pre_render_twitter(new_html, t, meta_desc, w)
        new_html = rewrite_image_refs(new_html, w)

        out = (b"\xef\xbb\xbf" if bom else b"") + (
            new_html.replace("\n", "\r\n") if crlf else new_html).encode("utf-8")
        assert b"\x0c" not in out
        if out == raw:
            unchanged.append(f"{lang}/shop/{wid}.html")
            print(f"  SKIP (no change): {lang}/shop/{wid}.html")
        else:
            path.write_bytes(out)
            updated.append(f"{lang}/shop/{wid}.html")
            print(f"  OK: {lang}/shop/{wid}.html")

print(f"\nDone. Updated: {len(updated)}  |  Unchanged: {len(unchanged)}  |  Missing: {len(skipped_missing)}")
if skipped_missing:
    print("Missing:", skipped_missing)
if stub_relink:
    print(f"\nNOTE: {len(stub_relink)} page(s) are still redirect stubs for watches that are no longer "
          f"retired. The catalogue lists them again, but their pages bounce to the shop index.")
    print("Rebuild those shells, then rerun this generator:")
    print("    python ../scripts/make-new-watch-pages.py")
    for s in stub_relink:
        print("   -", s)
