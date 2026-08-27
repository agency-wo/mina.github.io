# [UTIL-009] make_shells.py — rebuild a product page shell from the template.
# DOES:   For each id given, clones {en,it,sq}/shop/<TPL_ID>.html and swaps the
#         SEO-bearing head values (description, name, sku, brand, slug, EUR + Lek
#         JSON-LD price, og product:price:amount) so the static <head> already
#         agrees with what gen_product_pages.py will later render into the body.
# IN:     ensure_shells(ids) or `python tools/make_shells.py <id> [...]`. The watch
#         must already be in watches.json: descriptions, price and reference are
#         read from it.
# OUT:    writes {lang}/shop/{id}.html with the TEMPLATE'S OWN BOM and line endings.
#         Overwrites, so re-running is safe. Creates the shell only; the generator
#         chain still has to run afterwards.
# WHY THIS EXISTS INSIDE THE REPO. scripts/make-new-watch-pages.py does the same job
#         but lives OUTSIDE the git repo, so CI cannot reach it. Restoring an
#         archived watch needs exactly this: gen_product_pages refuses to patch a
#         redirect stub back into a full page (it needs #watch-content, which a stub
#         has none of) and prints "rebuild those shells, then rerun". With the
#         builder outside the repo, an archive/restore done from the admin panel
#         stopped there and needed someone at a terminal. Now it does not.
# NOTES:  Byte shape is MIRRORED, never assumed: write_text's default newline once
#         translated LF to CRLF and left five pages CRLF in an LF tree.
#         lek() keeps the half-up formula locally but takes the RATE from
#         catalog_stats, which is its one home. A writer with its own copy of the
#         rate publishes prices from a second opinion, and the 97 -> 92.25 change is
#         exactly the event that would have shipped stale Lek into every new page.
#         Plain round() is banker's and disagrees wherever the product lands on an
#         exact .5: EUR 200 at 92.25.
#         The template is a HAND-TUNED page. If daniel-klein-blue is ever retired,
#         repoint every TPL_* constant first or the next shell ships carrying
#         another watch's schema.
import json
import re
import sys
from pathlib import Path

BOM = b"\xef\xbb\xbf"
BASE = Path(__file__).resolve().parent.parent
LANGS = ("en", "it", "sq")

sys.path.insert(0, str(BASE))
from catalog_stats import LEK_RATE  # noqa: E402

TPL_ID = "daniel-klein-blue"
TPL_NAME = "Daniel Klein Blue"
TPL_SKU = "DK 1.12576.2"
TPL_BRAND = "Daniel Klein"
TPL_PRICE = "64"
TPL_ALL = "6200"

# The four renderers of this string must agree byte for byte.
# shop_bits.PRICE_ON_REQUEST is the home; this copy exists because the module is
# imported by tools that run before the generators.
POR = {"en": "Price on request", "it": "Prezzo su richiesta",
       "sq": "Çmimi me kërkesë"}


def lek(price):
    """Half-up, NOT Python's banker's round(), matching every other renderer."""
    return int(price * LEK_RATE / 100 + 0.5) * 100


def drop_offers(s):
    """Remove the whole "offers":{...} object (nested braces) plus its leading comma.

    A priceless watch ships a Product with no Offer at all rather than a fabricated
    price; schema.org allows it and verify-product-pages has no offers assertion."""
    i = s.index('"offers":{')
    j = s.index("{", i)
    depth = 0
    for k in range(j, len(s)):
        if s[k] == "{":
            depth += 1
        elif s[k] == "}":
            depth -= 1
            if depth == 0:
                break
    start = i - 1 if s[i - 1] == "," else i
    return s[:start] + s[k + 1:]


def is_stub(path):
    """A redirect stub, not a product page: gen_product_pages keys off the same
    marker, so the two agree about what needs rebuilding."""
    if not path.exists():
        return True
    return 'id="watch-content"' not in path.read_text(encoding="utf-8-sig")


