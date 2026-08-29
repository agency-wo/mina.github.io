#!/usr/bin/env python3
# [ERR-015] verify-chain.py — a generator that is not in the chain fails the build.
# DOES:   Asserts tools/sync_stock.GENERATORS lists every gen_*.py on disk, in CLAUDE.md's
#         dependency order, with gen_sitemap.py last.
# IN:     no args.  OUT: CHAIN GATE PASS, or exit 1 with findings.
# WHY:    Ported from MINA RANK/.build, whose build.py records the incident this prevents:
#         "the order lived in a document and in whatever loop somebody typed that afternoon,
#         and on 27 August 2026 the loop ran 10 of the 11. gen_launch was the omission, so
#         llms.txt went on describing the previous build for 5 days while every page carried a
#         fresh reading. Nothing failed. The gate was green, the pages were right, and the two
#         files written for AI assistants told them a number the site had retracted."
#         Not a wrong step - a MISSING one. That failure mode is live here too: this site's
#         chain is seven generators whose order is a hard dependency, and gen_blog_index has
#         already been left out once, shipping "50 of our 57 watches" after the count moved.
# NOTES:  GENERATORS in tools/sync_stock.py is the ONE source of truth, not a copy. The CI
#         workflow, the ship skill and CLAUDE.md all defer to it, so there is nothing to keep
#         in sync - which is the whole point, since two hand-synced lists is what this class of
#         bug is made of.
#         Order is asserted, not just membership: gen_brand_pages imports from gen_shop_index
#         so it must follow it, and gen_sitemap fingerprints page CONTENT to decide lastmod so
#         anything that rewrites HTML must precede it.
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE / "tools"))
from sync_stock import GENERATORS  # noqa: E402

findings = []


def flag(msg):
    findings.append(msg)
    print(f"  FINDING: {msg}")


def main():
    disk = sorted(p.name for p in BASE.glob("gen_*.py"))
    listed = list(GENERATORS)

    for g in disk:
        if g not in listed:
            flag(f"{g} exists but is not in sync_stock.GENERATORS - it would never run. "
                 f"Add it in dependency order, or delete it.")
    for g in listed:
        if g not in disk:
            flag(f"sync_stock.GENERATORS lists {g}, which is not on disk")

    if listed and listed[-1] != "gen_sitemap.py":
        flag(f"gen_sitemap.py must be LAST in the chain, not {listed[-1]}. It fingerprints page "
             f"content to decide lastmod, so every generator that rewrites HTML runs before it.")
    if "gen_shop_index.py" in listed and "gen_brand_pages.py" in listed:
        if listed.index("gen_brand_pages.py") < listed.index("gen_shop_index.py"):
            flag("gen_brand_pages.py must follow gen_shop_index.py - it imports card() and W "
                 "from it and clones the rendered shop index.")
    if "gen_blog_index.py" not in listed:
        flag("gen_blog_index.py is not in the chain. It must run on every catalogue change: the "
             "featured card carries {lolek}/{hilek} tokens only it resolves, and the rendered "
             "index has no data-stat marker for gen_stats to heal afterwards.")

    print(f"  {len(disk)} generators on disk | chain lists {len(listed)} | sitemap last: "
          f"{listed[-1] == 'gen_sitemap.py' if listed else False}")
    if findings:
        print(f"{len(findings)} FINDINGS")
        sys.exit(1)
    print("CHAIN GATE PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
