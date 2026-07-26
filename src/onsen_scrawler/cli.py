import argparse

from .crawler import Crawler


def main() -> None:
    ap = argparse.ArgumentParser(prog="onsen-scrawler")
    ap.add_argument("seeds", nargs="+", help="One or more seed URLs to start crawling from")
    ap.add_argument("--max-pages", type=int, default=50)
    ap.add_argument("--any-host", action="store_true", help="Allow following links off the seed hosts")
    args = ap.parse_args()

    crawler = Crawler(same_host_only=not args.any_host)
    crawler.crawl(args.seeds, max_pages=args.max_pages)
