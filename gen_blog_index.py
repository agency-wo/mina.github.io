#!/usr/bin/env python3
"""[DB-009] gen_blog_index.py — regenerates the three blog index pages from the manifest.
DOES:   rebuilds style block, chips, <main> (featured, Latest strip, five category
        sections) and the CollectionPage JSON-LD of {en,it,sq}/blog/index.html from
        blog_index_data.py + the articles' own dates; SKIPs byte-identical files.

gen_blog_index.py
Regenerates the three blog index pages ({en,it,sq}/blog/index.html) from
blog_index_data.py plus the articles themselves.

Why a generator: the index was hand-maintained and drifted three separate ways at
once - the visible section headings stopped matching the filter chips (seven buying
guides sat under the Gifts heading in IT and SQ), the ItemList JSON-LD order stopped
matching the page, and 23 cards had no date at all while the other 58 carried
hand-typed month literals. One taxonomy now lives in blog_index_data.py and
everything on the page is derived from it.

What the generator owns per file (everything else stays hand-maintained):
  A. the single <style> block's inner content
  B. the CollectionPage JSON-LD block (BreadcrumbList untouched)
  C. the chip row (chips can never drift from sections again)
  D. <main> wholesale: count line, featured, Latest strip, five category sections,
     empty state
  E. the blog-search.js?v= version

Ordering is by the EN article's datePublished DESC then manifest position, FOR ALL
THREE LANGUAGES: five families have per-language date drift and per-language ordering
would desync the mirrors. Displayed dates are each language's own - a card must never
claim an update its own article's schema denies.

The Latest strip holds duplicates (data-dup="1") of the three newest cards so the
category sections stay complete and their counts stay honest; blog-search.js hides
the strip whenever any filter or search is active, and the ItemList excludes dups.

Adding an article: add its family to blog_index_data.py ARTICLES (the build fails
loudly on any en/blog/*.html without an entry), then run this. Card title/desc
default to the article's BlogPosting headline + meta description when the entry
carries no card= override.

Byte discipline: these three files are no-BOM strict-CRLF and must stay that way.
Run from the repo: python gen_blog_index.py   (--seed builds the manifest once)
"""
import json
import re
import sys
from html import unescape
from pathlib import Path

import catalog_stats

BASE = Path(__file__).resolve().parent
LANGS = ("en", "it", "sq")
BLOG_SEARCH_V = 3
CATS = ("buying", "gifts", "care", "knowledge", "keys")  # owner order, money first
CAT_ICONS = {"buying": "fa-tag", "gifts": "fa-gift", "care": "fa-shield-alt",
             "knowledge": "fa-search", "keys": "fa-key"}
# every glyph here must exist in the subsetted Font Awesome (see shared.css);
# anything outside the subset renders as nothing.
PROVEN_GLYPHS = {"fa-tag", "fa-gift", "fa-shield-alt", "fa-search", "fa-key",
                 "fa-gem", "fa-clock", "fa-bolt", "fa-chevron-right",
                 "fa-balance-scale", "fa-cogs", "fa-tools", "fa-university",
                 "fa-graduation-cap", "fa-heart", "fa-star"}

