"""캠퍼스픽 수집기 (Playwright 필요). 작업 3.3(11/5~6)에서 구현.

준비: pip install playwright && playwright install chromium
"""
from ..base import BaseCrawler, RawContest


class CampuspickCrawler(BaseCrawler):
    source = "campuspick"

    def crawl(self) -> list[RawContest]:
        # TODO: Playwright로 목록 페이지를 띄운 뒤, 화면이 채워지면 공고 정보 읽기
        #       (접수 링크는 apply_url, 포스터 <img> 주소는 poster_url에. 이미지는 받지 않음)
        return []
