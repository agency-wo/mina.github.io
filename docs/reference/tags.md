# The `[TAG-NNN]` index - format reference

Moved out of CLAUDE.md 2026-08-30: this is specification, not rule. The rules that used to
sit here stayed behind - never allocate a number by eye, and adding a tag is comment-only
work that must be proven.


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
and the generated pages generally. `shared.js` is minified so it gets a file header only.

**Adding a tag is comment-only work.** Prove it the way commit `8120eec` did: `ast.parse` every
`.py`, `node --check` every `.js`, then re-run all the generators and confirm each reports
SKIP / Unchanged / `Written: 0`.

