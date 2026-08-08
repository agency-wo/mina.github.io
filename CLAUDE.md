# watch.al

Trilingual (EN/IT/SQ) static site for **Iglisi Watch**, a family watch repair shop and watch
retailer on Rruga Aleksander Goga, Durrës, Albania. Open since 2009. GitHub Pages behind
Cloudflare, deployed on push to `main`, live about a minute later.

**Standing brief: sell more watches.** Repair traffic is strong, watch sales are not. Everything
else is a means to that end. There is no cart and no checkout: the whole conversion path ends in a
prefilled WhatsApp message with cash on delivery, or a walk-in to the shop.

---

## Geography

```
watch-repair-shop/          <- working root, NOT a git repo
├── scripts/                <- gates and one-shot migrations, OUTSIDE git
├── .claude/agents/         <- the lane agents, OUTSIDE git
└── mina.github.io/         <- THE GIT REPO, deploys to watch.al
    ├── tools/              <- sync_stock.py and the only test file
    ├── {en,it,sq}/         <- 161 + 161 + 165 pages
    └── gen_*.py            <- the generators
```

Gates run **from the working root** (`python scripts/audit-watches.py`). Generators run **from
`mina.github.io/`** (`python gen_shop_index.py`) because they import sibling modules.

491 HTML files. 58 live watches, 174 product pages (58 x 3; plus 6 noindex redirect stubs the
gates skip), 15 brand pages, 240 blog articles in 5
categories, 18 service pages, 12 legal pages. `sitemap.xml` is 466 urls / 1,860 hreflang alternates
/ 348 images.

---

## Run order is a hard dependency, not a preference

```
python gen_shop_index.py
python gen_product_pages.py
python gen_brand_pages.py
python gen_stats.py
python gen_sitemap.py        # ALWAYS LAST
```

`gen_brand_pages` imports `card()` and `W` from `gen_shop_index` and clones `{lang}/shop/index.html`,
so it must follow it. `gen_sitemap` fingerprints page **content** to decide `lastmod`, so anything
that rewrites HTML must run before it. `gen_blog_index.py` is independent of this chain.

**Never `import gen_product_pages`.** Its page loop is at module level, so importing it regenerates
all 174 product pages as a side effect. Run it as a script. `tools/test_sync_stock.py` imports
`shop_bits` instead for exactly this reason.

---

## The gates

None are wired into CI. `.github/workflows/stock-sync.yml` (daily CRM reconcile) is the only
automatic job, so verification depends on somebody running these. All are read-only and exit 1 on
findings.

| command (from the working root) | PASS line |
|---|---|
| `python scripts/audit-watches.py` | `AUDIT CLEAN - 0 findings` |
| `python scripts/verify-product-pages.py` | `PRODUCT PAGE GATE PASS` |
| `python scripts/verify-sitemap.py` | `SITEMAP GATE PASS` |
| `python scripts/verify-stats.py [--all]` | `STATS GATE PASS` |
| `python scripts/verify-blog-index.py` | `BLOG INDEX GATE PASS` |
| `python scripts/faq-build.py --verify` | `problems: 0` |
| `python mina.github.io/tools/test_sync_stock.py` | `OK` |

`verify-blog-index.py` compares against **git HEAD**, so an intentional copy edit reads red until it
is committed. That is by design: confirm the change was deliberate, then commit.

---

## Finding your way: the `[TAG-NNN]` index

Every hand-written source file carries a header comment with a bracketed tag. **Grep the tag to
jump straight to the thing.** The header says what the file is, what it takes, what it emits, and
which bug each awkward line exists to prevent.

```js
// [UI-005] booking.js — service-booking form that hands off to WhatsApp
// DOES:   validates #bookForm, builds a localized message (en/it/sq from <html lang>)
// IN:     #bookForm fields: service, name, phone (required)
// OUT:    window.open on api.whatsapp.com with the encoded message
// NOTES:  falls back to the raw ISO string if toLocaleDateString throws.
```

