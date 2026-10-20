"""수집 실행. 실행: python -m crawler.run

지금은 각 사이트 수집기가 빈 목록을 돌려준다. 3.x 작업에서 채우고,
4.2 작업에서 page_text를 AI 서버에 보내 핵심 추출·요약을 받은 뒤 저장한다.
"""
from sqlalchemy import select

from main_server import models
from main_server.db import Base, SessionLocal, engine
from .sites.campuspick import CampuspickCrawler
from .sites.linkareer import LinkareerCrawler
from .sites.thinkgood import ThinkgoodCrawler

CRAWLER_CLASSES = [LinkareerCrawler, ThinkgoodCrawler, CampuspickCrawler]


def save_contests(raw_contests) -> int:
    saved_count = 0
    with SessionLocal() as db:
        for raw in raw_contests:
            if db.scalar(select(models.Contest).where(models.Contest.source_url == raw.source_url)):
                continue   # 이미 있는 공고 (사이트 간 중복 병합은 4.3 작업)
            db.add(models.Contest(source=raw.source, source_url=raw.source_url, title=raw.title,
                                  host=raw.host, organizer=raw.organizer, category=raw.category,
                                  deadline=raw.deadline, apply_url=raw.apply_url, poster_url=raw.poster_url))
            saved_count += 1
        db.commit()
    return saved_count


def main():
    Base.metadata.create_all(engine)
    for crawler_class in CRAWLER_CLASSES:
        crawler = crawler_class()
        try:
            raw_contests = crawler.crawl()
            saved_count = save_contests(raw_contests)
            result = "ok"
        except Exception as error:  # 한 사이트가 실패해도 나머지는 계속
            saved_count, result = 0, f"error: {type(error).__name__}"
        with SessionLocal() as db:
            db.add(models.CrawlLog(source=crawler.source, collected=saved_count, result=result))
            db.commit()
        print(f"[{crawler.source}] 새 공고 {saved_count}건 ({result})")


if __name__ == "__main__":
    main()
