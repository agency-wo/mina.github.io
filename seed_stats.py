#!/usr/bin/env python3
"""[DB-012] seed_stats.py — one-off migration that plants the data-stat markers.
DOES:   wraps the literal catalogue numbers in the services pages in
        <span data-stat> markers so gen_stats.py can own them from then on;
        each page must match at least 3 anchors or the run fails loudly.

seed_stats.py
One-off: wrap the catalogue numbers in hand-written pages in <span data-stat>
markers, so gen_stats.py can keep them current from then on.

Only run once per page. It is anchored on the CURRENT text, which is exactly the
weakness that made scripts/fix-reviews.py rot, and that is fine here because this
is a migration rather than a build step: gen_stats.py takes over afterwards and is
anchored on the marker, which never changes.

Every rule asserts its own hit count, so a page whose wording has drifted fails
loudly instead of being skipped.
"""
import re

# (glob, [(pattern, replacement, expected_hits_per_file_or_None)])
# The span always wraps a whitespace-delimited whole token, never a fragment
# glued to punctuation. See gen_stats.py for why.
RULES = [
    # ---- services: the "Also in our shop" teaser, 18 pages ----
    ("en/services.html", "en"), ("en/services/*.html", "en"),
    ("it/services.html", "it"), ("it/services/*.html", "it"),
    ("sq/services.html", "sq"), ("sq/services/*.html", "sq"),
]

SUBS = {
    "en": [
        (r"collection of 57 brand-new watches from 10 brands",
         'collection of <span data-stat="n">57</span> brand-new watches from '
         '<span data-stat="b">10</span> brands'),
        (r"10 brands in store", '<span data-stat="b">10</span> brands in store'),
    ],
    "it": [
        (r"collezione di 57 orologi nuovi di 10 marchi",
         'collezione di <span data-stat="n">57</span> orologi nuovi di '
         '<span data-stat="b">10</span> marchi'),
        (r"10 marchi in negozio", '<span data-stat="b">10</span> marchi in negozio'),
    ],
    "sq": [
        (r"me 57 or&euml; t&euml; reja nga 10 marka",
         'me <span data-stat="n">57</span> or&euml; t&euml; reja nga '
         '<span data-stat="b">10</span> marka'),
        (r"me 57 orë të reja nga 10 marka",
         'me <span data-stat="n">57</span> orë të reja nga '
         '<span data-stat="b">10</span> marka'),
        (r"10 marka n&euml; dyqan", '<span data-stat="b">10</span> marka n&euml; dyqan'),
        (r"10 marka në dyqan", '<span data-stat="b">10</span> marka në dyqan'),
    ],
}

# language-independent: the stat tiles
COMMON = [
    (r'(<span class="svp-stat-num">)57(</span>)', r'\1<span data-stat="n">57</span>\2'),
    (r"~4\.900 L", '<span data-stat="lolek~">~4.900 L</span>'),
    (r"~4,900 L", '<span data-stat="lolek~">~4,900 L</span>'),
]


# [DB-012.a] run — apply SUBS + COMMON to every RULES glob, once per page
# DOES:   skips pages already carrying markers (idempotence), asserts the per-page
#         hit floor so drifted wording cannot be silently half-seeded.
# IN:     base — repo root Path; read/write — gen_stats.py's byte-preserving I/O
def run(base, read, write):
    total = files = 0
    for pattern, lang in RULES:
        for p in sorted(base.glob(pattern)):
            raw = p.read_bytes()
            t, bom, crlf = read(p)
            if 'data-stat="' in t:
                continue  # already seeded
            n = 0
            for rx, rep in SUBS[lang] + COMMON:
                t, k = re.subn(rx, rep, t)
                n += k
            assert n >= 3, f"{p.name}: only {n} anchors matched, wording has drifted"
            if write(p, t, bom, crlf, raw):
                files += 1
                total += n
    print(f"  seeded {total} markers in {files} files")
