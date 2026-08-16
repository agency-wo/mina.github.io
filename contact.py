#!/usr/bin/env python3
"""[CFG-010] contact.py — the one home for the shop's phone number, per language.
DOES:   maps a page language to the three spellings of the number that language
        must show: the WhatsApp deep-link parameter, the tel:/JSON-LD form, and
        the visible text. Data only, no I/O, no derivation.

contact.py
There are two numbers, and which one a page shows is a language question.

The Albanian line, +355 67 636 0510, is the owner's father. He speaks only
Albanian. Every English or Italian visitor who reached it, through the floating
WhatsApp button, a watch enquiry, the call bar or a blog CTA, reached somebody
who could not serve them, so en/ and it/ now reach the owner's own line instead.

RULE: sq/ keeps the father's number. en/ and it/ get the owner's. Nothing else
is a judgement call, and there is no default: an unknown language raises rather
than guessing, because guessing here sends a customer to the wrong person.

The three forms are not interchangeable and all three are in use:
  wa    digits only, for https://api.whatsapp.com/send?phone=...
  tel   +CC form, for href="tel:..." and the LocalBusiness JSON-LD "telephone"
  text  the spaced form a human reads on the page

NOTES:  the JS side cannot import this. {en,it,sq}/shop/shop.js are per-language
        files and carry their own literal; booking.js and stock-live.js are
        shared and pick the number off <html lang>, the same way they already
        pick their strings. scripts/verify-contact.py reads THIS file and proves
        every page agrees with it, so the literals cannot drift back.
"""

PHONE = {
    # English and Italian: the owner's line. WhatsApp Business runs on it.
    "en": {"wa": "355675716090", "tel": "+355675716090", "text": "+355 67 571 6090"},
    "it": {"wa": "355675716090", "tel": "+355675716090", "text": "+355 67 571 6090"},
    # Albanian: the father's line, unchanged and deliberately so.
    "sq": {"wa": "355676360510", "tel": "+355676360510", "text": "+355 67 636 0510"},
}


# [CFG-010.a] phone — the three spellings for one language
# IN:     lang — "en" | "it" | "sq"
# OUT:    {"wa": ..., "tel": ..., "text": ...}
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
