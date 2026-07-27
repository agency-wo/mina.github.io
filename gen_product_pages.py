#!/usr/bin/env python3
"""
gen_product_pages.py
Pre-renders product page body content (H1, price, description, CTA, trust row)
into static HTML so AI crawlers and non-JS environments see real content.

watch.js continues to run for real users (progressive enhancement):
it overwrites #watch-content at runtime, so there is no functional change
for browsers — only crawlers and view-source benefit.

Run from repo root:  python gen_product_pages.py
Idempotent: safe to run multiple times.
"""
import json
import re
import urllib.parse
from pathlib import Path

BASE = Path(__file__).parent

watches = json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))

LEK_RATE = 97

# brand+model is not unique for the Hislon Classic / Classic Queen families, so those
# titles get the reference appended to stay distinct.
DUP_NAMES = {}
for _w in watches:
    _n = f'{_w["brand"]} {_w["model"]}'.strip()
    DUP_NAMES[_n] = DUP_NAMES.get(_n, 0) + 1

LANGS = {
    "en": {
        "desc_key": "description_en",
        "back_href": "/en/shop/",
        "back_label": "Back to shop",
        "ref_label": "Ref.",
        "sold_text": "This watch has been sold.",
        "cta_label": "Enquire via WhatsApp",
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
        "wa_msg": (
            "Hi, I’m interested in the {brand} {model}"
            " (Ref. {ref}) - can you confirm if it’s still available?"
        ),
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
        "related_h": "Other watches you may like",
    },
    "it": {
        "desc_key": "description_it",
        "back_href": "/it/shop/",
        "back_label": "Torna al negozio",
        "ref_label": "Rif.",
        "sold_text": "Questo orologio è stato venduto.",
        "cta_label": "Richiedi via WhatsApp",
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
        "wa_msg": (
            "Salve, sono interessato all’orologio {brand} {model}"
            " (Rif. {ref}) - potete confermare se è ancora disponibile?"
        ),
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
        "related_h": "Altri orologi che potrebbero piacerti",
    },
    "sq": {
        "desc_key": "description_sq",
        "back_href": "/sq/shop/",
        "back_label": "Kthehu në dyqan",
        "ref_label": "Ref.",
        "sold_text": "Kjo orë është shëtur.",
        "cta_label": "Pyesni në WhatsApp",
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
        "wa_msg": (
            "Pershendetje, jam i interesuar per oren {brand} {model}"
            " (Ref. {ref}) - a mund te konfirmoni nese është ende e disponueshme?"
        ),
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
        "related_h": "Orë të tjera që mund t’ju pëlqejnë",
    },
}


def title_for(w, lang):
    """Product <title>. MUST stay byte-identical to the string watch.js builds at runtime.
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
    """Replace <div id="watch-content"...>...</div> with new_div.
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


def lek(price, currency):
    if not price or currency != "EUR":
        return 0
    # half-up to match Math.round in shop/watch.js (Python round() is banker's: 48.5 -> 48)
    return int(price * LEK_RATE / 100 + 0.5) * 100


def build_price_html(price, currency):
    if not price:
        return "Price on request"
    eur = f"€{price}"
    l = lek(price, currency)
    if l:
        eur += (
            f'<span style="font-size:1.1rem;color:#888;font-weight:500;margin-left:.5rem">'
            f"· {l:,} L</span>"
        )
    return eur


def build_img_html(w):
    image = w.get("image", "")
    if not image:
        return ""
    webp = image
    jpg = re.sub(r"\.webp$", ".jpg", image, flags=re.IGNORECASE)
    alt = f'{w["brand"]} {w["model"]}'
    sold = w.get("sold", False)
    badge = "Sold" if sold else w.get("condition", "New")
    return (
        f'<div class="watch-img-wrap">'
        f"<picture>"
        f'<source srcset="{webp}" type="image/webp">'
        f'<img src="{jpg}" alt="{alt}" fetchpriority="high" loading="eager">'
        f"</picture>"
        f'<span class="watch-badge-pg">{badge}</span>'
        f"</div>"
    )


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
    ".rel-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:1rem}"
    ".rel-card{display:flex;flex-direction:column;gap:.4rem;text-decoration:none;color:inherit;"
    "border:1px solid var(--border-light,#eaeaea);border-radius:.75rem;padding:.75rem;"
    "transition:border-color .2s,transform .2s}"
    ".rel-card:hover{border-color:var(--accent-gold,#b4945c);transform:translateY(-3px)}"
    ".rel-card img{width:100%;height:auto;border-radius:.5rem;background:#f7f5f0}"
    ".rel-name{font-size:.82rem;font-weight:600;line-height:1.35}"
    ".rel-price{font-size:.82rem;color:var(--text-secondary,#4a4a4a)}"
    "@media(max-width:900px){.watch-extra{grid-template-columns:1fr;gap:1.5rem;padding:0 1rem 3rem}"
    ".rel-grid{grid-template-columns:repeat(2,1fr)}}"
    "</style>"
)


