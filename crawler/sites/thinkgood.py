"""씽굿 수집기 (일반 요청 + HTML 파싱). 작업 3.2(11/4~5)에서 구현."""
from ..base import BaseCrawler, RawContest


class Crawler(BaseCrawler):
    source = "thinkgood"
    list_url = ""   # TODO: 공모전 목록 페이지 주소

    def crawl(self) -> list[RawContest]:
        # TODO: 1) self.fetch(self.list_url)로 목록 HTML 받기
        #       2) 공고별 제목·상세 주소 뽑기 (HTML 파서 선택: BeautifulSoup 등)
        #       3) 상세 페이지에서 본문 텍스트만 page_text에 담기 (첨부파일은 받지 않음)
        #       4) 홈페이지(접수) 링크는 apply_url, 포스터 <img> 주소는 poster_url에 담기 (이미지는 받지 않음)
        return []
