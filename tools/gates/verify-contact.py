#!/usr/bin/env python3
"""[ERR-013] verify-contact.py — the gate that keeps the call line and the WhatsApp line apart.
DOES:   five checks. A every tel: link and every JSON-LD "telephone" is the call
        line; B no call link shows any other number in its text; C every WhatsApp
        deep link on an en/ or it/ page (and on the English root pages) reaches
        that language's WhatsApp line; D each per-language shop.js builds its
        WhatsApp links on its own line and no other; E floors, so a sweep that
        escaped its scope cannot quietly empty an area.
IN:     python tools/gates/verify-contact.py, from the WORKING ROOT. No args.
        Read-only.
OUT:    "  FINDING: ..." per problem, a scanned/occurrence tally, then
        "CONTACT GATE PASS" or "<n> FINDINGS". Exit 1 on findings.
CALLS:  mina.github.io/contact.py for every number, so this gate and the
        generators cannot hold two opinions about which number belongs where.
NOTES:  The rule since 2026-11-06 (the owner): CALLS go to the shop's line,
        +355 67 636 0510, on every page, because the owner is in Italy for a long
        time and cannot take calls on his own number. WHATSAPP is unchanged: en/
        and it/ write to the owner, +355 67 571 6090, since the shop's line is the
        owner's father, who speaks only Albanian; sq/ writes to the father. The
        2026-08-16 rule, one number per language for both, is what checks A to C
        replace; its check "no Albanian number on an en/ or it/ page" would now
        fire on the call line, which is correct markup.
        The owner's number may still appear as text on en/ and it/ pages, in a
        sentence that says WhatsApp or "message us"; B keeps it out of call links,
        which is the place a visitor would dial it.
        sq/ may also carry the owner's WhatsApp: its home page and two legal pages
        list it as a secondary, WhatsApp-only contact, and 5 gift posts link it.
        That is not a finding.
        booking.js and stock-live.js are shared across the 3 languages and carry a
        per-language WhatsApp map keyed off <html lang>; C does not read them, D's
        sibling check below does.
"""
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
import corpus  # noqa: E402  - shared read cache, see [PERF-004]
ROOT = BASE.parent
sys.path.insert(0, str(BASE))
from contact import PHONE  # noqa: E402

CALL_TEL = {PHONE[k]["tel"] for k in PHONE}
assert len(CALL_TEL) == 1, "contact.py: the call line must be one number in every language"
CALL_TEL = CALL_TEL.pop()
CALL_TEXT = PHONE["en"]["text"]
EXT = (".html", ".js", ".txt", ".tpl", ".json", ".xml")
SHARED_JS = {"booking.js", "stock-live.js"}

TEL = re.compile(r'href="tel:([^"]*)"')
TEL_ANCHOR = re.compile(r'<a\b[^>]*href="tel:[^"]*"[^>]*>(.*?)</a>', re.S)
JSONLD_TEL = re.compile(r'"telephone"\s*:\s*"([^"]*)"')
WA_LINK = re.compile(r'(?:api\.whatsapp\.com/send\?phone=|wa\.me/)(\d+)')
NUMBER = re.compile(r"\+355 ?\d\d ?\d{3} ?\d{4}")

findings = []


# [ERR-013.a] flag — record one finding and print it as it is found ([ERR-007.a])
def flag(m):
    findings.append(m)
    print("  FINDING:", m)


# [ERR-013.b] normalise — collapse the entity spellings of a space
# NOTES:  the visible number is written "+355&thinsp;67&thinsp;636&thinsp;0510"
#         on 39 pages, and a plain-text scan does not see it. The 2026-08-16
#         sweep matched three literal spellings, missed this fourth one in 26
#         files, and left their visible FAQ copy disagreeing with its JSON-LD twin.
def normalise(text):
    for ent in ("&thinsp;", "&nbsp;", "&#8201;", "&#160;", " ", " "):
        text = text.replace(ent, " ")
    return text


