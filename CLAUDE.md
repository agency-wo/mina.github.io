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
├── scripts/                <- one-shots and operator tools, OUTSIDE git
├── .claude/agents/         <- the lane agents, OUTSIDE git
└── mina.github.io/         <- THE GIT REPO, deploys to watch.al
    ├── tools/              <- sync_stock.py, make_shells.py
    │   └── gates/          <- the 8 gates + run.py, IN git so CI can run them
    ├── {en,it,sq}/         <- the three language trees
    └── gen_*.py            <- the generators
```

Gates run **from the working root** (`python mina.github.io/tools/gates/run.py`). Generators run
**from `mina.github.io/`** (`python gen_shop_index.py`) because they import sibling modules.

The site is the three language trees plus the shop, the brand hubs, the article families in 5
categories, the service pages and the legal pages.

**No counts are written here.** Every one that used to be gave a wrong number: this file said 512
HTML files against 605 real, 61 watches against 70, 487 sitemap locs against 577. The rules were
fine; the numbers rotted, and a reader who spot-checks one stops trusting the section it sits in.
A `SessionStart` hook now computes them from the working tree and injects them, so they are
always current. On demand: `verify-product-pages.py` prints the product-page count,
`verify-sitemap.py` the sitemap totals. Never copy one into a page.

---

## Run order is a hard dependency, not a preference

```
python gen_shop_index.py
python gen_product_pages.py
python gen_brand_pages.py
python gen_blog_index.py
python gen_article_cta.py
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
every product page as a side effect. Run it as a script. `tools/test_sync_stock.py` imports
`shop_bits` instead for exactly this reason.

---

## The gates

All are read-only and exit 1 on findings. `tools/gates/run.py` runs all eight in ONE process so
`tools/gates/corpus.py` can cache the corpus across them: measured 9,565 reads served from 620
actual file opens, where the eight separate processes did ~13,000 opens of 848 files.

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
jump straight to the thing.** Functions get `.a`, `.b`, `.c` **in source order** under their
file's tag.

The namespace is shared with the part-tracker repo, prefixes are a closed set, and numbers are
**sequential per prefix and never reused** - including numbers consumed only by a commit
subject, so **never allocate one by eye**:

```
python scripts/check-tags.py      # next free number per prefix, across both repos and both
                                  # git logs; fails on duplicates and on out-of-order letters
python scripts/renumber-tags.py <file> <TAG>   # fixes an ordering finding; --apply to write
```

**Adding a tag is comment-only work.** Prove it: `ast.parse` every `.py`, `node --check` every
`.js`, then re-run all the generators and confirm each reports SKIP / `Updated: 0` /
`Written: 0`.

Full format spec - header fields, the worked example, the commit-subject convention, where tags
are deliberately absent: `docs/reference/tags.md`.

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
- **Lek is half-up, never banker's rounding**: `int(EUR * LEK_RATE / 100 + 0.5) * 100`, with the
  rate in `catalog_stats.LEK_RATE`. **It is 92.25 as of 2026-08-25 and it is a float.** Python's
  `round()` disagrees whenever the product lands on an exact .5: at the old rate of 97 that was €50
  (4,800 instead of 4,900) and Belonni is €50, so the bug was live on the cheapest watch. **At 92.25
  the only tie in range is €200** (18,400 instead of 18,500), and nothing costs €200 today, so the
  next person to price a watch there is the one who finds out. There were once six copies of this
  formula and they had begun to diverge.
- **A rate change reprices roughly 3,000 published figures.** The shop, the brand pages, `llms.txt`
  and every `data-stat` marker heal on a generator run. **Article prose does not**, and neither do
  the three homepages, which no generator owns. `verify-stats.py` check E is the oracle: it reads
  every euro/Lek pair in four shapes (parenthesised both ways, and the `·`/`/` separator forms) and
  proves the arithmetic. Widen that check before a repricing, never after.
- **Thousands separator: comma in EN, dot in IT and SQ.** All three `shop.js` once called
  `toLocaleString()` with no locale, so an Italian phone reflowed the grid from 18,300 L to 18.300 L
  after hydration.