def related_for(w, n=4):
    """Same brand first, then nearest price. Gives every product page real internal
    links and is the one part of the added markup that is unique per page."""
    others = [x for x in watches if x["id"] != w["id"] and not x.get("sold")]
    price = w.get("price") or 0
    same = [x for x in others if x["brand"] == w["brand"]]
    same.sort(key=lambda x: abs((x.get("price") or 0) - price))
    rest = [x for x in others if x["brand"] != w["brand"]]
    rest.sort(key=lambda x: abs((x.get("price") or 0) - price))
    return (same + rest)[:n]


def build_specs_html(w, cfg):
    rows = [(cfg["spec_brand"], w.get("brand", ""))]
    if w.get("reference"):
        rows.append((cfg["spec_ref"], w["reference"]))
    rows.append((cfg["spec_cond"], w.get("condition", "")))
    price, currency = w.get("price"), w.get("currency", "EUR")
    if price:
        l = lek(price, currency)
        rows.append((cfg["spec_price"], f"€{price}" + (f" · {l:,} L" if l else "")))
    if not w.get("sold"):
        rows.append((cfg["spec_avail"], cfg["avail_val"]))
    items = "".join(
        f'<div class="spec-row"><dt>{k}</dt><dd>{v}</dd></div>' for k, v in rows if v
    )
    return (f'<section class="watch-specs"><h2>{cfg["specs_h"]}</h2>'
            f'<dl class="spec-list">{items}</dl></section>')


def build_buy_html(cfg):
    """Renders delivery/returns/guarantee that until now existed only inside JSON-LD."""
    lis = "".join(f"<li>{t}</li>" for t in cfg["buy_items"])
    return (f'<section class="watch-buyinfo"><h2>{cfg["buy_h"]}</h2>'
            f'<ul class="buy-list">{lis}</ul></section>')


def build_related_html(w, lang, cfg):
    cards = []
    for r in related_for(w):
        price = r.get("price")
        l = lek(price, r.get("currency", "EUR")) if price else 0
        price_html = (f'<span class="rel-price">€{price}'
                      + (f' · {l:,} L' if l else "") + "</span>") if price else ""
        img = r.get("image", "")
        img_html = (f'<img src="{re.sub(r".webp$", ".jpg", img, flags=re.I)}" alt="{r["brand"]} {r["model"]}"'
                    f' loading="lazy" width="300" height="300">') if img else ""
        cards.append(
            f'<a class="rel-card" href="/{lang}/shop/{r["id"]}.html">{img_html}'
            f'<span class="rel-name">{r["brand"]} {r["model"]}</span>{price_html}</a>'
        )
    return (f'<section class="watch-related"><h2>{cfg["related_h"]}</h2>'
            f'<div class="rel-grid">{"".join(cards)}</div></section>')


