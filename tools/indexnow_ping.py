# [API-007] indexnow_ping.py — tell Bing and the other IndexNow engines which pages just changed.
# DOES:   Reads sitemap.xml, takes every URL whose <lastmod> is today or yesterday (UTC; a page
#         dated "tomorrow" by the Albanian build counts too), and sends them in ONE POST to
#         api.indexnow.org with the site's key, falling back to yandex.com when it is refused
#         (see ENDPOINTS).
# IN:     `python tools/indexnow_ping.py [--dry-run] [--days N]` from mina.github.io/. Run by
#         .github/workflows/indexnow.yml after every GitHub Pages build.
# OUT:    one line saying what was sent and the engine's answer. ALWAYS exits 0.
# WHY:    Bing Webmaster's own home page recommends "Set up IndexNow". The key file has been at
#         the site root since 2026-05-17 (587f5ca) and nothing ever pinged. On 2026-11-16 Search
#         Console listed 19 in-stock watches (57 product pages) Google had discovered and never
#         crawled, and Bing is the engine still sending searches after the 2026-09-07 drop.
#         Google does not read IndexNow; Bing, Yandex, Seznam and Naver do, and Bing feeds
#         ChatGPT and Copilot search.
# NOTES:  gen_sitemap.py moves <lastmod> only when a page's content fingerprint changes, so the
#         window is exactly the changed pages, and noindex pages are never in the sitemap. One
#         request, not one per URL: elsewhere in this workspace a GET per URL never finished.
#         NON-FATAL BY DESIGN: a ping is a hint, never a gate, so every failure is a printed
#         sentence and exit 0.
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
HOST = "watch.al"
# Tried in order until one accepts. The engines share what they receive with each other. On 2026-11-16
# api.indexnow.org and bing.com answered 403 "UserForbiddedToAccessSite" for this key while yandex.com accepted
# the same request ("success": true), so the key and its file are valid and Bing's side is the odd one out.
ENDPOINTS = ["https://api.indexnow.org/indexnow", "https://yandex.com/indexnow"]
URL_RE = re.compile(r"<url>\s*<loc>([^<]+)</loc>(.*?)</url>", re.S)
LASTMOD_RE = re.compile(r"<lastmod>(\d{4}-\d{2}-\d{2})")


def find_key():
    """[API-007.a] the key is the root .txt file named after its own 32-hex content"""
    for p in BASE.glob("*.txt"):
        stem = p.stem
        if re.fullmatch(r"[0-9a-f]{32}", stem) and p.read_text(encoding="utf-8").strip() == stem:
            return stem
    return None


def changed_urls(days):
    """[API-007.b] sitemap URLs whose lastmod falls in the window (today minus `days`, or later)"""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    text = (BASE / "sitemap.xml").read_text(encoding="utf-8-sig")
    out = []
    for loc, body in URL_RE.findall(text):
        m = LASTMOD_RE.search(body)
        if m and m.group(1) >= cutoff and loc.startswith("https://" + HOST + "/"):
            out.append(loc.strip())
    return out


def main(argv):
    dry = "--dry-run" in argv
    days = int(argv[argv.index("--days") + 1]) if "--days" in argv else 1
    key = find_key()
    if not key:
        print("indexnow: no key file at the site root; nothing sent")
        return 0
    urls = changed_urls(days)[:10000]          # the protocol's limit per request
    if not urls:
        print(f"indexnow: no page changed in the last {days + 1} days; nothing sent")
        return 0
    if dry:
        print(f"indexnow: dry run, would send {len(urls)} URLs, e.g. {urls[:3]}")
        return 0
    body = json.dumps({"host": HOST, "key": key, "keyLocation": f"https://{HOST}/{key}.txt",
                       "urlList": urls}).encode("utf-8")
    for endpoint in ENDPOINTS:
        req = urllib.request.Request(endpoint, data=body, method="POST",
                                     headers={"Content-Type": "application/json; charset=utf-8",
                                              "User-Agent": "watch.al-indexnow/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                print(f"indexnow: sent {len(urls)} URLs to {endpoint}, answer {r.status}")
                return 0
        except urllib.error.HTTPError as e:
            detail = e.read(200).decode("utf-8", "replace") if e.fp else ""
            print(f"indexnow: {endpoint} refused {e.code} {detail}")
        except Exception as e:                  # network down, DNS, timeout: a hint lost, not a failure
            print(f"indexnow: {endpoint} not reached ({type(e).__name__}: {e})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
