from typing import Iterable
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import Onsen


class OnsenParser:
    """Turn an HTML page into an Onsen + outbound links to follow.

    Selectors are placeholders — replace with ones that match the target
    site once you've inspected its markup.
    """

    def parse(self, url: str, html: str) -> tuple[Onsen, list[str]]:
        soup = BeautifulSoup(html, "lxml")
        onsen = Onsen(
            url=url,
            name=self._text(soup, "h1"),
            area=self._text(soup, ".area"),
            address=self._text(soup, ".address"),
            description=self._text(soup, ".description"),
            tags=[t.get_text(strip=True) for t in soup.select(".tag")],
        )
        links = list(self._extract_links(url, soup))
        return onsen, links

    @staticmethod
    def _text(soup: BeautifulSoup, selector: str) -> str | None:
        el = soup.select_one(selector)
        return el.get_text(strip=True) if el else None

    @staticmethod
    def _extract_links(base_url: str, soup: BeautifulSoup) -> Iterable[str]:
        for a in soup.select("a[href]"):
            yield urljoin(base_url, a["href"])
