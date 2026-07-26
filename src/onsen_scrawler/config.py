import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    user_agent: str = "onsen-scrawler/0.1 (+contact: steve.thecyberdev@gmail.com)"
    request_timeout: float = 15.0
    delay_between_requests: float = 1.0
    max_retries: int = 3
    respect_robots_txt: bool = True
    output_path: Path = Path("data/onsen.jsonl")
    db_url: str = os.environ.get("DATABASE_URL", "postgresql://localhost/onsen")


SETTINGS = Settings()
