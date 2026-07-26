import time
from typing import Optional

import requests
from charset_normalizer import from_bytes

from .config import SETTINGS


class Fetcher:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": SETTINGS.user_agent})

    def get(self, url: str) -> Optional[str]:
        last_exc: Optional[Exception] = None
        for attempt in range(SETTINGS.max_retries):
            try:
                resp = self.session.get(url, timeout=SETTINGS.request_timeout)
                resp.raise_for_status()
                return self._decode(resp)
            except requests.RequestException as exc:
                last_exc = exc
                time.sleep(2**attempt)
        print(f"[fetcher] giving up on {url}: {last_exc}")
        return None

    @staticmethod
    def _decode(resp: requests.Response) -> str:
        # Japanese sites still use Shift_JIS / EUC-JP. Trust meta-declared
        # charset first, fall back to charset_normalizer's detection.
        declared = resp.encoding if "charset" in resp.headers.get("content-type", "").lower() else None
        if declared:
            return resp.content.decode(declared, errors="replace")
        best = from_bytes(resp.content).best()
        encoding = best.encoding if best else "utf-8"
        return resp.content.decode(encoding, errors="replace")
