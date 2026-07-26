"""On-demand region scraping — reusable by the CLI, one-off scripts, and the MCP server."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .config import SETTINGS
from .fetcher import Fetcher
from .models import OnsenSpring
from .parser_spa import SpaOrJpSearchParser

_REGIONS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "regions.jsonl"

# English slug -> Japanese region name, as used in data/regions.jsonl.
SLUG_TO_REGION_NAME = {
    "hokkaido": "北海道",
    "tohoku": "東北地方",
    "hokuriku": "北陸・甲信越地方",
    "kanto": "関東地方",
    "tokai": "東海地方",
    "kinki": "近畿地方",
    "chugoku": "中国地方",
    "shikoku": "四国地方",
    "kyushu": "九州地方",
    "okinawa": "沖縄",
}


class UnknownRegionError(ValueError):
    pass


def _load_region_url(region_slug: str) -> str:
    region_name = SLUG_TO_REGION_NAME.get(region_slug)
    if region_name is None:
        raise UnknownRegionError(
            f"Unknown region slug {region_slug!r}. Valid slugs: {sorted(SLUG_TO_REGION_NAME)}"
        )
    with open(_REGIONS_FILE, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if row["name"] == region_name:
                return row["url"]
    raise UnknownRegionError(f"{region_name!r} not found in {_REGIONS_FILE}")


def scrape_region(region_slug: str, max_pages: int = 10) -> list[OnsenSpring]:
    """Scrape a single region's spa.or.jp search results, paginating until a page
    returns fewer than 10 results (last-page signal) or max_pages is reached."""
    base_url = _load_region_url(region_slug)
    fetcher = Fetcher()
    parser = SpaOrJpSearchParser()

    all_springs: list[OnsenSpring] = []
    for page in range(max_pages):
        sep = "&" if "?" in base_url else "?"
        page_url = f"{base_url}{sep}pg={page}"
        html = fetcher.get(page_url)
        if html is None:
            break
        springs = parser.parse(page_url, html)
        all_springs.extend(springs)
        if len(springs) < 10:
            break
        time.sleep(SETTINGS.delay_between_requests)

    return all_springs