- **The review count is owner-reported and lives once, in `catalog_stats.REVIEWS`.** The number is
  deliberately not repeated here: it is external, it moves, and a frozen copy in an instruction
  file cannot follow Google. Read it from that constant, and confirm it against the profile before
  publishing it anywhere. A dropping count is normal. `scripts/fix-reviews.py` is retired and
  raises if run.
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
- **Every CTA links to an exact product page**, never to the shop index. **Match the anchor text,
  never the href**: every article also carries a *breadcrumb* to the shop index, and a sweep on
  `href="/xx/shop/"` alone hits every one of them and deletes the site's navigation. The breadcrumb
  label is not even constant — Italian articles use the English word `Shop`, Albanian mixes `Shop`
  and `Dyqan`. A prose link that writes `watch.al/xx/shop/` as an address, or that genuinely means
  the whole catalogue ("see the full stock on the shop page"), is correct and stays: repointing it
  at one watch makes the sentence false.
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
- **A media query adds no specificity, so a responsive override must come LAST.** Put
  `@media(max-width:600px){.watch-price{font-size:1.2rem}}` above the base `.watch-price{...
  font-size:1.45rem}` and the phone silently gets 1.45rem: same specificity, later rule wins.
  Nothing reports it. The declaration is present, spelled correctly, and dead. This has now bitten
  twice: the three homepages, then the shop index and the brand hubs that clone it, where seven
  declarations had never once applied and the phone was rendering desktop padding and a desktop
  serif price. **Append responsive overrides at the end of the block**, and when a page looks wrong
  at one breakpoint only, check the rule ORDER before rewriting the value:
  ```python
  # a page is clean when, for every (selector, property), the winning declaration
  # by (specificity, document order) is not a base rule that a media query meant to beat
  ```

- **The viewport is `viewport-fit=cover` on every real page, so every bottom-fixed element must
  carry `env(safe-area-inset-bottom)`** and the header wrap carries `env(safe-area-inset-top)`.
  That is what lets iPhones and in-app WebViews that lay the page out edge-to-edge keep the header
  and the call bar clear of the notch, the home indicator and a host app's bar. A new fixed-bottom
  element without the inset sits under the home indicator in Safari. The noindex stubs are
  exempt: they refresh in 0s.
- **In-app browsers are handled by `/inapp.js` + the `html.in-app*` hooks in `shared.css`.** The
  script loads synchronously right after the viewport meta (before first paint, on purpose) and
  flags Instagram, Facebook, Messenger, TikTok, WhatsApp and generic WebViews by user agent;
  `shared.css` unsticks the header and pushes it below the host's translucent bar. Clients were
  sending screenshots with the logo and call buttons hidden under that bar (2026-08-20). No
  "open in browser" nudge, ever: the owner declined one. New pages inherit the tag by cloning;
  `scripts/add-viewport-fit.py` re-sweeps if one is ever missed.

### Bytes

- `core.autocrlf=true` with **no `.gitattributes`**, so the correct EOL and BOM depend on which
  machine checked out. **Mirror the existing file's shape, never assume one:**
  ```python
  def style_of(raw):                       # tools/sync_stock.py
      return ("\r\n" if b"\r\n" in raw else "\n", raw.startswith(b"\xef\xbb\xbf"))
  ```
  A gate must assert a file is internally consistent (all-CRLF or all-LF), never a fixed shape. The
  blog indexes are the one exception with a fixed contract: no BOM, strict CRLF.
- **Albanian and Italian mix encodings inside a single file** — most SQ files carry both
  `&euml;` and a literal `ë`, and most IT files carry entities. **Any sweep must match both forms** or
  it will report a corrupt corpus clean.

---

## Adding a watch

The most frequent job here, and the one with the longest ripple. Run `/add-watch`, which carries
the full procedure and its footguns. The five steps:

1. `scripts/process-new-watch-images.py` - set `JOBS` to **only** the new watch. It overwrites
   unconditionally, so a stale entry re-encodes a published image.
2. Append to **both** `watches.json` and `watches-data.js` from one source, via
   `tools/sync_stock.py`'s `style_of` / `json_bytes` / `data_js_bytes`. Descriptions must contain no
   `"` and no `&`. The model name must be **unique across the whole catalogue**, or `DUP_NAMES`
   retroactively rewrites the existing watch's title in all three languages.
3. `python tools/make_shells.py <id>` from `mina.github.io/`.
4. The generator chain above, in order. **`gen_blog_index.py` included.**
5. **Fix the prose the count broke.** Everything generated heals itself; article and service
   prose does not.

Nothing needs a cache-bust: the `watches-data.js?v=` requirement died with the runtime renderer.

---

## The lanes

Work is divided between agents in `../.claude/agents/`: `shop` `blog` `funnel` `seo` `ui` `lang`
`verify`, each owning a file set no other lane writes. Five derived regions are written by a lane
that does not own the surrounding file, which is correct rather than a conflict.

**An article declares a CTA role, never a watch.** `data-cta-role="battery"` on the bridge box is
the editorial decision and it is authored once; `gen_article_cta.py` picks the watch that fits
that role out of `watches.json` on every build, so a sell-out re-points the article and an
arrival can win the slot back.

**Agents stop at green gates.** They run the gates that cover their surface, report the exact
output, and leave committing and pushing to the owner.

Who owns what, the five derived regions in full, and why the rotation is anchored on price
rather than a list index: `docs/reference/lanes.md`.