def build_watch_div(w, lang, cfg):
    brand = w.get("brand", "")
    model = w.get("model", "")
    ref = w.get("reference", "")
    price = w.get("price")
    currency = w.get("currency", "EUR")
    sold = w.get("sold", False)
    desc = w.get(cfg["desc_key"]) or w.get("description_en", "")

    # WhatsApp URL
    wa_text = cfg["wa_msg"].format(brand=brand, model=model, ref=ref or "N/A")
    wa_url = (
        "https://api.whatsapp.com/send?phone=355676360510&amp;text="
        + urllib.parse.quote(wa_text)
    )

    img_html = build_img_html(w)
    price_html = build_price_html(price, currency)

    swiss_html = ""
    if brand == "Hislon":
        swiss_html = (
            f'<p style="font-size:.72rem;letter-spacing:.1em;text-transform:uppercase;'
            f'color:#8a9abf;font-weight:600;margin:0 0 .3rem">{cfg["swiss_label"]}</p>'
        )

    if sold:
        cta_html = (
            f'<p style="font-size:1rem;color:#888;font-weight:600">{cfg["sold_text"]}</p>'
        )
    else:
        cta_html = (
            f'<div class="watch-cta-wrap">'
            f'<a href="{wa_url}" target="_blank" rel="noopener noreferrer" '
            f'class="watch-cta-main" data-fb-contact="1">'
            f'<i class="fab fa-whatsapp" aria-hidden="true"></i> {cfg["cta_label"]}</a>'
            f'<a href="https://instagram.com/iglisiwatch" target="_blank" '
            f'rel="noopener noreferrer" class="watch-ig">'
            f'<i class="fab fa-instagram" aria-hidden="true"></i> {cfg["ig_label"]}</a>'
            f"</div>"
        )

    trust_html = (
        '<div class="trust-row">'
        + "".join(cfg["trust"])
        + "</div>"
    )

    info_html = (
        f'<div class="watch-info">'
        f'<a href="{cfg["back_href"]}" class="back-link">'
        f'<i class="fas fa-arrow-left" aria-hidden="true"></i> {cfg["back_label"]}</a>'
        f"<div>"
        f'<p class="watch-brand-pg">{brand}</p>'
        f"{swiss_html}"
        f'<h1 class="watch-title-pg">{brand} {model}</h1>'
        + (f'<p class="watch-ref-pg">{cfg["ref_label"]} {ref}</p>' if ref else "")
        + f"</div>"
        f'<p class="watch-price-pg">{price_html}</p>'
        f'<p class="watch-desc-pg">{desc}</p>'
        f"{cta_html}"
        f"{trust_html}"
        f"</div>"
    )

    return (
        f'<div id="watch-content" class="watch-page pre-rendered">'
        f"{img_html}"
        f"{info_html}"
        f"</div>"
    )


def build_extra_div(w, lang, cfg):
    """Specs / delivery / related products.

    This lives as a SIBLING of #watch-content, never inside it: watch.js replaces
    watch-content.innerHTML wholesale at runtime, so anything nested there is destroyed
    for real users and for Google's rendered view.
    """
    return (
        f'<div id="watch-extra" class="watch-extra">'
        f"{EXTRA_CSS}"
        f"{build_specs_html(w, cfg)}"
        f"{build_buy_html(cfg)}"
        f"{build_related_html(w, lang, cfg)}"
        f"</div>"
    )


def replace_extra(html: str, new_div: str) -> str:
    """Replace an existing #watch-extra, else insert it right before </main>."""
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

for w in watches:
    wid = w["id"]
    for lang, cfg in LANGS.items():
        path = BASE / lang / "shop" / f"{wid}.html"
        if not path.exists():
            skipped_missing.append(f"{lang}/shop/{wid}.html")
            continue

        html = path.read_text(encoding="utf-8")
        new_html = replace_watch_content(html, build_watch_div(w, lang, cfg))
        new_html = replace_extra(new_html, build_extra_div(w, lang, cfg))

        # <title> + og:title, localized and commercial. Must equal what watch.js
        # rebuilds at runtime (see title_for), or static and rendered pages disagree.
        t = title_for(w, lang)
        new_html = re.sub(r'(<title id="page-title">)[^<]*(</title>)',
                          lambda m: m.group(1) + t + m.group(2), new_html, count=1)
        new_html = re.sub(r'(<meta property="og:title" id="og-title" content=")[^"]*(")',
                          lambda m: m.group(1) + t + m.group(2), new_html, count=1)

        if new_html == html:
            unchanged.append(f"{lang}/shop/{wid}.html")
            print(f"  SKIP (no change): {lang}/shop/{wid}.html")
        else:
            path.write_text(new_html, encoding="utf-8")
            updated.append(f"{lang}/shop/{wid}.html")
            print(f"  OK: {lang}/shop/{wid}.html")

print(f"\nDone. Updated: {len(updated)}  |  Unchanged: {len(unchanged)}  |  Missing: {len(skipped_missing)}")
if skipped_missing:
    print("Missing:", skipped_missing)