UI = {
    "en": dict(
        aria="Filter by category", all_chip="All",
        latest="Latest Articles",
        count_tpl="Showing {n} of {t} articles",
        empty="No articles found. Try a different search or category.",
        readmore="Read article", readtime="{n} min read", updated="Updated",
        months=["January", "February", "March", "April", "May", "June", "July",
                "August", "September", "October", "November", "December"],
        cats={"buying": ("Buying Guides", "Buying Guide"),
              "gifts": ("Gift Guides", "Gift Guide"),
              "care": ("Watch Care", "Watch Care"),
              "knowledge": ("Watch Knowledge", "Watch Knowledge"),
              "keys": ("Key Services", "Key Services")},
    ),
    "it": dict(
        aria="Filtra per categoria", all_chip="Tutti",
        latest="Articoli Recenti",
        count_tpl="Mostrati {n} di {t} articoli",
        empty="Nessun articolo trovato. Prova una ricerca o categoria diversa.",
        readmore="Leggi l’articolo", readtime="{n} min di lettura",
        updated="Aggiornato",
        months=["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
                "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"],
        cats={"buying": ("Guide all’Acquisto", "Guida all’Acquisto"),
              "gifts": ("Guide ai Regali", "Guida ai Regali"),
              "care": ("Cura dell’Orologio", "Cura dell’Orologio"),
              "knowledge": ("Cultura Orologio", "Conoscenza Orologi"),
              "keys": ("Servizi Chiavi", "Servizi Chiavi")},
    ),
    "sq": dict(
        aria="Filtro sipas kategorisë", all_chip="Të gjitha",
        latest="Artikujt e Fundit",
        count_tpl="Po shfaqen {n} nga {t} artikuj",
        empty="Nuk u gjet asnjë artikull. Provo me një kërkim ose kategori tjetër.",
        readmore="Lexo artikullin", readtime="{n} min lexim",
        updated="Përditësuar",
        months=["Janar", "Shkurt", "Mars", "Prill", "Maj", "Qershor", "Korrik",
                "Gusht", "Shtator", "Tetor", "Nëntor", "Dhjetor"],
        cats={"buying": ("Udhëzues Blerjeje", "Udhëzues Blerjeje"),
              "gifts": ("Udhëzues Dhuratash", "Udhëzues Dhuratash"),
              "care": ("Kujdesi i Orës", "Kujdesi i Orës"),
              "knowledge": ("Njohuri Orësh", "Njohuri Orësh"),
              "keys": ("Shërbime Çelësash", "Shërbime Çelësash")},
    ),
}

# two IT articles say "min lettura" without "di", hence the optional group
READTIME_RE = {
    "en": re.compile(r"(\d+)\s*min read"),
    "it": re.compile(r"(\d+)\s*min(?:\s+di)?\s+lettura"),
    "sq": re.compile(r"(\d+)\s*min lexim"),
}

