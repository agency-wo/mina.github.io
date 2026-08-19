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
    ├── {en,it,sq}/         <- 168 + 168 + 172 pages
    └── gen_*.py            <- the generators
```

Gates run **from the working root** (`python scripts/audit-watches.py`). Generators run **from
`mina.github.io/`** (`python gen_shop_index.py`) because they import sibling modules.

512 HTML files. 61 live watches, 183 product pages (61 x 3; plus noindex redirect stubs the
gates skip), 15 brand pages, 84 article families in 5 categories, 18 service pages, 12 legal
pages. `sitemap.xml` is 487 urls / 1,944 hreflang alternates / 183 images.

These figures go stale on every catalogue or article change and **nothing regenerates this file**.
Do not quote them at a visitor and never copy one into a page. Read them off the gates instead:
`verify-product-pages.py` prints the product-page count, `verify-sitemap.py` the sitemap totals.

---

## Run order is a hard dependency, not a preference

```
python gen_shop_index.py
python gen_product_pages.py
python gen_brand_pages.py
python gen_blog_index.py
python gen_stats.py
python gen_sitemap.py        # ALWAYS LAST
```

`gen_brand_pages` imports `card()` and `W` from `gen_shop_index` and clones `{lang}/shop/index.html`,
so it must follow it. `gen_sitemap` fingerprints page **content** to decide `lastmod`, so anything
that rewrites HTML must run before it.

`gen_blog_index` does not depend on the shop generators, but it **belongs in this chain and must run
on every catalogue change**. The featured blog card's copy carries `{lolek}` and `{hilek}` price
tokens that only resolve when this generator runs, and the rendered index carries no `data-stat`
marker, so `gen_stats.py` cannot heal it afterwards. Leave it out and the blog's front page quietly
advertises the previous catalogue. That is a real incident: it shipped reading "50 of our 57
watches" after the counter had moved on, which is also why counts are no longer published at all.

**Never `import gen_product_pages`.** Its page loop is at module level, so importing it regenerates
all 183 product pages as a side effect. Run it as a script. `tools/test_sync_stock.py` imports
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
| `python scripts/verify-contact.py` | `CONTACT GATE PASS` |
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

- **NO PAGE STATES HOW MANY WATCHES.** Not a total, not per brand, not per price band, in digits
  or in words. The shop holds considerably more stock than it publishes, so every published count
  understated the shelf; the owner raised it more than once. This is enforced, not remembered:
  `catalog_stats.TOKEN_RE` no longer knows `{n}`, `{u10k}` or `{n:brand}` so `fill()` raises on
  one, `gen_stats.render()` raises on the matching `data-stat` keys, and `verify-stats.py` check G
  fails the build on either. **A word-form count reads clean to all three** ("four chronographs",
  "eleven models") so read for it. Rewrite the sentence; never revive the token.
- **Never type a catalogue-derived number into a page.** `catalog_stats.py` computes every one of
  them. Generated pages use the `{b} {lo} {hi} {lolek} {hilek}` tokens plus the per-brand
  `{lo:brand-slug}` family; hand-written pages carry `<span data-stat="lo">€50</span>` markers that
  `gen_stats.py` refreshes. The span must wrap a **whitespace-delimited whole token**, never
  `€<span>50</span>`, because the FAQ visibility probe in `gen_shop_index.py` turns every tag into
  a space. Brand count and prices stay: they are accurate and they sell.
- **Lek is half-up, never banker's rounding**: `int(EUR * 97 / 100 + 0.5) * 100`. Python's `round()`
  first disagrees at €50 (4,800 instead of 4,900) and Belonni is €50. There were once six copies of
  this formula and they had begun to diverge.
- **Thousands separator: comma in EN, dot in IT and SQ.** All three `shop.js` once called
  `toLocaleString()` with no locale, so an Italian phone reflowed the grid from 18,300 L to 18.300 L
  after hydration.
- **Reviews = 102**, owner-reported, one home in `catalog_stats.REVIEWS`. A dropping count is normal
  and must always match what Google shows. `scripts/fix-reviews.py` is retired and raises if run.
- Some counts must be **recomputed, not incremented** (steel watches, blue dials, subdials). When a
  new item cannot be classified, **drop the total rather than guess at it.**

### Contact

- **The phone number is a language question, not a constant.** `en` and `it` reach the owner on
  **+355 67 571 6090**. `sq` reaches his father on **+355 67 636 0510**, and his father speaks only
  Albanian, so an English or Italian page carrying that number sends a customer to someone who
  cannot serve them. The split covers display text, `tel:` links, `api.whatsapp.com/send?phone=`
  and the floating WhatsApp button alike.
- **`contact.py` is the one authority.** Take a number from `contact.phone(lang)` or
  `contact.wa_link(lang, msg)`, or from that language's own `shop/delivery.html`. Never copy one
  across languages.
- `scripts/verify-contact.py` fails the build on an Albanian number under `en/` or `it/`. It
  normalises `&thinsp;`, `&nbsp;` and `&#8201;` first, because the number is written four ways and
  a scan that allows only plain spaces reports a desynced corpus clean. That is a real incident:
  26 FAQ JSON-LD copies drifted from their visible twins and only `faq-build.py --verify` saw it.

### Claims

- **Sapphire crystal** is claimable only on the 7 Hislons and `romanson-bh3054gbr`.
- Say **"crystal-set"**, never "diamonds".
- **No Philippe Lauren description states a movement.**
- **Never call a watch a chronograph without verifying it.** The site counts real chronographs
  separately from lookalikes, having got it wrong once.
- **No fitting advice. Specs are fine.** The line, set by the owner on 2026-08-18 after this rule
  was found to contradict three published article families:
  - **Banned**: telling a reader what size to pick, asking for a wrist measurement, wrist-size
    reference tables, "measure your wrist", "send us your wrist size", "what suits your wrist",
    and size filters, size fields or gender fields on a product.
  - **Allowed**: a case diameter stated as a neutral fact ("the case is 40mm"), strap and lug
    widths (a repair fact a customer needs in order to buy the right strap), and **bracelet link
    adjustment described as a service we perform** ("we size it free at the counter",
    "lo adattiamo al tuo polso"). The service is the point; the advice is what was banned.
  - **Say that online buyers are welcome to walk in and have it sized.** Owner, 2026-08-18: the
    bracelet is adjusted at the counter for anyone who buys in the shop, "but they are welcome to
    come even if they [buy] online". That is a reason to buy, not a caveat, so it belongs in
    delivery, returns and buying copy rather than being trimmed away with the fitting advice.
  - Still banned outright: **wrist shots**.
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
4. The generator chain above, in order. **`gen_blog_index.py` included** — the featured blog card
   quotes the catalogue and nothing else can refresh it.
5. **Fix the prose the count broke.** The shop index, brand pages, blog indexes, sitemaps,
   `llms.txt` and all `data-stat` markers heal themselves. Article and service prose does not.

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