def ensure_shells(ids, watches=None, verbose=True):
    """Write a fresh shell for each id. Returns the list of paths written."""
    if watches is None:
        watches = json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))
    by_id = {w["id"]: w for w in watches}
    tpl = by_id[TPL_ID]
    written = []

    for wid in ids:
        w = by_id[wid]
        name = f'{w["brand"]} {w["model"]}'.strip()
        price = str(w["price"]) if w.get("price") else ""
        all_price = str(lek(w["price"])) if w.get("price") else ""
        ref = w.get("reference", "")

        for lang in LANGS:
            src = BASE / lang / "shop" / f"{TPL_ID}.html"
            raw = src.read_bytes()
            bom = raw.startswith(BOM)
            eol = "\r\n" if b"\r\n" in raw else "\n"
            s = raw.decode("utf-8-sig").replace("\r\n", "\n")

            # 1. description -> head meta/og/json-ld + body
            s = s.replace(tpl[f"description_{lang}"], w[f"description_{lang}"])
            # 2. product name -> title, og:title, JSON-LD name, breadcrumb name
            s = s.replace(TPL_NAME, name)
            # 3. sku: swap when we have a reference, else drop the field
            if ref:
                s = s.replace(f'"sku":"{TPL_SKU}"', f'"sku":"{ref}"')
            else:
                s = s.replace(f'"sku":"{TPL_SKU}",', "")
            # 4. brand, only when different
            if w["brand"] != TPL_BRAND:
                s = s.replace(f'"name":"{TPL_BRAND}"', f'"name":"{w["brand"]}"')
            # 5. slug -> canonical/hreflang/og:url/og:image/JSON-LD url+image/breadcrumb
            s = s.replace(TPL_ID, wid)
            if price:
                # 6. prices (quoted JSON-LD forms only)
                s = s.replace(f'"price":"{TPL_PRICE}"', f'"price":"{price}"')
                s = s.replace(f'"price":"{TPL_ALL}"', f'"price":"{all_price}"')
                # 7. Open Graph product price meta
                s = s.replace(
                    f'property="product:price:amount" content="{TPL_PRICE}"',
                    f'property="product:price:amount" content="{price}"')
            else:
                # priceless: no fabricated figure anywhere
                s = s.replace(f" - €{TPL_PRICE} | ", " | ")
                s = drop_offers(s)
                s = re.sub(r'[ \t]*<meta property="product:price:(?:amount|currency)"[^>]*>\n',
                           "", s)
                s = re.sub(r'(class="watch-price-pg">).*?(</p>)',
                           r"\g<1>" + POR[lang] + r"\g<2>", s)

            dest = BASE / lang / "shop" / f"{wid}.html"
            dest.write_bytes((BOM if bom else b"") + s.replace("\n", eol).encode("utf-8"))
            written.append(dest)
            if verbose:
                print(f"  shell: {lang}/shop/{wid}.html  ({name}, €{price or 'on request'})")
    return written


def restore_missing(watches=None, verbose=True):
    """Rebuild a shell for every LIVE watch whose page is still a stub.

    This is the restore leg: clearing `deleted` puts the watch back in the
    catalogue, but its page is still the redirect stub archiving left behind, and
    gen_product_pages will not patch a stub into a full page. Called by
    sync_stock before the generators run so a restore completes by itself.
    """
    if watches is None:
        watches = json.loads((BASE / "watches.json").read_text(encoding="utf-8-sig"))
    need = [w["id"] for w in watches
            if not w.get("deleted")
            and any(is_stub(BASE / lg / "shop" / f'{w["id"]}.html') for lg in LANGS)]
    if not need:
        return []
    if verbose:
        print(f"  rebuilding {len(need)} shell(s) for restored watches: {need}")
    return ensure_shells(need, watches, verbose)


if __name__ == "__main__":
    ids = sys.argv[1:]
    if ids:
        ensure_shells(ids)
    else:
        n = restore_missing()
        print("nothing to rebuild" if not n else f"rebuilt {len(n)} page(s)")