# The style block is identical across the three files. .b-row2 and .b-card-num are
# gone (no longer emitted); .b-label-count and .b-count are new; #blog-empty is
# declared ONCE (a second white-on-light rule used to make the text invisible).
STYLE = r""".solid-header{background:rgba(6,21,59,.98);border-bottom:2px solid rgba(180,148,92,.4);position:sticky;top:0;z-index:50;padding:0}
.nav-drawer{display:none}
#nav-toggle:checked~.nav-drawer{display:block!important}

    .blog-wrap{max-width:1100px;margin:0 auto;display:flex;flex-direction:column;gap:2rem}
    .b-feat{display:grid;grid-template-columns:5.5rem 1fr;gap:2.5rem;align-items:center;background:linear-gradient(135deg,#18110a 0%,#2c1d0d 60%,#1a1208 100%);border-radius:1.5rem;padding:2.5rem 3rem;text-decoration:none;color:#fff;position:relative;overflow:hidden;transition:transform .22s,box-shadow .22s;box-shadow:0 6px 40px rgba(0,0,0,.22)}
    .b-feat::before{content:'';position:absolute;top:0;left:0;width:5px;height:100%;background:var(--accent-gold);border-radius:6px 0 0 6px}
    .b-feat::after{content:'';position:absolute;inset:0;border-radius:1.5rem;border:1px solid rgba(180,148,92,.18);pointer-events:none}
    .b-feat:hover{transform:translateY(-4px);box-shadow:0 18px 56px rgba(0,0,0,.3)}
    .b-feat-num{font-size:5.5rem;font-weight:900;color:rgba(180,148,92,.18);font-family:'Cormorant Garamond',serif;line-height:1;user-select:none}
    .b-feat-cat{display:inline-flex;align-items:center;gap:.4rem;font-size:.68rem;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--accent-gold);margin-bottom:.6rem}
    .b-feat-title{font-size:1.7rem;font-weight:800;line-height:1.25;margin-bottom:.65rem;color:#fff}
    .b-feat-desc{font-size:.9rem;color:rgba(255,255,255,.62);line-height:1.6;margin-bottom:1.2rem;max-width:54ch}
    .b-feat-meta{display:flex;align-items:center;gap:1rem;font-size:.78rem;color:rgba(255,255,255,.4);margin-bottom:1.25rem}
    .b-feat-meta i{color:rgba(180,148,92,.7)}
    .b-feat-cta{display:inline-flex;align-items:center;gap:.5rem;font-size:.85rem;font-weight:700;color:var(--accent-gold);border:1.5px solid rgba(180,148,92,.4);padding:.55rem 1.3rem;border-radius:2rem;transition:background .2s,border-color .2s}
    .b-feat:hover .b-feat-cta{background:rgba(180,148,92,.12);border-color:rgba(180,148,92,.65)}
    .b-label{display:flex;align-items:center;gap:1rem;font-size:.68rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:#bbb;margin:0}
    .b-label::after{content:'';flex:1;height:1px;background:#e5ddd3}
    .b-label-count{background:rgba(180,148,92,.14);color:var(--accent-gold-accessible);padding:.2rem .6rem;border-radius:1rem;font-size:.65rem;font-weight:700;letter-spacing:normal}
    .b-count{text-align:center;font-size:.8rem;color:var(--text-secondary);margin:0}
    .b-grid3{display:grid;grid-template-columns:repeat(3,1fr);gap:1.25rem}
    .b-card{background:#fff;border-radius:1.1rem;box-shadow:0 2px 14px rgba(0,0,0,.07);display:flex;flex-direction:column;text-decoration:none;color:inherit;transition:transform .2s,box-shadow .2s,border-top-color .2s;border-top:3px solid transparent;overflow:hidden}
    .b-card:hover{transform:translateY(-3px);box-shadow:0 10px 30px rgba(0,0,0,.12);border-top-color:var(--accent-gold)}
    .b-card-body{padding:1.4rem 1.5rem;flex:1;display:flex;flex-direction:column}
    .b-card-cat{display:inline-flex;align-items:center;gap:.4rem;font-size:.68rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent-gold);margin-bottom:.6rem}
    .b-card-title{font-size:1.05rem;font-weight:800;line-height:1.3;margin-bottom:.5rem;color:var(--text-primary);flex:1}
    .b-card-desc{font-size:.83rem;color:var(--text-secondary);line-height:1.55;margin-bottom:.85rem}
    .b-card-meta{display:flex;align-items:center;gap:.6rem;font-size:.75rem;color:#999;margin-bottom:.75rem}
    .b-card-meta i{color:var(--accent-gold)}
    .b-card-link{display:inline-flex;align-items:center;gap:.35rem;font-size:.82rem;font-weight:700;color:var(--accent-gold);margin-top:auto}
    .b-card-link i{font-size:.65rem;transition:transform .2s}
    .b-card:hover .b-card-link i{transform:translateX(3px)}
    @media(max-width:960px){.b-grid3{grid-template-columns:1fr 1fr}.b-feat{grid-template-columns:1fr;padding:2rem}.b-feat-num{display:none}}
    @media(max-width:640px){.b-grid3{grid-template-columns:1fr}}
    .blog-search-wrap{position:relative;max-width:440px;margin:0 auto 1.75rem}
    .blog-search-icon{position:absolute;left:1rem;top:50%;transform:translateY(-50%);color:rgba(180,148,92,.7);font-size:.95rem;pointer-events:none}
    .blog-search-input{width:100%;padding:.7rem 1rem .7rem 2.6rem;background:rgba(255,255,255,.08);border:1.5px solid rgba(180,148,92,.3);border-radius:2rem;color:#fff;font-size:.9rem;outline:none;transition:border-color .2s,background .2s;box-sizing:border-box}
    .blog-search-input::placeholder{color:rgba(255,255,255,.38)}
    .blog-search-input:focus{border-color:rgba(180,148,92,.7);background:rgba(255,255,255,.12)}
    .blog-search-input::-webkit-search-cancel-button{cursor:pointer;filter:invert(1)opacity(.5)}
    .blog-cats{display:flex;flex-wrap:wrap;gap:.5rem;justify-content:center;max-width:700px;margin:0 auto 1.75rem}
    .b-cat-btn{display:inline-flex;align-items:center;gap:.35rem;padding:.45rem 1.05rem;border-radius:2rem;border:1.5px solid rgba(180,148,92,.45);background:rgba(255,255,255,.11);color:rgba(255,255,255,.82);font-size:.75rem;font-weight:600;letter-spacing:.05em;cursor:pointer;transition:all .18s;white-space:nowrap;line-height:1;font-family:inherit}
    .b-cat-btn:hover{border-color:rgba(180,148,92,.6);background:rgba(180,148,92,.12);color:#fff}
    .b-cat-btn[aria-pressed="true"]{background:var(--accent-gold);border-color:var(--accent-gold);color:#18110a}
    #blog-empty{display:none;text-align:center;padding:3rem 1rem;color:var(--text-secondary);font-size:.95rem}
    #blog-empty::before{content:'\f002';font-family:'Font Awesome 6 Free';font-weight:900;display:block;font-size:2rem;margin-bottom:.75rem;opacity:.4}
"""


