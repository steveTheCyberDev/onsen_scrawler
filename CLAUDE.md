# onsen_scrawler

Scraper for Japanese onsen (温泉) sites. Stores normalized data in Postgres.

## Stack
- Python ≥3.10 (PEP 604 unions used). `.python-version` = 3.12.
- `requests` + `beautifulsoup4` (lxml) + `charset-normalizer`.
- Postgres via `psycopg` v3 with hand-written SQL (no ORM).
- Output: JSONL writer exists at `storage.py` as a stop-gap; Postgres writer + `schema.sql` come once the schema is designed.

## Layout
```
src/onsen_scrawler/
├── config.py        Settings dataclass (UA, delays, output path, robots toggle)
├── models.py        Onsen dataclass + OnsenSpring (spa.or.jp search_p fields)
├── fetcher.py       requests.Session + retries + JP-aware decoding
├── parser.py        BeautifulSoup → Onsen; selectors are placeholders
├── parser_spa.py    SpaOrJpSearchParser — parses search_p result pages into OnsenSpring
├── storage.py       JSONL append writer (interim)
├── crawler.py       BFS queue, seen-set, same-host gate, robots.txt
└── cli.py           argparse: `onsen-scrawler <seeds...> [--max-pages N] [--any-host]`

data/
├── regions.jsonl              10 regions scraped from division01_left (name + url)
├── dropdown_options.json      F_PREFS (47 prefectures) + F_QUALITY (13 spring types)
├── {region}_springs.jsonl     All springs for a region, all pages combined
│   e.g. shikoku_springs.jsonl, okinawa_springs.jsonl
└── ...
```

## Workflow: adding a new target site
**Schema-first.** Inspect the site, design tables, *then* write parser code.

1. **Save one detail page locally** (not a listing page):
   ```bash
   curl -A "Mozilla/5.0" -o sample.html "<url>"
   file sample.html                              # check encoding
   iconv -f SHIFT_JIS -t UTF-8 sample.html > sample.utf8.html   # if needed
   ```
2. **Inventory fields** in DevTools. For each field record: example value, CSS selector, presence (always / mostly / sometimes).
3. **Bucket the fields** to drive the schema:
   - single-value, always present → `NOT NULL` column on `onsen`
   - single-value, sometimes missing → nullable column on `onsen`
   - multi-value (泉質, 効能, images, bath types) → child table with FK, or many-to-many via lookup if values repeat across onsens
   - always include crawl metadata: `source_url`, `fetched_at`, `raw_html_hash`
4. **Write `schema.sql`**, apply to a local Postgres.
5. **Then** update `parser.py` selectors and swap `JsonlStorage` for the psycopg writer.

## Japanese-page gotchas
- Many onsen sites still serve Shift_JIS or EUC-JP. `fetcher.py` trusts the response's declared charset only when `Content-Type` includes one; otherwise falls back to `charset_normalizer`. Don't bypass this.
- Write JSONL/JSON with `ensure_ascii=False` so kanji stay readable.
- When inspecting saved HTML, convert to UTF-8 with `iconv` before reading.

## Conventions
- No ORM. Schema lives in `schema.sql`; queries in Python are plain SQL strings.
- Parser selectors are per-site. If a second site is added, namespace parsers (e.g. `parser/niftyonsen.py`) rather than branching inside one parser.
- Respect `robots.txt` (`SETTINGS.respect_robots_txt`) and the `delay_between_requests` floor. Don't lower the delay below ~1s without a reason.

## Scraping spa.or.jp regions

### Data flow
1. Regions are stored in `data/regions.jsonl` (name + full URL).
2. Each region's search page paginates as `?pg=0`, `?pg=1`, … until a page returns fewer than 10 results.
3. Each region is saved to `data/{region_slug}_springs.jsonl` where `region_slug` is the romaji/ascii slug derived from the region name (e.g. `shikoku`, `okinawa`).

### Output format per record (`OnsenSpring`)
```json
{
  "source_url": "https://www.spa.or.jp/search_p/?pg=0&F_AREA=...",
  "name": "温泉名",
  "location": "都道府県 市区町村",
  "spa_quality": "泉質",
  "sales_point": "概要テキスト",
  "detail_url": "https://www.spa.or.jp/search_p/detail_p/?F_ID=..."
}
```

### Pagination rule
- Start at `pg=0`, increment by 1.
- Stop when the page returns **fewer than 10 results** (signals last page).
- Respect `delay_between_requests` (≥1 s) between page fetches.

### File naming — all regions scraped (2026-05-22)
| Region | Slug | File | Records |
|--------|------|------|---------|
| 北海道 | hokkaido | `data/hokkaido_springs.jsonl` | 227 |
| 東北地方 | tohoku | `data/tohoku_springs.jsonl` | 577 |
| 北陸・甲信越地方 | hokuriku | `data/hokuriku_springs.jsonl` | 577 |
| 関東地方 | kanto | `data/kanto_springs.jsonl` | 286 |
| 東海地方 | tokai | `data/tokai_springs.jsonl` | 217 |
| 近畿地方 | kinki | `data/kinki_springs.jsonl` | 191 |
| 中国地方 | chugoku | `data/chugoku_springs.jsonl` | 171 |
| 四国地方 | shikoku | `data/shikoku_springs.jsonl` | 98 |
| 九州地方 | kyushu | `data/kyushu_springs.jsonl` | 289 |
| 沖縄 | okinawa | `data/okinawa_springs.jsonl` | 3 |
| **Total** | | | **2,636** |

## Running
```bash
uv sync
uv run onsen-scrawler <seed-url> --max-pages 10
uv run python -m onsen_scrawler <seed-url>

# One-off region scrapes
python3 scrape_okinawa.py
```
