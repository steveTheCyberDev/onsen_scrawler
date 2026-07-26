from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .models import OnsenSpring


class SpaOrJpSearchParser:
    """Parse a spa.or.jp /search_p/ result page into a list of OnsenSpring."""

    def parse(self, url: str, html: str) -> list[OnsenSpring]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        for item in soup.select("ul.result_item li"):
            results.append(self._parse_item(url, item))
        return results

    def _parse_item(self, base_url: str, item) -> OnsenSpring:
        location_tag = item.select_one(".location")
        name_tag = item.select_one(".name a")
        quality_tag = item.select_one(".spa_quality")
        # sales_point uses style="sales_point" (not a class)
        sales_tag = item.find("div", style="sales_point")

        detail_url = None
        if name_tag and name_tag.get("href"):
            detail_url = urljoin(base_url, name_tag["href"])

        quality_text = None
        if quality_tag:
            for img in quality_tag.find_all("img"):
                img.decompose()
            quality_text = quality_tag.get_text(strip=True) or None

        return OnsenSpring(
            source_url=base_url,
            name=name_tag.get_text(strip=True) if name_tag else None,
            location=location_tag.get_text(strip=True) if location_tag else None,
            spa_quality=quality_text,
            sales_point=sales_tag.get_text(strip=True) if sales_tag else None,
            detail_url=detail_url,
        )