# [DB-009.a] read_index — load one index and enforce its byte discipline
# OUT:    (path, raw bytes, LF-normalized text); asserts no BOM and strict CRLF.
def read_index(lang):
    p = BASE / lang / "blog" / "index.html"
    raw = p.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf"), f"{p}: unexpected BOM"
    assert raw.count(b"\n") == raw.count(b"\r\n"), f"{p}: not strict CRLF"
    return p, raw, raw.decode("utf-8").replace("\r\n", "\n")


# [DB-009.b] write_index — re-CRLF, verify, and write only on change
# DOES:   prints SKIP when the bytes are identical to what is on disk, so a no-op
#         rebuild is visibly a no-op.
def write_index(p, raw, html):
    out = html.replace("\n", "\r\n").encode("utf-8")
    assert out.count(b"\n") == out.count(b"\r\n") and b"\x0c" not in out
    if out == raw:
        print(f"  SKIP {p.relative_to(BASE).as_posix()}")
        return
    p.write_bytes(out)
    print(f"  WROTE {p.relative_to(BASE).as_posix()}")


def article_meta(lang, slug):
    """[DB-009.c] dates + read-time from the article itself, the single source of truth."""
    p = BASE / lang / "blog" / f"{slug}.html"
    t = p.read_text(encoding="utf-8", errors="strict")
    pub = re.search(r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})"', t)
    mod = re.search(r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})"', t)
    rt = READTIME_RE[lang].search(t)
    assert pub and mod, f"{p}: BlogPosting dates not found"
    assert rt, f"{p}: read-time string not found"
    return pub.group(1), mod.group(1), int(rt.group(1))


def family_map():
    """[DB-009.d] EN slug -> {it: slug, sq: slug} from the EN article's own hreflang links."""
    fam = {}
    for p in sorted((BASE / "en" / "blog").glob("*.html")):
        if p.name == "index.html":
            continue
        t = p.read_text(encoding="utf-8")
        m = {}
        for lg in ("it", "sq"):
            hit = re.search(
                rf'hreflang="{lg}"\s+href="https://watch\.al/{lg}/blog/([\w-]+)\.html"', t)
            assert hit, f"{p}: hreflang {lg} missing"
            m[lg] = hit.group(1)
        fam[p.stem] = m
    return fam


# [DB-009.e] date_str — "Month YYYY" in that language's own month names
def date_str(lang, iso):
    y, m, _ = iso.split("-")
    return f"{UI[lang]['months'][int(m) - 1]} {y}"


