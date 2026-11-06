#!/usr/bin/env python3
"""[CFG-010] contact.py — the one home for the shop's phone numbers, per language.
DOES:   maps a page language to the spellings of the two lines it shows: the
        CALL line (tel:, JSON-LD "telephone", and its visible text) and the
        WHATSAPP line (the deep-link parameter and its visible text). Data only,
        no I/O, no derivation.

contact.py
There are two numbers, and since 2026-11-06 which one a page shows depends on
what the visitor is doing, calling or writing.

The father's line, +355 67 636 0510, is the shop's phone. He speaks only
Albanian. The owner's line, +355 67 571 6090, runs WhatsApp Business.

RULE (the owner, 2026-11-06): CALLS go to +355 67 636 0510 on every page, in
every language, because the owner is in Italy for a long time and cannot take
calls on his own number. WHATSAPP stays as it was: en/ and it/ write to the
owner (an English or Italian visitor writing to the father reaches somebody who
cannot answer them), sq/ writes to the father. Before 2026-11-06 en/ and it/
showed the owner's number for both; that was the 2026-08-16 rule.
There is no default: an unknown language raises rather than guessing, because
guessing here sends a customer to the wrong person.

The forms are not interchangeable and all four are in use:
  tel      +CC form of the call line, for href="tel:..." and JSON-LD "telephone"
  text     the spaced form of the call line a human reads, next to a call link
  wa       digits only of the WhatsApp line, for https://api.whatsapp.com/send?phone=...
  wa_text  the spaced form of the WhatsApp line, in a sentence that says WhatsApp

NOTES:  the JS side cannot import this. {en,it,sq}/shop/shop.js are per-language
        files and carry their own literal; booking.js and stock-live.js are
        shared and pick the number off <html lang>, the same way they already
        pick their strings. scripts/verify-contact.py reads THIS file and proves
        every page agrees with it, so the literals cannot drift back.
"""

_CALL = {"tel": "+355676360510", "text": "+355 67 636 0510"}   # the shop's phone, every language
PHONE = {
    # English and Italian: calls to the shop, WhatsApp to the owner (WhatsApp Business runs on it).
    "en": {**_CALL, "wa": "355675716090", "wa_text": "+355 67 571 6090"},
    "it": {**_CALL, "wa": "355675716090", "wa_text": "+355 67 571 6090"},
    # Albanian: the father's line for both.
    "sq": {**_CALL, "wa": "355676360510", "wa_text": "+355 67 636 0510"},
}


# [CFG-010.a] phone — the four spellings for one language
# IN:     lang — "en" | "it" | "sq"
# OUT:    {"tel": ..., "text": ..., "wa": ..., "wa_text": ...}
# NOTES:  raises on anything else. A fallback would silently route a customer to
#         the wrong person, which is the exact failure this module exists to end.
def phone(lang):
    try:
        return PHONE[lang]
    except KeyError:
        raise KeyError(f"contact.phone: no number for language {lang!r}; "
                       f"known languages are {sorted(PHONE)}")


# [CFG-010.b] wa_link — the WhatsApp deep link for one language, message unencoded
# IN:     lang; msg — the prefilled text, already URL-encoded by the caller
# OUT:    the full https://api.whatsapp.com/send?phone=...&text=... URL
# NOTES:  amp is "&amp;" for callers writing straight into HTML and "&" for the
#         ones building a URL in code. Both spellings exist in the generators.
def wa_link(lang, msg="", amp="&"):
    return f"https://api.whatsapp.com/send?phone={phone(lang)['wa']}{amp}text={msg}"
