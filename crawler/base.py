"""크롤러 공통 규칙. 운영 원칙(사실 정보만 저장, 하루 1~2회, 요청 간격)을 여기서 지킨다."""
import time
from dataclasses import dataclass
from datetime import date

import httpx

REQUEST_DELAY_SEC = 3      # 요청 사이 간격
USER_AGENT = "CampusMate-SchoolProject/0.1 (non-commercial, educational)"


@dataclass
class RawContest:
    """크롤러가 넘기는 값. 원문 전체가 아니라 핵심 항목만 담는다."""
    source: str
    source_url: str
    title: str
    host: str | None = None
    organizer: str | None = None   # 주관
    category: str | None = None
    deadline: date | None = None
    apply_url: str | None = None   # 지원(주최측 접수) 링크
    poster_url: str | None = None  # 포스터 이미지 주소만 저장. 크롤러가 이 주소에 접속하지 않음
    page_text: str | None = None   # 에이전트가 핵심 추출·요약할 때만 쓰고 DB에는 저장하지 않음


class BaseCrawler:
    source = ""

    def __init__(self):
        self.client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=20, follow_redirects=True)
        self._last = 0.0

    def fetch(self, url: str) -> str:
        wait = REQUEST_DELAY_SEC - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        res = self.client.get(url)
        self._last = time.time()
        res.raise_for_status()
        return res.text

    def crawl(self) -> list[RawContest]:
        raise NotImplementedError