# [DB-009.f] load_manifest — ARTICLES from blog_index_data.py, fully validated
# DOES:   asserts slugs are unique and exactly match en/blog on disk (noindex stubs
#         excluded), exactly one featured entry exists, every cat is known and every
#         icon override is a proven glyph. Drift fails the build loudly.
# OUT:    (articles list, the featured entry)
def load_manifest():
    sys.path.insert(0, str(BASE))
    import blog_index_data
    arts = blog_index_data.ARTICLES
    slugs = [a["slug"] for a in arts]
    assert len(slugs) == len(set(slugs)), "duplicate slug in manifest"
    # noindex files in the blog directory are redirect stubs from a slug rename,
    # not articles. gen_sitemap.py excludes them by the same rule.
    on_disk = {p.stem for p in (BASE / "en" / "blog").glob("*.html")
               if "noindex" not in p.read_bytes().decode("utf-8-sig").lower()} - {"index"}
    assert set(slugs) == on_disk, (
        f"manifest vs en/blog drift: only-manifest={sorted(set(slugs) - on_disk)} "
        f"only-disk={sorted(on_disk - set(slugs))}")
    feats = [a for a in arts if a.get("featured")]
    assert len(feats) == 1, f"exactly one featured required, got {len(feats)}"
    for a in arts:
        assert a["cat"] in CATS, f"{a['slug']}: bad cat {a['cat']!r}"
        if "icon" in a:
            assert a["icon"] in PROVEN_GLYPHS, f"{a['slug']}: unproven glyph {a['icon']}"
    return arts, feats[0]


def card_texts(a, lang, fam):
    """[DB-009.g] (title, desc) for the card: manifest override or article-derived fallback."""
    if "card" in a:
        c = a["card"][lang]
        # counts and price bounds are tokens, never literals: the shop publishes
        # fewer watches than it holds and the number moves every month
        return (catalog_stats.fill(c["title"], lang), catalog_stats.fill(c["desc"], lang))
    slug = a["slug"] if lang == "en" else fam[a["slug"]][lang]
    t = (BASE / lang / "blog" / f"{slug}.html").read_text(encoding="utf-8")
    h = re.search(r'"headline"\s*:\s*"([^"]+)"', t)
    d = re.search(r'<meta name="description" content="([^"]*)"', t)
    assert h and d, f"{lang}/{slug}: no headline/description to derive a card from"
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return esc(unescape(h.group(1))), esc(d.group(1))


# [DB-009.h] meta_html — the read-time + date line of a card
# DOES:   shows "Updated <month>" only when dateModified genuinely postdates
#         datePublished, so a card never claims an update its article denies.
def meta_html(lang, meta):
    pub, mod, rt = meta
    iso, label = (mod, f"{UI[lang]['updated']} {date_str(lang, mod)}") if mod > pub \
        else (pub, date_str(lang, pub))
    rts = UI[lang]["readtime"].format(n=rt)
    return (f'<div class="b-card-meta"><span><i class="fas fa-clock" aria-hidden="true">'
            f'</i> {rts}</span><span><i class="fas fa-bolt" aria-hidden="true"></i> '
            f'<time datetime="{iso}">{label}</time></span></div>')


# [DB-009.i] card_html — one grid card; dup=True marks a Latest-strip duplicate
# NOTES:  data-dup="1" is what blog-search.js keys on to hide duplicates while
#         any filter is active; the ItemList excludes dups for the same reason.
def card_html(a, lang, fam, meta, dup=False):
    slug = a["slug"] if lang == "en" else fam[a["slug"]][lang]
    title, desc = card_texts(a, lang, fam)
    label = a.get("label", {}).get(lang) or UI[lang]["cats"][a["cat"]][1]
    icon = a.get("icon", CAT_ICONS[a["cat"]])
    m = meta_html(lang, meta)
    return f"""          <a data-cat="{a['cat']}" href="/{lang}/blog/{slug}.html" class="b-card"{' data-dup="1"' if dup else ''}>
            <div class="b-card-body">
              <span class="b-card-cat"><i class="fas {icon}" aria-hidden="true"></i> {label}</span>
              <h2 class="b-card-title">{title}</h2>
              <p class="b-card-desc">{desc}</p>
              {m}
              <span class="b-card-link">{UI[lang]['readmore']} <i class="fas fa-chevron-right" aria-hidden="true"></i></span>
            </div>
          </a>"""


