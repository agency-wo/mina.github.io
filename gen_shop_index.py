#!/usr/bin/env python3
"""
gen_shop_index.py
Pre-renders the shop grid into {en,it,sq}/shop/index.html so crawlers and non-JS
visitors see every product card and link. Before this the grid was six skeleton
divs hydrated by a cross-origin fetch, so the shop hub exposed ZERO product links.
Also regenerates the static ItemList JSON-LD from watches.json.

Card markup mirrors shop.js watchCard() exactly, so runtime hydration is a visual
no-op. RERUN AFTER ANY CATALOG CHANGE (add/remove/reprice a watch).

Run from the repo:  python gen_shop_index.py
Idempotent.
"""
import json
import re
from pathlib import Path
from urllib.parse import quote

BASE = Path(__file__).parent
BOM = b"\xef\xbb\xbf"
W = json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))

L = {
 "en": dict(sold="Sold", cta="Enquire", ig="See on Instagram", ref="Ref.",
            cta_aria="Enquire about {n} via WhatsApp",
            wa="Hi\u2019s", was="Was ",
            msg="Hi, I\u2019m interested in the {b} {m} (Ref. {r}) listed on your website."),
 "it": dict(sold="Venduto", cta="Richiedi", ig="Vedi su Instagram", ref="Rif.",
            cta_aria="Richiedi info su {n} via WhatsApp", was="Prima ",
            msg="Salve, sono interessato all'orologio {b} {m} (Rif. {r}) sul vostro sito."),
 "sq": dict(sold="Shitur", cta="Pyesni", ig="Shiko n\u00eb Instagram", ref="Ref.",
            cta_aria="Pyesni per {n} ne WhatsApp", was="M\u00eb par\u00eb ",
            msg="Pershendetje, jam i interesuar per oren {b} {m} (Ref. {r}) ne faqen tuaj."),
}


def lek(price, currency):
    if not price or currency != "EUR":
        return ""
    v = int(price * 97 / 100 + 0.5) * 100
    return ('<span style="font-size:.78rem;color:#888;font-weight:400"> \u00b7 '
            + f"{v:,}" + "\u00a0L</span>")


def card(w, lang):
    t = L[lang]
    swiss = " Swiss Watch" if w["brand"] == "Hislon" else ""
    name = f'{w["brand"]} {w["model"]}'
    alt = name + swiss
    webp = re.sub(r"\.jpe?g$", ".webp", w["image"], flags=re.I)
    img = (f'<a href="/{lang}/shop/{w["id"]}.html" aria-label="{alt}"><picture>'
           f'<source srcset="{webp}" type="image/webp">'
           f'<img src="{w["image"]}" alt="{alt}" loading="lazy"></picture></a>') if w.get("image") else \
          '<div class="watch-img-placeholder"><i class="fas fa-clock" aria-hidden="true"></i></div>'
    sold_ov = f'<div class="sold-overlay">{t["sold"]}</div>' if w.get("sold") else ""
    if w.get("sold"):
        cta = f'<span style="font-size:.82rem;color:#888">{t["sold"]}</span>'
    else:
        msg = t["msg"].format(b=w["brand"], m=w["model"], r=w.get("reference") or "N/A")
        url = "https://api.whatsapp.com/send?phone=355676360510&text=" + quote(msg, safe="")
        cta = (f'<a href="{url}" target="_blank" rel="noopener noreferrer" class="watch-cta" '
               f'data-fb-contact="1" aria-label="{t["cta_aria"].format(n=name)}">'
               f'<i class="fab fa-whatsapp" aria-hidden="true"></i> {t["cta"]}</a>')
    swiss_tag = ('<span style="font-size:.65rem;letter-spacing:.08em;text-transform:uppercase;'
                 'color:#8a9abf;font-weight:500;margin-left:.4rem;vertical-align:middle">Swiss</span>'
                 ) if w["brand"] == "Hislon" else ""
    sale = '<span class="sale-badge">\u221210%</span>' if w.get("originalPrice") else ""
    was = (f'<p class="was-price-line">{t["was"]}\u20ac{w["originalPrice"]}</p>'
           if w.get("originalPrice") else "")
    price = ("\u20ac" if w.get("currency") == "EUR" else str(w.get("currency", ""))) + f'{w["price"]:,}'
    sold_cls = " sold-card" if w.get("sold") else ""
    desc = w[f"description_{lang}"]
    ref_line = f'<p class="watch-ref">{t["ref"]} {w["reference"]}</p>' if w.get("reference") else ""
    parts = [
        f'<article class="watch-card{sold_cls}">',
        f'<div class="watch-card-img">{img}{sold_ov}',
        f'<span class="watch-badge">{w["condition"]}</span>{sale}</div>',
        '<div class="watch-card-body">',
        f'<p class="watch-brand">{w["brand"]}{swiss_tag}</p>',
        f'<h2 class="watch-model">{w["model"]}</h2>',
        ref_line,
        f'<p class="watch-desc">{desc}</p>',
        '<div class="watch-card-footer"><div>',
        f'<p class="watch-price">{price}{lek(w["price"], w.get("currency"))}</p>{was}</div>',
        '<a href="https://instagram.com/iglisiwatch" target="_blank" rel="noopener noreferrer" '
        f'class="watch-ig-link" aria-label="{t["ig"]}">'
        '<i class="fab fa-instagram" aria-hidden="true"></i></a>',
        cta,
        '</div></div></article>',
    ]
    return "".join(parts)


