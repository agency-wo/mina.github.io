#!/usr/bin/env python3
# [SEC-002] update_csp.py — one-shot: allow api.watch.al in connect-src.
# DOES:   Inserts https://api.watch.al right after connect-src 'self' in every
#         page's <meta http-equiv="Content-Security-Policy"> AND in _headers,
#         so the live stock layer ([UI-001]/[UI-002]) may fetch the CRM feed.
# IN:     No args; operates on the repo this file lives in. Idempotent — a
#         second run is a no-op.
# OUT:    Rewrites files in place (UTF-8, BOM preserved where present) and
#         prints changed/skipped counts. Exits 1 if any file that carries a
#         connect-src still lacks api.watch.al afterwards — no silent misses.
# NOTES:  This site pins its CSP per page (478 files) + _headers, so one new
#         origin touches all of them; that is the price of the per-page pin.
#         Contract: part-tracker repo, docs/CRM_SYNC.md.
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
NEEDLE = "connect-src 'self' "
INSERT = "https://api.watch.al "

def process(p: Path) -> str:
    raw = p.read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    txt = raw.decode("utf-8-sig")
    if "connect-src" not in txt:
        return "no-csp"
    seg = txt.split("connect-src", 1)[1].split(";", 1)[0]
    if "https://api.watch.al" in seg:
        return "already"
    if NEEDLE not in txt:
        return "ODD"          # a connect-src that doesn't start with 'self' — surfaced, never guessed
    txt = txt.replace(NEEDLE, NEEDLE + INSERT)
    p.write_bytes((b"\xef\xbb\xbf" if bom else b"") + txt.encode("utf-8"))
    return "changed"

def main():
    counts = {"changed": 0, "already": 0, "no-csp": 0, "ODD": 0}
    odd = []
    targets = sorted(BASE.rglob("*.html")) + [BASE / "_headers"]
    for p in targets:
        if not p.is_file():
            continue
        r = process(p)
        counts[r] += 1
        if r == "ODD":
            odd.append(str(p))
    print(f"changed: {counts['changed']}  already: {counts['already']}  "
          f"no-csp: {counts['no-csp']}  odd: {counts['ODD']}")
    for p in odd:
        print("ODD (connect-src without leading 'self'):", p)
    sys.exit(1 if odd else 0)

if __name__ == "__main__":
    main()