# [DB-009.j] feat_html — the single featured (hero) card
def feat_html(a, lang, fam, meta):
    slug = a["slug"] if lang == "en" else fam[a["slug"]][lang]
    title, desc = card_texts(a, lang, fam)
    label = a.get("label", {}).get(lang) or UI[lang]["cats"][a["cat"]][1]
    icon = a.get("icon", CAT_ICONS[a["cat"]])
    m = meta_html(lang, meta).replace("b-card-meta", "b-feat-meta")
    return f"""        <a data-cat="{a['cat']}" href="/{lang}/blog/{slug}.html" class="b-feat">
          <span class="b-feat-num" aria-hidden="true">01</span>
          <div>
            <span class="b-feat-cat"><i class="fas {icon}" aria-hidden="true"></i> {label}</span>
            <h2 class="b-feat-title">{title}</h2>
            <p class="b-feat-desc">{desc}</p>
            {m}
            <span class="b-feat-cta">{UI[lang]['readmore']} <i class="fas fa-chevron-right" aria-hidden="true"></i></span>
          </div>
        </a>"""


# [DB-009.k] build_main — the whole <main> of one blog index
# DOES:   count line, featured hero, Latest strip (3 newest as dups), the five
#         category sections in owner order, and the empty state.
# NOTES:  order is the EN datePublished DESC for ALL languages (mirror-sync rule
#         in the module docstring); returns (main html, order, latest indexes).
def build_main(lang, arts, feat, fam, metas):
    u = UI[lang]
    order = sorted(range(len(arts)),
                   key=lambda i: (metas["en"][arts[i]["slug"]][0], -i), reverse=True)
    latest = [i for i in order if arts[i] is not feat][:3]
    parts = [f'        <p id="blog-count" class="b-count" aria-live="polite" hidden '
             f'data-tpl="{u["count_tpl"]}"></p>', ""]
    parts += [feat_html(feat, lang, fam, metas[lang][feat["slug"]]), ""]
    parts += [f'        <p class="b-label" id="b-latest-label">{u["latest"]}</p>',
              '        <div class="b-grid3" id="b-latest">']
    parts += [card_html(arts[i], lang, fam, metas[lang][arts[i]["slug"]], dup=True)
              for i in latest]
    parts += ["        </div>", ""]
    for cat in CATS:
        idxs = [i for i in order if arts[i]["cat"] == cat and arts[i] is not feat]
        total = len(idxs) + (1 if feat["cat"] == cat else 0)
        parts += [f'        <p class="b-label" data-sec="{cat}">{u["cats"][cat][0]} '
                  f'<span class="b-label-count">{total}</span></p>',
                  f'        <div class="b-grid3" data-sec-grid="{cat}">']
        parts += [card_html(arts[i], lang, fam, metas[lang][arts[i]["slug"]])
                  for i in idxs]
        parts += ["        </div>", ""]
    parts += [f'        <p id="blog-empty">{u["empty"]}</p>']
    body = "\n".join(parts)
    return (f'<main id="main-content">\n'
            f'    <section class="py-16 px-6" style="background:var(--bg-soft)">\n'
            f'      <div class="blog-wrap">\n\n{body}\n\n'
            f'      </div>\n    </section>\n  </main>'), order, latest