Functions get `.a`, `.b`, `.c` in source order under their file's tag. Python modules prepend the
tag to the existing docstring and keep it. Fields are `DOES: IN: OUT: CALLS: NOTES:`, padded so
the body starts at a fixed column; only the tag line is mandatory. Cross-reference another tag as
a bare bracket in prose: `(see [SEC-002])`. Em dashes are fine **here** — the no-em-dash rule is
about rendered prose, not comments.

**The namespace is shared with the part-tracker repo.** `W:` is this repo, `T:` is the tracker,
and the registry is `part tracker/docs/CODE_INDEX.md`. Prefixes are a closed set:
`UI UX API DB CRM SEC PERF ERR UTIL CFG`. Numbers are **sequential per prefix and never reused**,
including numbers consumed only by a commit subject, so **never allocate one by eye**:

```
python scripts/check-tags.py      # prints the next free number per prefix, across both
                                  # repos and both git logs, and fails on duplicates
```

Commit subjects carry the tags the work consumed, concatenated, ranges as `..`:
`[UI-005..015][UX-002][SEC-003..004] W5: indexed headers across the site's source`.

Where tags are deliberately absent: `watches-data.js` and the generated HTML (both build output),
and the 491 pages generally. `shared.js` is minified so it gets a file header only.

**Adding a tag is comment-only work.** Prove it the way commit `8120eec` did: `ast.parse` every
`.py`, `node --check` every `.js`, then re-run all the generators and confirm each reports
SKIP / Unchanged / `Written: 0`.

## Binding rules

Breaking one of these has caused a real incident. They are not style preferences.

### Numbers

- **Never type a catalogue-derived number into a page.** `catalog_stats.py` computes every one of
  them. Generated pages use `{n} {b} {lo} {hi} {lolek} {hilek} {u10k} {n:brand-slug}` tokens;
  hand-written pages carry `<span data-stat="n">58</span>` markers that `gen_stats.py` refreshes.
  The span must wrap a **whitespace-delimited whole token** (`<span data-stat="lo">€50</span>`,
  never `€<span>50</span>`) because the FAQ visibility probe in `gen_shop_index.py` turns every tag
  into a space.
- **Lek is half-up, never banker's rounding**: `int(EUR * 97 / 100 + 0.5) * 100`. Python's `round()`
  first disagrees at €50 (4,800 instead of 4,900) and Belonni is €50. There were once six copies of
  this formula and they had begun to diverge.
- **Thousands separator: comma in EN, dot in IT and SQ.** All three `shop.js` once called
  `toLocaleString()` with no locale, so an Italian phone reflowed the grid from 18,300 L to 18.300 L
  after hydration.
- **Reviews = 104**, owner-reported, one home in `catalog_stats.REVIEWS`. A dropping count is normal
  and must always match what Google shows. `scripts/fix-reviews.py` is retired and raises if run.
- Some counts must be **recomputed, not incremented** (steel watches, blue dials, subdials). When a
  new item cannot be classified, **drop the total rather than guess at it.**

### Claims

- **Sapphire crystal** is claimable only on the 7 Hislons and `romanson-bh3054gbr`.
- Say **"crystal-set"**, never "diamonds".
- **No Philippe Lauren description states a movement.**
- **Never call a watch a chronograph without verifying it.** The site counts real chronographs
  separately from lookalikes, having got it wrong once.
- **No fitting or size work of any kind.** No case diameters, no wrist shots, no size filters, no
  gender fields. The owner has banned the entire category.
- **The six real workshop photos are embargoed** until the owner says the renovation is finished.
- **Product H1 wording is owner-fixed** and carries search value. Do not rewrite it.

### Writing

- **No em dashes.** Not `—`, not `&mdash;`, not `&#8212;`. Several gates assert this.
- **No AI filler.** No "in today's world", no "it's worth noting", no throat-clearing.
- **Every CTA links to an exact product page**, never to the shop index.
- Nothing ships in one language. EN, IT and SQ go together, with localised slugs and reciprocal
  hreflang.

### Structure

