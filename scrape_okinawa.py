"""One-shot scraper: spa.or.jp Okinawa onsen springs search page."""
import json

from src.onsen_scrawler.fetcher import Fetcher
from src.onsen_scrawler.parser_spa import SpaOrJpSearchParser

URL = "https://www.spa.or.jp/search_p/?F_AREA=%E6%B2%96%E7%B8%84"
OUT = "data/okinawa_springs.jsonl"


def main() -> None:
    fetcher = Fetcher()
    parser = SpaOrJpSearchParser()

    print(f"Fetching {URL} ...")
    html = fetcher.get(URL)
    if not html:
        print("Failed to fetch page.")
        return

    springs = parser.parse(URL, html)
    print(f"Found {len(springs)} results.")

    import pathlib
    pathlib.Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for s in springs:
            f.write(json.dumps(s.to_dict(), ensure_ascii=False) + "\n")

    print(f"Saved to {OUT}")
    print()
    for s in springs:
        print(f"  [{s.location}] {s.name}")
        print(f"    泉質: {s.spa_quality}")
        print(f"    概要: {s.sales_point}")
        print(f"    URL:  {s.detail_url}")
        print()


if __name__ == "__main__":
    main()
