from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Onsen:
    url: str
    name: Optional[str] = None
    area: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OnsenSpring:
    """One row scraped from a spa.or.jp search_p result page."""
    source_url: str
    name: Optional[str] = None
    location: Optional[str] = None
    spa_quality: Optional[str] = None
    sales_point: Optional[str] = None
    detail_url: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)