- **Static equals runtime.** The shop grid is re-rendered by `{lang}/shop/shop.js` from the same
  data. `gen_shop_index.card()` and `watchCard()` mirror each other **byte for byte**, including the
  non-breaking space before the `L` in a price. Change one and you must change the other in the same
  edit, or make the change CSS-only. A second renderer was deleted once for producing `NaN` Lek
  prices; do not reintroduce one.
- **A FAQ answer exists twice**: visible HTML and a `FAQPage` JSON-LD twin. Author it once in
  `scripts/faq-overrides.json` and let `faq-build.py` write both copies in one pass.
  `faq-build.py --verify` fails any page whose schema claims an answer the reader cannot see.
- **Never put a `<span>` inside JSON-LD.** Wrapping a price range in a marker once matched its FAQ
  schema twin too, injected HTML into a JSON string and broke the Italian and Albanian homepages.
- **Inline `<script>` is dead sitewide.** `_headers` sets `script-src 'self'` with no
  `unsafe-inline`, so an inline script silently never runs. Inline `<style>` is fine. JSON-LD is
  data, not script, and is allowed.
- **Font Awesome is subsetted to 64 declared glyphs** in `shared.css`. A class outside the subset
  renders as **nothing** and no text-based check can see it. This is the most repeated bug in the
  repo's history.

### Bytes

- `core.autocrlf=true` with **no `.gitattributes`**, so the correct EOL and BOM depend on which
  machine checked out. **Mirror the existing file's shape, never assume one:**
  ```python
  def style_of(raw):                       # tools/sync_stock.py
      return ("\r\n" if b"\r\n" in raw else "\n", raw.startswith(b"\xef\xbb\xbf"))
  ```
  A gate must assert a file is internally consistent (all-CRLF or all-LF), never a fixed shape. The
  blog indexes are the one exception with a fixed contract: no BOM, strict CRLF.
- **Albanian and Italian mix encodings inside a single file** — 151 of 165 SQ files carry both
  `&euml;` and a literal `ë`, and 129 IT files carry entities. **Any sweep must match both forms** or
  it will report a corrupt corpus clean.

---

## Adding a watch

The most frequent job here, and the one with the longest ripple.

1. `scripts/process-new-watch-images.py` — set `JOBS` to **only** the new watch. It overwrites
   unconditionally, so a stale entry re-encodes an existing image and dirties the diff for a watch
   nobody touched. Output: 800×800 white-canvas `.webp` + `.jpg`.
2. Append to **both** `watches.json` and `watches-data.js`, written from one source using
   `tools/sync_stock.py`'s `style_of` / `json_bytes` / `data_js_bytes`. Descriptions must contain no
   `"` and no `&`. Give the watch a **model name unique across the whole catalogue**, or `DUP_NAMES`
   appends a reference and retroactively rewrites the existing watch's title in all three languages.
3. `scripts/make-new-watch-pages.py` with `NEW_IDS` set.
4. The generator chain above, in order.
5. **Fix the prose the count broke.** The shop index, brand pages, sitemaps, `llms.txt` and all
   `data-stat` markers heal themselves. Blog and service prose does not.

Nothing needs a cache-bust: the `watches-data.js?v=` requirement died with the runtime renderer.

---

## The lanes

Work is divided between agents in `../.claude/agents/`. Each owns a file set no other lane writes.

`shop` · catalogue and buying path — `blog` · the 240 articles — `funnel` · homepages, services,
about, b2b, delivery, legal — `seo` · sitemap, stats, llms.txt, robots, FAQ, schema — `ui` ·
`shared.css`, chrome, glyphs, assets (CSS-only) — `lang` · all Italian and Albanian prose —
`verify` · the gates.

Four **derived regions** are written by a lane that does not own the surrounding file, and this is
correct rather than a conflict: `gen_stats.py` owns what is inside a `data-stat` span, `ui` owns the
`?v=` cache-bust sweep, `verify` owns the CSP meta, and `faq-build.py` owns both copies of a FAQ
answer. In each case a second writer can only produce a stale value, never a conflicting one.

**Agents stop at green gates.** They run the gates that cover their surface, report the exact
output, and leave committing and pushing to the owner.
