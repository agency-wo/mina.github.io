#!/usr/bin/env python3
"""[ERR-013] verify-contact.py — the gate that keeps the two phone numbers apart.
DOES:   four checks. A no en/ or it/ page carries the Albanian number; B the
        Albanian number is still present under sq/, so an over-broad sweep cannot
        quietly wipe it; C each per-language shop.js carries only its own number;
        D no root file outside a named allowlist carries the Albanian number.
IN:     python tools/gates/verify-contact.py, from the WORKING ROOT. No args.
        Read-only.
OUT:    "  FINDING: ..." per problem, a scanned/occurrence tally, then
        "CONTACT GATE PASS" or "<n> FINDINGS". Exit 1 on findings.
CALLS:  mina.github.io/contact.py for both numbers, so this gate and the
        generators cannot hold two opinions about which number belongs where.
NOTES:  Two numbers, and which one a page shows is a language question. The
        Albanian line is the owner's father, who speaks only Albanian, so an
        English or Italian visitor reaching it reaches somebody who cannot serve
        them. That was true on 4,208 occurrences until 2026-08-16.
        Check A is the one that matters and it is one-directional on purpose.
        The reverse is NOT a finding: sq/ legitimately carries the owner's number
        as a labelled SECONDARY contact on sq/index.html and the two sq legal
        pages, and did so before any of this. Flagging that would fire on correct
        markup, and a gate that fires on correct markup gets ignored.
        Check B exists because check A can be satisfied by deleting the number
        everywhere, which would be a much worse outcome than the bug. A floor of
        one occurrence under sq/ is enough to catch a sweep that escaped scope.
        Check D's allowlist is named files, never a blanket root skip, so a new
        root page cannot inherit the wrong number unnoticed. booking.js and
        stock-live.js are shared across all three languages and carry a per-
        language map keyed off <html lang>; llms.txt and its template list both
        numbers labelled, because AI answer engines read that one English file
        and then answer in Albanian too; contact.py is the authority itself.
"""
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
import corpus  # noqa: E402  - shared read cache, see [PERF-004]
ROOT = BASE.parent
sys.path.insert(0, str(BASE))
from contact import PHONE  # noqa: E402

SQ = PHONE["sq"]
EN = PHONE["en"]
# longest first, so the bare digits are never counted inside the +CC form
FORMS = ("text", "tel", "wa")
EXT = (".html", ".js", ".txt", ".tpl", ".json", ".xml")

# Root files that may legitimately name the Albanian number. Named, not globbed:
# a new root page must be considered rather than inherit an exemption.
ROOT_ALLOW = {"contact.py", "booking.js", "stock-live.js", "llms.txt", "llms.tpl"}

findings = []


# [ERR-013.a] flag — record one finding and print it as it is found ([ERR-007.a])
def flag(m):
    findings.append(m)
    print("  FINDING:", m)


# [ERR-013.b] normalise — collapse the entity spellings of a space
# NOTES:  the visible number is written "+355&thinsp;67&thinsp;636&thinsp;0510"
#         on 39 pages, and a plain-text scan does not see it. That is not
#         hypothetical: the 2026-08-16 sweep matched three literal spellings,
#         missed this fourth one in 26 en/ and it/ files, and left their visible
#         FAQ copy disagreeing with the JSON-LD twin it had already changed.
#         faq-build.py caught it; this gate had said PASS. Normalising first is
#         what makes the count honest.
def normalise(text):
    for ent in ("&thinsp;", "&nbsp;", "&#8201;", "&#160;", " ", " "):
        text = text.replace(ent, " ")
    return text


# [ERR-013.c] hits — how many times one number appears in one file
# NOTES:  counts longest form first and removes it, so "+355676360510" is never
#         also counted as the bare "355676360510" sitting inside it.
def hits(text, num):
    text = normalise(text)
    n = 0
    for k in FORMS:
        n += text.count(num[k])
        text = text.replace(num[k], "")
    return n


def main():
    scanned = sq_total = 0

    for p in corpus.all_files():
        if p.is_dir() or p.suffix.lower() not in EXT:
            continue
        rel = p.relative_to(BASE).as_posix()
        lang = rel.split("/")[0]
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        scanned += 1
        n = hits(text, SQ)

        # A. the Albanian number must not appear on an English or Italian page
        if lang in ("en", "it") and n:
            flag(f"{rel}: carries the Albanian number ({SQ['text']}) {n}x on an "
                 f"{lang} page. {lang} reaches {EN['text']} — see contact.py.")

        # B. and it must still be present under sq/
        if lang == "sq":
            sq_total += n

        # D. root files, allowlisted by name
        if lang not in ("en", "it", "sq") and n and p.name not in ROOT_ALLOW:
            flag(f"{rel}: root file carries the Albanian number ({SQ['text']}) "
                 f"{n}x and is not in ROOT_ALLOW. Decide which language it "
                 f"serves, then either fix it or add it to the allowlist.")

    if not sq_total:
        flag(f"the Albanian number ({SQ['text']}) has vanished from sq/ "
             f"entirely. It is the primary contact there; a sweep has escaped "
             f"its scope. Do not 'fix' this by editing the gate.")

    # C. each per-language shop.js carries its own number and no other
    for lang in ("en", "it", "sq"):
        p = BASE / lang / "shop" / "shop.js"
        if not p.exists():
            flag(f"{lang}/shop/shop.js is missing")
            continue
        text = p.read_text(encoding="utf-8-sig", errors="replace")
        want, other = PHONE[lang], PHONE["sq" if lang != "sq" else "en"]
        if not hits(text, want):
            flag(f"{lang}/shop/shop.js does not carry {want['text']}")
        if want["wa"] != other["wa"] and hits(text, other):
            flag(f"{lang}/shop/shop.js carries {other['text']}, which belongs to "
                 f"another language. It mirrors gen_shop_index.card() byte for "
                 f"byte, so fix both or the grid changes after hydration.")

    print(f"\n  {scanned} files scanned | Albanian number: 0 under en/ and it/, "
          f"{sq_total} under sq/ | root allowlist: {len(ROOT_ALLOW)}")
    if findings:
        print(f"{len(findings)} FINDINGS")
        sys.exit(1)
    print("CONTACT GATE PASS")


if __name__ == "__main__":
    main()
