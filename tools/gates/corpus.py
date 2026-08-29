# [PERF-004] corpus.py — read the 605-file corpus once, not fifteen times.
# DOES:   Caches the sorted HTML file list and every file's bytes, plus the two decodes every
#         gate does downstream. Nothing else.
# IN:     Nothing. BASE resolves to the repo from this file's own location.
# OUT:    html_files() -> tuple[Path], sorted. raw(p) -> bytes. sig(p) -> str (utf-8-sig).
# WHY:    Measured 2026-08-30: the 8 gates performed ~13,000 file opens over 848 unique files,
#         a redundancy factor of ~15. verify-sitemap.py alone made nine near-full passes;
#         verify-stats.py ran the same rglob with the same prefilter twice, 88 lines apart.
#         The tree lives in OneDrive, where every open() traverses a sync placeholder, so the
#         cost is I/O, not regex.
# NOTES:  CACHES BYTES, NOT TEXT. Fifteen of the nineteen corpus passes are literally
#         rglob("*.html") + read_bytes(); the six different decodes downstream
#         (utf-8-sig, utf-8, errors=replace, errors=ignore) are all pure functions of the same
#         bytes and cost microseconds once those bytes are in RAM. Caching text would need one
#         cache per decode and would still re-read the file.
#         SORTED ORDER IS LOAD-BEARING and must never become a plain rglob: finding text is
#         compared byte-for-byte against a baseline, and verify-sitemap's broken-link report
#         cuts off at 30 entries, so order decides WHICH 30 are shown.
#         Safe only because every gate is read-only, which their headers state and the lane
#         rules require. If a writer ever runs in the same process, call invalidate() after it.
from functools import lru_cache
from pathlib import Path

BASE = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def html_files():
    """Every .html in the repo, sorted. One directory walk per process."""
    return tuple(sorted(BASE.rglob("*.html")))


@lru_cache(maxsize=1)
def all_files():
    """Every file, sorted. verify-contact walks this and filters by suffix itself."""
    return tuple(sorted(p for p in BASE.rglob("*") if p.is_file()))


@lru_cache(maxsize=None)
def raw(p):
    return Path(p).read_bytes()


@lru_cache(maxsize=None)
def sig(p):
    """utf-8-sig decode, by far the most common form in these gates."""
    return raw(p).decode("utf-8-sig")


def invalidate():
    """Drop everything. Only needed if a writer runs in the same process as a reader."""
    for f in (html_files, all_files, raw, sig):
        f.cache_clear()


def stats():
    return {"listing": html_files.cache_info(), "raw": raw.cache_info(), "sig": sig.cache_info()}
