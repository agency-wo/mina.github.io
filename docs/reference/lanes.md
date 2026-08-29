# The lanes, and why the CTA rotation works the way it does

Moved out of CLAUDE.md 2026-08-30. The two RULES that lived in this section stayed behind:
an article declares a CTA role and never a watch, and agents stop at green gates.


Work is divided between agents in `../.claude/agents/`. Each owns a file set no other lane writes.

`shop` · catalogue and buying path — `blog` · the articles — `funnel` · homepages, services,
about, b2b, delivery, legal — `seo` · sitemap, stats, llms.txt, robots, FAQ, schema — `ui` ·
`shared.css`, chrome, glyphs, assets (CSS-only) — `lang` · all Italian and Albanian prose —
`verify` · the gates.

Five **derived regions** are written by a lane that does not own the surrounding file, and this is
correct rather than a conflict: `gen_stats.py` owns what is inside a `data-stat` span, `ui` owns the
`?v=` cache-bust sweep, `verify` owns the CSP meta, `faq-build.py` owns both copies of a FAQ
answer, and `gen_article_cta.py` owns the button inside an article's `data-shop-bridge` box. In each
case a second writer can only produce a stale value, never a conflicting one.

**An article declares a CTA role, never a watch.** `data-cta-role="battery"` on the bridge box is the
editorial decision and it is authored once; `gen_article_cta.py` picks the watch that currently fits
that role out of `watches.json` on every build, so a sell-out re-points the article and an arrival can
win the slot back. Writing a watch id into every bridge box would have created one more thing to go stale the
first time one of them sold. The rotation is anchored on PRICE rather than on a list index: an index
shifts for every article when any watch sells, and a test doing exactly that moved 30 articles and
would have churned 90 sitemap lastmod dates for a stock change.

**Agents stop at green gates.** They run the gates that cover their surface, report the exact
output, and leave committing and pushing to the owner.
