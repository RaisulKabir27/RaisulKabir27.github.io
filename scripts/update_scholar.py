#!/usr/bin/env python3
"""
Refresh data/scholar.js with Google Scholar metrics for the portfolio site.

Why this exists: browsers cannot read Google Scholar directly (Google blocks
cross-site requests), so a scheduled GitHub Action runs this script every few
hours and commits the result. The page loads data/scholar.js as a plain script,
which also works when index.html is opened straight from disk.

Order of attempts:
  1. The public Scholar profile page (no key needed).
  2. SerpAPI's google_scholar_author endpoint, only if a SERPAPI_KEY secret is set.
If both fail, the existing file is left untouched and the run ends without error,
so the site keeps showing the last known numbers (including a number typed in by hand).

Standard library only: nothing to install.
"""
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SCHOLAR_USER = os.environ.get("SCHOLAR_USER", "ufPe9c8AAAAJ")
OUT_FILE = Path(__file__).resolve().parent.parent / "data" / "scholar.js"
HEADER = (
    "/* Google Scholar numbers for the portfolio. Rewritten automatically by\n"
    "   .github/workflows/deploy.yml; a failed fetch never overwrites it, so you can\n"
    "   also set \"citations\" by hand. */\n"
    "window.SCHOLAR_STATS = "
)
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
)


def get(url: str) -> str:
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"}
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "replace")


def clean(text: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip()


def to_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def parse_profile(page: str) -> dict:
    """Extract totals and per-article citations from a Scholar profile page."""
    cells = re.findall(r'<td class="gsc_rsb_std">(\d*)</td>', page)
    if len(cells) < 6:
        raise RuntimeError("metrics table not found (request blocked or page layout changed)")
    publications = []
    for row in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', page, re.S):
        title = re.search(r'class="gsc_a_at"[^>]*>(.*?)</a>', row, re.S)
        cites = re.search(r'class="gsc_a_ac[^"]*"[^>]*>(\d*)</a>', row)
        if title:
            publications.append(
                {"title": clean(title.group(1)), "citations": to_int(cites.group(1)) if cites else 0}
            )
    return {
        # Table order: citations (all, since), h-index (all, since), i10-index (all, since)
        "citations": to_int(cells[0]),
        "h_index": to_int(cells[2]),
        "i10_index": to_int(cells[4]),
        "publications": publications,
        "source": "Google Scholar profile",
    }


def from_profile_page() -> dict:
    query = urllib.parse.urlencode({"user": SCHOLAR_USER, "hl": "en", "cstart": 0, "pagesize": 100})
    return parse_profile(get("https://scholar.google.com/citations?" + query))


def from_serpapi(api_key: str) -> dict:
    query = urllib.parse.urlencode(
        {"engine": "google_scholar_author", "author_id": SCHOLAR_USER, "hl": "en", "num": 100, "api_key": api_key}
    )
    data = json.loads(get("https://serpapi.com/search.json?" + query))
    if "error" in data:
        raise RuntimeError(data["error"])
    table = (data.get("cited_by") or {}).get("table") or []

    def metric(name: str) -> int:
        for row in table:
            if name in row:
                return to_int((row[name] or {}).get("all"))
        return 0

    publications = [
        {"title": article.get("title", ""), "citations": to_int((article.get("cited_by") or {}).get("value"))}
        for article in data.get("articles") or []
    ]
    return {
        "citations": metric("citations"),
        "h_index": metric("h_index"),
        "i10_index": metric("i10_index"),
        "publications": publications,
        "source": "Google Scholar via SerpAPI",
    }


def read_existing() -> dict:
    """Return the object stored in data/scholar.js, or {} if missing or unreadable."""
    try:
        text = OUT_FILE.read_text(encoding="utf-8")
        return json.loads(text[text.index("{"): text.rindex("}") + 1])
    except (OSError, ValueError):
        return {}


def main() -> int:
    attempts = [("profile page", from_profile_page)]
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if api_key:
        attempts.append(("SerpAPI", lambda: from_serpapi(api_key)))

    data = None
    for name, fetch in attempts:
        try:
            data = fetch()
            break
        except Exception as exc:  # network errors, blocks, layout changes
            print(f"::warning::Scholar fetch via {name} failed: {exc}")
    if data is None:
        print("::warning::No Scholar data fetched; keeping the existing data/scholar.js")
        return 0

    previous = read_existing()
    fields = ("citations", "h_index", "i10_index", "publications")
    if all(previous.get(field) == data.get(field) for field in fields):
        print("Scholar metrics unchanged.")
        return 0

    data["updated"] = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    data["profile"] = f"https://scholar.google.com/citations?user={SCHOLAR_USER}&hl=en"
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(HEADER + json.dumps(data, indent=2, ensure_ascii=False) + ";\n", encoding="utf-8")
    print(f"Updated: {data['citations']} citations, h-index {data['h_index']}, i10-index {data['i10_index']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
