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

import catalog_stats
from shop_bits import (card_price_html, crumb_html, CRUMB_CSS,
                       delivery_bar_html, DELIVERY_CSS)
from shop_seo import COPY as SEO_COPY, fill as seo_fill, seo_section_html, faq_jsonld

BASE = Path(__file__).parent
BOM = b"\xef\xbb\xbf"
# [DB-006] deleted ≠ sold (P125 W4): a SOLD watch stays fully visible with its
# badge; a DELETED (retired) entry leaves the grid, the ItemList and the brand
# pages entirely — its product page becomes a redirect stub. Data stays in
# watches.json forever; clearing the flag brings everything back.
W = [w for w in json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))
     if not w.get("deleted")]
S = catalog_stats.load()

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


_SIZES = {}


def img_size(rel):
    """Intrinsic dimensions for the card <img>. The container already sets
    aspect-ratio:1/1 so this is correctness rather than a layout-shift fix."""
    if not rel:
        return (0, 0)
    if rel not in _SIZES:
        try:
            from PIL import Image
            with Image.open(BASE / rel.lstrip("/")) as im:
                _SIZES[rel] = im.size
        except Exception:
            _SIZES[rel] = (0, 0)
    return _SIZES[rel]


def card(w, lang):
    t = L[lang]
    swiss = " Swiss Watch" if w["brand"] == "Hislon" else ""
    name = f'{w["brand"]} {w["model"]}'
    alt = name + swiss
    webp = re.sub(r"\.jpe?g$", ".webp", w["image"], flags=re.I)
    iw, ih = img_size(w.get("image", ""))
    dims = f' width="{iw}" height="{ih}"' if iw else ""
    img = (f'<a href="/{lang}/shop/{w["id"]}.html" aria-label="{alt}"><picture>'
           f'<source srcset="{webp}" type="image/webp">'
           f'<img src="{w["image"]}" alt="{alt}" loading="lazy"{dims}></picture></a>') if w.get("image") else \
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
    # SQ leads with Lek; mirrored by shop.js. Single definition in shop_bits.
    price = card_price_html(w["price"], w.get("currency"), lang)
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
        f'<p class="watch-price">{price}</p>{was}</div>',
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

        # 3. visible Home > Shop crumb, placed on the LIGHT content area just above the
        #    filter controls. It must NOT go above the hero: a pale band between the dark
        #    sticky header and the dark hero cuts the top of the page in half.
        #    Directly under it sits the delivery bar: free delivery, pay on arrival,
        #    30 days to return, linking to shop/delivery.html. It answers the three
        #    objections a buyer outside Durres has before they will open a card.
        norm = re.sub(r'<style>\.shop-crumb.*?</nav>', "", norm, flags=re.S)   # drop any old copy
        norm = re.sub(r'<nav class="shop-crumb".*?</nav>', "", norm, flags=re.S)
        norm = re.sub(r'<style>\.shop-deliv.*?</style>', "", norm, flags=re.S)
        norm = re.sub(r'<div class="shop-deliv">.*?</div></div>', "", norm, flags=re.S)
        anchor = '<div class="shop-controls">'
        assert norm.count(anchor) == 1, f"{lang}: shop-controls anchor x{norm.count(anchor)}"
        norm = norm.replace(anchor, CRUMB_CSS + crumb_html(lang)
                            + DELIVERY_CSS + delivery_bar_html(lang) + anchor, 1)

        # 4. below-grid geo lead + FAQ section, just before </main>
        sec = seo_section_html(lang, W)
        old_sec = re.search(r'<section id="shop-seo".*?</section>', norm, re.S)
        if old_sec:
            norm = norm[:old_sec.start()] + sec + norm[old_sec.end():]
        else:
            i = norm.index("</main>")
            norm = norm[:i] + sec + "\n  " + norm[i:]

        # 5. FAQPage JSON-LD matching the visible FAQ byte for byte
        faq_tag = ('<script type="application/ld+json" id="ld-shop-faq">'
                   + json.dumps(faq_jsonld(lang, W), ensure_ascii=False) + "</script>")
        old_faq = re.search(r'<script type="application/ld\+json" id="ld-shop-faq">.*?</script>', norm, re.S)
        if old_faq:
            norm = norm[:old_faq.start()] + faq_tag + norm[old_faq.end():]
        else:
            i = norm.index("</head>")
            norm = norm[:i] + faq_tag + "\n" + norm[i:]

        # 6. meta + og description with the COD/Tirana hooks (titles untouched)
        desc = seo_fill(SEO_COPY[lang]["desc"], W, lang)
        norm = re.sub(r'(<meta name="description" content=")[^"]*(")',
                      lambda m: m.group(1) + desc + m.group(2), norm, count=1)
        norm = re.sub(r'(<meta property="og:description" content=")[^"]*(")',
                      lambda m: m.group(1) + desc + m.group(2), norm, count=1)

        # 7. refresh the stale schema descriptions from live data.
        #    Replacements change block lengths, so matches are applied in REVERSE
        #    document order: earlier spans stay valid while later ones are rewritten.
        for s in reversed(list(SCRIPT_RE.finditer(norm))):
            body = s.group(1)
            if not body.strip():
                continue
            d = json.loads(body)
            changed = False
            if isinstance(d, dict) and "@graph" in d:
                for node in d["@graph"]:
                    ts = node.get("@type")
                    if ts == "LocalBusiness" or (isinstance(ts, list) and "LocalBusiness" in ts):
                        node["description"] = seo_fill(SEO_COPY[lang]["biz_desc"], W, lang)
                        changed = True
                # the @graph carried a FAQPage whose 8 questions were never visible on the
                # page (Google requires FAQ content to be visible) and which would duplicate
                # the visible ld-shop-faq block. Drop it; ld-shop-faq is the only FAQPage.
                pruned = [n for n in d["@graph"] if n.get("@type") != "FAQPage"]
                if len(pruned) != len(d["@graph"]):
                    d["@graph"] = pruned
                    changed = True
            elif isinstance(d, dict) and d.get("@type") == "CollectionPage":
                d["description"] = seo_fill(SEO_COPY[lang]["coll_desc"], W, lang)
                changed = True
            if changed:
                payload = json.dumps(d, indent=2, ensure_ascii=False)
                payload = "\n  " + payload.replace("\n", "\n  ") + "\n  "
                norm = norm[:s.start(1)] + payload + norm[s.end(1):]

        # 8. drop the empty shop-ld-list tag: the static ItemList above is the single
        #    source of truth now (shop.js no longer injects a runtime duplicate)
        norm = re.sub(r'\s*<script type="application/ld\+json" id="shop-ld-list"></script>', "", norm)

        out = norm.replace("\n", eol) if eol == "\r\n" else norm
        f.write_bytes((BOM if bom else b"") + out.encode("utf-8"))
    
        # sanity
        chk = f.read_text(encoding="utf-8-sig")
        for b in SCRIPT_RE.findall(chk):
            if b.strip():
                json.loads(b)
        n_cards = chk.count('<article class="watch-card')
        # shop/ also holds delivery.html, which is a page not a product. Count product
        # links against the catalog ids rather than "everything under shop/".
        linked = set(re.findall(rf'href="/{lang}/shop/([a-z0-9.-]+)\.html"', chk))
        ids = {w["id"] for w in W}
        assert ids <= linked, f"{lang}: unlinked products {sorted(ids - linked)}"
        assert not (linked - ids - {"delivery"}), f"{lang}: stray shop links {sorted(linked - ids - {'delivery'})}"
        n_links = len(ids)
        il = [json.loads(b) for b in SCRIPT_RE.findall(chk) if b.strip() and '"ItemList"' in b][0]
        assert n_cards == len(W), f"{lang}: {n_cards} cards != {len(W)}"
        assert "delivery" in linked, f"{lang}: delivery page not linked from the shop index"
        # itemlist() excludes sold, so this must compare against the live count, not
        # len(W). It asserted len(W) and would have crashed the first time a watch
        # was marked sold.
        assert il["numberOfItems"] == len(il["itemListElement"]) == S.n, f"{lang}: ItemList count"
        assert "\u2014" not in chk.split("</head>")[1].replace('watch-ref">Ref. \u2014', ""), f"{lang}: em dash"
        body_html = chk.split("</head>")[1]
        n_faq_vis = body_html.count('<details class="faq-item"')
        fd = [json.loads(b) for b in SCRIPT_RE.findall(chk) if b.strip() and '"FAQPage"' in b]
        fd = [d for d in fd if d.get("@type") == "FAQPage"]  # top-level only; @graph FAQ is pruned
        assert len(fd) == 1 and len(fd[0]["mainEntity"]) == n_faq_vis == 6, f"{lang}: FAQ sync"
        assert '"FAQPage"' not in json.dumps([json.loads(b) for b in SCRIPT_RE.findall(chk)
                                              if b.strip() and "@graph" in b]), f"{lang}: graph FAQ left"
        stripped = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body_html))
        for q in fd[0]["mainEntity"]:
            probe = re.sub(r"\s+", " ", q["acceptedAnswer"]["text"])[:60]
            assert probe in stripped, f"{lang}: FAQ answer not visible: {probe[:40]}"
        assert 'class="shop-crumb"' in chk, f"{lang}: crumb missing"
        assert "shop-ld-list" not in chk, f"{lang}: empty ld tag still present"
        print(f"{lang}/shop/index.html: {n_cards} cards, {n_links} links, "
              f"ItemList {il['numberOfItems']}, FAQ {n_faq_vis}, crumb OK")
    


if __name__ == "__main__":
    main()
    print("SHOP GRID PRE-RENDERED")