def build_itemlist(lang, arts, feat, fam, order, page):
    """[DB-009.l] CollectionPage JSON-LD in DOM order: featured first, then sections."""
    blocks = re.findall(r'<script type="application/ld\+json">.*?</script>', page, re.S)
    src = [b for b in blocks if '"CollectionPage"' in b]
    assert len(src) == 1, f"{lang}: expected one CollectionPage block"
    old = json.loads(re.sub(r"^<script[^>]*>|</script>$", "", src[0]).strip())
    seq = [feat] + [arts[i] for cat in CATS for i in order
                    if arts[i]["cat"] == cat and arts[i] is not feat]
    items = []
    for pos, a in enumerate(seq, 1):
        slug = a["slug"] if lang == "en" else fam[a["slug"]][lang]
        title, _ = card_texts(a, lang, fam)
        items.append({"@type": "ListItem", "position": pos,
                      "name": unescape(re.sub(r"<[^>]+>", "", title)),
                      "url": f"https://watch.al/{lang}/blog/{slug}.html"})
    data = {"@context": "https://schema.org", "@type": "CollectionPage",
            "name": old["name"], "url": old["url"], "inLanguage": old["inLanguage"],
            "numberOfItems": len(seq),
            "mainEntity": {"@type": "ItemList", "name": old["name"],
                           "numberOfItems": len(seq), "itemListElement": items}}
    new = ('<script type="application/ld+json">'
           + json.dumps(data, ensure_ascii=False) + "</script>")
    return page.replace(src[0], new)


# [DB-009.m] build_chips — the filter chip row, derived from CATS
# NOTES:  generated from the same taxonomy as the sections, so chips can never
#         drift from what they filter (the original hand-maintained failure mode).
def build_chips(lang):
    u = UI[lang]
    rows = [f'<div class="blog-cats" role="group" aria-label="{u["aria"]}">',
            f'        <button class="b-cat-btn" data-filter="all" aria-pressed="true">{u["all_chip"]}</button>']
    for cat in CATS:
        rows.append(f'        <button class="b-cat-btn" data-filter="{cat}" '
                    f'aria-pressed="false"><i class="fas {CAT_ICONS[cat]}" '
                    f'aria-hidden="true"></i> {u["cats"][cat][0]}</button>')
    rows.append("      </div>")
    return "\n".join(rows)


# [DB-009.n] generate — the normal build: rebuild all three indexes in place
# DOES:   style block, <main>, chips, ItemList, blog-search.js ?v= bump, em-dash
#         ban, then write_index's changed-only write.
def generate():
    arts, feat = load_manifest()
    fam = family_map()
    metas = {lang: {a["slug"]: article_meta(
        lang, a["slug"] if lang == "en" else fam[a["slug"]][lang])
        for a in arts} for lang in LANGS}
    for lang in LANGS:
        p, raw, html = read_index(lang)
        assert html.count("<style") == 1 and html.count("<main") == 1
        i, j = html.index("<style>") + 7, html.index("</style>")
        html = html[:i] + STYLE + html[j:]
        i, j = html.index("<main"), html.index("</main>") + 7
        main, order, _ = build_main(lang, arts, feat, fam, metas)
        html = html[:i] + main + html[j:]
        i = html.index('<div class="blog-cats"')
        j = html.index("</div>", i) + 6
        assert "<div" not in html[i + 1:j - 6], f"{lang}: chips div not flat"
        html = html[:i] + build_chips(lang) + html[j:]
        html = build_itemlist(lang, arts, feat, fam, order, html)
        html = re.sub(r"blog-search\.js\?v=\d+", f"blog-search.js?v={BLOG_SEARCH_V}", html)
        assert "—" not in html and "&#8212;" not in html and "&mdash;" not in html
        write_index(p, raw, html)


