"""MCP server exposing on-demand onsen scraping as a tool for MCP clients
(Claude Code, Claude Desktop, etc.) — instead of only running on a schedule."""
from __future__ import annotations

import psycopg
from mcp.server.fastmcp import FastMCP

from .config import SETTINGS
from .region_scraper import SLUG_TO_REGION_NAME, UnknownRegionError, scrape_region
from .storage_pg import PostgresStorage

mcp = FastMCP("onsen-scrawler")


@mcp.tool()
def scrape_onsen(region: str, max_pages: int = 5, write_to_db: bool = True) -> dict:
    """Scrape onsen spring listings for a Japanese region on demand.

    Args:
        region: region slug, one of: hokkaido, tohoku, hokuriku, kanto, tokai,
            kinki, chugoku, shikoku, kyushu, okinawa.
        max_pages: maximum number of paginated search-result pages to fetch
            (each page holds up to 10 results; stops early if a page returns
            fewer than 10). Keep this small for a quick on-demand call.
        write_to_db: if True, upsert the scraped records into Postgres via the
            existing three-table schema (onsen_springs / spa_quality_types /
            onsen_spring_qualities). If False, just return the scraped data
            without touching the database.

    Returns:
        A summary dict: region, records_found, records_written, and a small
        sample of the scraped records.
    """
    try:
        springs = scrape_region(region, max_pages=max_pages)
    except UnknownRegionError as exc:
        return {"error": str(exc)}

    records_written = 0
    if write_to_db and springs:
        with psycopg.connect(SETTINGS.db_url) as conn:
            storage = PostgresStorage(conn)
            for spring in springs:
                storage.write(spring, region_slug=region)
            records_written = storage.flush()
            conn.commit()

    return {
        "region": region,
        "records_found": len(springs),
        "records_written": records_written if write_to_db else 0,
        "sample": [s.to_dict() for s in springs[:3]],
    }


@mcp.tool()
def list_regions() -> list[str]:
    """List the valid region slugs this scraper knows how to fetch."""
    return sorted(SLUG_TO_REGION_NAME)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
