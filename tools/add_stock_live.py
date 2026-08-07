#!/usr/bin/env python3
# [UI-003] add_stock_live.py — one-shot: mount stock-live.js on product pages.
# DOES:   Adds <script src="/stock-live.js?v=1" defer> after shared.js on every
#         {lang}/shop/*.html EXCEPT index.html (shop.js merges live stock into
#         its own data — [UI-002]) and delivery.html (no watch on it). The two
#         legacy meta-refresh stubs self-exclude: they carry no shared.js.
# IN:     No args. Idempotent — pages already carrying the tag are skipped.
# OUT:    Rewrites files in place (BOM preserved); prints per-language counts.
#         Exits 1 if a candidate page has no shared.js anchor — surfaced, not
#         skipped silently.
# NOTES:  Brand pages get their tag from gen_brand_pages.py (they are
#         regenerated wholesale); new product pages inherit it because
#         make-new-watch-pages.py clones an existing page.
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ANCHOR = '<script src="/shared.js?v=23" defer></script>'
TAG = '\n  <script src="/stock-live.js?v=1" defer></script>'

def main():
    missing = []
    for lang in ("en", "sq", "it"):
        changed = already = stubs = 0
        for p in sorted((BASE / lang / "shop").glob("*.html")):
            if p.name in ("index.html", "delivery.html"):
                continue
            raw = p.read_bytes()
            bom = raw.startswith(b"\xef\xbb\xbf")
            txt = raw.decode("utf-8-sig")
            if "/stock-live.js" in txt:
                already += 1
                continue
            if ANCHOR not in txt:
                if "shared.js" in txt:
                    missing.append(str(p))     # anchor drifted — surface it
                else:
                    stubs += 1                 # legacy meta-refresh stub
                continue
            txt = txt.replace(ANCHOR, ANCHOR + TAG, 1)
            p.write_bytes((b"\xef\xbb\xbf" if bom else b"") + txt.encode("utf-8"))
            changed += 1
        print(f"{lang}: changed {changed}, already {already}, stubs {stubs}")
    for p in missing:
        print("MISSING shared.js anchor:", p)
    sys.exit(1 if missing else 0)

if __name__ == "__main__":
    main()
