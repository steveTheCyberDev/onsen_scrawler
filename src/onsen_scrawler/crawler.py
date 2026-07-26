import time
from collections import deque
from typing import Iterable
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

from .config import SETTINGS
from .fetcher import Fetcher
from .parser import OnsenParser
from .storage import JsonlStorage


class Crawler:
    def __init__(
        self,
        fetcher: Fetcher | None = None,
        parser: OnsenParser | None = None,
        storage: JsonlStorage | None = None,
        same_host_only: bool = True,
    ) -> None:
        self.fetcher = fetcher or Fetcher()
        self.parser = parser or OnsenParser()
        self.storage = storage or JsonlStorage(SETTINGS.output_path)
        self.same_host_only = same_host_only
        self.seen: set[str] = set()
        self._robots: dict[str, RobotFileParser] = {}

    def crawl(self, seeds: Iterable[str], max_pages: int = 50) -> None:
        queue: deque[str] = deque(seeds)
        start_hosts = {urlparse(u).netloc for u in queue}
        fetched = 0

        while queue and fetched < max_pages:
            url = queue.popleft()
            if url in self.seen:
                continue
            self.seen.add(url)

            if self.same_host_only and urlparse(url).netloc not in start_hosts:
                continue
            if SETTINGS.respect_robots_txt and not self._allowed(url):
                print(f"[crawler] blocked by robots.txt: {url}")
                continue

            html = self.fetcher.get(url)
            if html is None:
                continue

            onsen, links = self.parser.parse(url, html)
            self.storage.append(onsen)
            fetched += 1
            print(f"[crawler] {fetched:>4}  {url}")

            for link in links:
                if link not in self.seen:
                    queue.append(link)

            time.sleep(SETTINGS.delay_between_requests)

    def _allowed(self, url: str) -> bool:
        host = urlparse(url).netloc
        rp = self._robots.get(host)
        if rp is None:
            rp = RobotFileParser()
            rp.set_url(f"{urlparse(url).scheme}://{host}/robots.txt")
            try:
                rp.read()
            except Exception:
                return True
            self._robots[host] = rp
        return rp.can_fetch(SETTINGS.user_agent, url)
