"""수집 실행. 실행: python -m crawler.run

지금은 각 사이트 수집기가 빈 목록을 돌려준다. 3.x 작업에서 채우고,
4.2 작업에서 page_text를 AI 서버에 보내 핵심 추출·요약을 받은 뒤 저장한다.
"""
from sqlalchemy import select

from main_server import models
from main_server.db import Base, SessionLocal, engine
from .sites import campuspick, linkareer, thinkgood

CRAWLERS = [linkareer.Crawler, thinkgood.Crawler, campuspick.Crawler]


def save(items) -> int:
    n = 0
    with SessionLocal() as db:
        for it in items:
            if db.scalar(select(models.Contest).where(models.Contest.source_url == it.source_url)):
                continue   # 이미 있는 공고 (사이트 간 중복 병합은 4.3 작업)
            db.add(models.Contest(source=it.source, source_url=it.source_url, title=it.title,
                                  host=it.host, organizer=it.organizer, category=it.category,
                                  deadline=it.deadline, apply_url=it.apply_url, poster_url=it.poster_url))
            n += 1
        db.commit()
    return n


def main():
    Base.metadata.create_all(engine)
    for cls in CRAWLERS:
        c = cls()
        try:
            items = c.crawl()
            n = save(items)
            result = "ok"
        except Exception as e:  # 한 사이트가 실패해도 나머지는 계속
            n, result = 0, f"error: {type(e).__name__}"
        with SessionLocal() as db:
            db.add(models.CrawlLog(source=c.source, collected=n, result=result))
            db.commit()
        print(f"[{c.source}] 새 공고 {n}건 ({result})")


if __name__ == "__main__":
    main()