def main():
    scanned = 0
    counts = {"tel": 0, "jsonld": 0, "wa": {"en": 0, "it": 0, "sq": 0, "root": 0}}
    wa_by_area = {"en": set(), "it": set(), "sq": set(), "root": set()}

    for p in corpus.all_files():
        if p.is_dir() or p.suffix.lower() not in EXT:
            continue
        rel = p.relative_to(BASE).as_posix()
        top = rel.split("/")[0]
        area = top if top in ("en", "it", "sq") else "root"
        text = normalise(p.read_text(encoding="utf-8-sig", errors="replace"))
        scanned += 1

        # A. every call link and every JSON-LD telephone is the call line
        for m in TEL.finditer(text):
            counts["tel"] += 1
            if m.group(1) != CALL_TEL:
                flag(f"{rel}: tel:{m.group(1)} is not the call line {CALL_TEL} (contact.py).")
        for m in JSONLD_TEL.finditer(text):
            counts["jsonld"] += 1
            if m.group(1).replace(" ", "") != CALL_TEL:
                flag(f'{rel}: JSON-LD "telephone" {m.group(1)} is not the call line {CALL_TEL}.')

        # B. a call link never shows another number
        for m in TEL_ANCHOR.finditer(text):
            inner = re.sub(r"<[^>]+>", " ", m.group(1))
            for shown in NUMBER.findall(inner):
                if shown.replace(" ", "") != CALL_TEL:
                    flag(f"{rel}: a call link shows {shown}; a call link shows {CALL_TEXT} or no number.")

        # C. WhatsApp on en/, it/ and the English root pages reaches that language's WhatsApp line
        if p.name in SHARED_JS:
            continue
        for m in WA_LINK.finditer(text):
            counts["wa"][area] += 1
            wa_by_area[area].add(m.group(1))
            want = PHONE["en" if area == "root" else area]["wa"]
            if area != "sq" and p.suffix.lower() == ".html" and m.group(1) != want:
                flag(f"{rel}: a WhatsApp link reaches {m.group(1)} on an {area} page; "
                     f"{area} writes to {want} (contact.py).")

    # D. each per-language shop.js builds WhatsApp links on its own line, and the shared JS maps agree
    for lang in ("en", "it", "sq"):
        p = BASE / lang / "shop" / "shop.js"
        if not p.exists():
            flag(f"{lang}/shop/shop.js is missing")
            continue
        found = set(WA_LINK.findall(p.read_text(encoding="utf-8-sig", errors="replace")))
        if found != {PHONE[lang]["wa"]}:
            flag(f"{lang}/shop/shop.js builds WhatsApp links on {sorted(found)}, not {PHONE[lang]['wa']}. "
                 f"It mirrors gen_shop_index.card() byte for byte, so fix both.")
    for name in sorted(SHARED_JS):
        t = (BASE / name).read_text(encoding="utf-8-sig", errors="replace")
        for lang in ("en", "it", "sq"):
            if not re.search(rf"\b{lang}\s*:\s*'{PHONE[lang]['wa']}'", t):
                flag(f"{name}: its per-language map does not give {lang} the WhatsApp line {PHONE[lang]['wa']}.")

    # E. floors: every area still carries its WhatsApp line, and the site still has call links
    for area in ("en", "it", "sq"):
        if PHONE[area]["wa"] not in wa_by_area[area]:
            flag(f"{area}/ has no WhatsApp link to {PHONE[area]['wa']} left. A sweep has escaped its "
                 f"scope. Do not 'fix' this by editing the gate.")
    if not counts["tel"]:
        flag("no tel: link anywhere: the call line has vanished from the site.")

    w = counts["wa"]
    print(f"\n  {scanned} files scanned | call links {counts['tel']}, JSON-LD telephone {counts['jsonld']}, all "
          f"{CALL_TEXT} | WhatsApp links en {w['en']}, it {w['it']}, sq {w['sq']}, root {w['root']}")
    if findings:
        print(f"{len(findings)} FINDINGS")
        sys.exit(1)
    print("CONTACT GATE PASS")


if __name__ == "__main__":
    main()