def itemlist(lang, old):
    items = []
    for i, w in enumerate([x for x in W if not x.get("sold")], 1):
        items.append({
            "@type": "ListItem", "position": i,
            "item": {
                "@type": "Product",
                "name": f'{w["brand"]} {w["model"]}' + (" Swiss Watch" if w["brand"] == "Hislon" else ""),
                "sku": w.get("reference", ""),
                "description": w[f"description_{lang}"],
                "brand": {"@type": "Brand", "name": w["brand"]},
                "image": "https://watch.al" + re.sub(r"\.jpe?g$", ".webp", w["image"], flags=re.I),
                "offers": {
                    "@type": "Offer", "priceCurrency": w.get("currency", "EUR"),
                    "price": str(w["price"]),
                    "availability": "https://schema.org/InStock",
                    "priceValidUntil": "2026-12-31",
                    "itemCondition": "https://schema.org/NewCondition",
                    "seller": {"@type": "Organization", "name": "Iglisi Watch"},
                    "url": f'https://watch.al/{lang}/shop/{w["id"]}.html',
                },
            },
        })
    new = dict(old)
    new["numberOfItems"] = len(items)
    new["itemListElement"] = items
    return new


SCRIPT_RE = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S)
GRID_RE = re.compile(r'(<div class="shop-grid" id="shopGrid"[^>]*>)(.*?)(\n    </div>)', re.S)

def main():
    for lang in ("en", "it", "sq"):
        f = BASE / lang / "shop" / "index.html"
        raw = f.read_bytes()
        bom = raw.startswith(BOM)
        text = raw[len(BOM):].decode("utf-8") if bom else raw.decode("utf-8")
        eol = "\r\n" if "\r\n" in text else "\n"
        norm = text.replace("\r\n", "\n")
    
        # 1. pre-render the grid (replace skeleton, or refresh a previous pre-render)
        m = GRID_RE.search(norm)
        assert m, f"{lang}: shopGrid block not found"
        cards = "\n      " + "\n      ".join(card(w, lang) for w in W) + "\n    "
        norm = norm[:m.start(2)] + cards + norm[m.end(2):]
    
        # 2. regenerate the static ItemList JSON-LD from watches.json
        done = False
        for s in SCRIPT_RE.finditer(norm):
            body = s.group(1)
            if not body.strip():
                continue
            d = json.loads(body)
            if isinstance(d, dict) and d.get("@type") == "ItemList":
                payload = json.dumps(itemlist(lang, d), indent=2, ensure_ascii=False)
                payload = "\n  " + payload.replace("\n", "\n  ") + "\n  "
                norm = norm[:s.start(1)] + payload + norm[s.end(1):]
                done = True
                break
        assert done, f"{lang}: ItemList not found"
    
        out = norm.replace("\n", eol) if eol == "\r\n" else norm
        f.write_bytes((BOM if bom else b"") + out.encode("utf-8"))
    
        # sanity
        chk = f.read_text(encoding="utf-8-sig")
        for b in SCRIPT_RE.findall(chk):
            if b.strip():
                json.loads(b)
        n_cards = chk.count('<article class="watch-card')
        n_links = len(set(re.findall(rf'href="/{lang}/shop/([a-z0-9.-]+)\.html"', chk)))
        il = [json.loads(b) for b in SCRIPT_RE.findall(chk) if b.strip() and '"ItemList"' in b][0]
        assert n_cards == len(W), f"{lang}: {n_cards} cards != {len(W)}"
        assert n_links == len(W), f"{lang}: {n_links} distinct product links"
        assert il["numberOfItems"] == len(il["itemListElement"]) == len(W), f"{lang}: ItemList count"
        assert "\u2014" not in chk.split("</head>")[1].replace('watch-ref">Ref. \u2014', ""), f"{lang}: em dash"
        print(f"{lang}/shop/index.html: {n_cards} cards, {n_links} product links, ItemList {il['numberOfItems']}")
    


if __name__ == "__main__":
    main()
    print("SHOP GRID PRE-RENDERED")