# ---------------------------------------------------------------------------- seed
def seed():
    """[DB-009.o] One-off: build blog_index_data.py from the CURRENT hand-tuned indexes."""
    out = BASE / "blog_index_data.py"
    assert not out.exists(), f"{out} already exists; refusing to overwrite"
    fam = family_map()
    rev = {v[lg]: en for en, v in fam.items() for lg in ("it", "sq")}
    rev.update({en: en for en in fam})

    harvest = {}  # lang -> en_slug -> dict(cat, label, title, desc, kind)
    for lang in LANGS:
        _, _, html = read_index(lang)
        cards = {}
        for m in re.finditer(
                r'<a data-cat="(\w+)" href="/' + lang +
                r'/blog/([\w-]+)\.html" class="b-(card|feat)"[^>]*>(.*?)</a>',
                html, re.S):
            cat, slug, kind, body = m.groups()
            en = rev[slug]
            t = re.search(r'<h2 class="b-(?:card|feat)-title">(.*?)</h2>', body, re.S)
            d = re.search(r'<p class="b-(?:card|feat)-desc">(.*?)</p>', body, re.S)
            lab = re.search(r'class="b-(?:card|feat)-cat">(.*?)</span>', body, re.S)
            raw_label = re.sub(r"<i[^>]*></i>\s*|<svg.*?</svg>\s*", "", lab.group(1),
                               flags=re.S)
            rec = dict(cat=cat, label=unescape(raw_label).strip(),
                       title=t.group(1).strip(), desc=d.group(1).strip())
            # featured is duplicated as a normal card today; the card copy wins
            if en not in cards or kind == "card":
                cards[en] = rec
        assert len(cards) == len(fam), f"{lang}: {len(cards)} families != {len(fam)}"
        harvest[lang] = cards

    # order: EN datePublished DESC, then current EN DOM order
    dom = [rev[s] for s in re.findall(
        r'<a data-cat="\w+" href="/en/blog/([\w-]+)\.html" class="b-card"',
        read_index("en")[2])]
    seen, dom_order = set(), []
    for s in dom:
        if s not in seen:
            seen.add(s)
            dom_order.append(s)
    pubs = {s: article_meta("en", s)[0] for s in fam}
    ordered = sorted(dom_order, key=lambda s: (pubs[s], -dom_order.index(s)),
                     reverse=True)

    lines = ['"""Taxonomy and hand-tuned card copy for gen_blog_index.py.',
             "",
             "One entry per trilingual article family, newest first (list order is the",
             "tie-break for equal dates). cat is the single category authority; the EN",
             "value won every seed conflict, per the owner. card= holds the hand-tuned",
             "index copy verbatim, entities included; omit card= on future entries to",
             "derive from the article headline + meta description. label= overrides the",
             'category card label where the old index carried nuance ("Watch History",',
             '"Brand Comparison"); icon= must be a PROVEN_GLYPHS member.',
             '"""', "", "ARTICLES = ["]
    defaults = {lg: {c: UI[lg]["cats"][c][1] for c in CATS} for lg in LANGS}
    for en in ordered:
        e = harvest["en"][en]
        cat = e["cat"] if e["cat"] != "repair" else "care"
        confl = [f"{lg}={harvest[lg][en]['cat']}" for lg in ("it", "sq")
                 if harvest[lg][en]["cat"] != cat]
        if confl or e["cat"] == "repair":
            lines.append(f"    # CONFLICT seeded en={e['cat']} "
                         + " ".join(confl) + " -> using " + cat)
        lines.append("    dict(")
        lines.append(f"        slug={en!r}, cat={cat!r},"
                     + (" featured=True," if en == "watches-under-10000-lek" else ""))
        labels = {lg: harvest[lg][en]["label"] for lg in LANGS}
        if any(labels[lg] != defaults[lg][cat] for lg in LANGS):
            lines.append(f"        label=dict(en={labels['en']!r}, "
                         f"it={labels['it']!r}, sq={labels['sq']!r}),")
        lines.append("        card=dict(")
        for lg in LANGS:
            h = harvest[lg][en]
            lines.append(f"            {lg}=dict(title={h['title']!r},")
            lines.append(f"                    desc={h['desc']!r}),")
        lines.append("        ),")
        lines.append("    ),")
    lines += ["]", ""]
    out.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    print(f"seeded {out.name}: {len(ordered)} families")


if __name__ == "__main__":
    if "--seed" in sys.argv:
        seed()
    else:
        generate()
