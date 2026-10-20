"""DB 테이블. 원문 전체는 저장하지 않고 핵심 항목 + 요약 + 원문 링크만 저장한다."""
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Contest(Base):
    __tablename__ = "contest"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(20))            # linkareer / campuspick / thinkgood
    source_url: Mapped[str] = mapped_column(String(500), unique=True)
    title: Mapped[str] = mapped_column(String(300))
    host: Mapped[str | None] = mapped_column(String(200))       # 주최
    organizer: Mapped[str | None] = mapped_column(String(200))  # 주관 (없으면 비움)
    category: Mapped[str | None] = mapped_column(String(50))    # 분야
    start_date: Mapped[date | None] = mapped_column(Date)       # 접수 시작일
    deadline: Mapped[date | None] = mapped_column(Date)         # 마감일
    eligibility: Mapped[str | None] = mapped_column(String(300))  # 참가 자격
    prize: Mapped[str | None] = mapped_column(String(300))      # 시상
    summary: Mapped[str | None] = mapped_column(Text)           # 에이전트가 새로 작성한 요약
    apply_url: Mapped[str | None] = mapped_column(String(500))  # 지원(주최측 접수) 링크
    poster_url: Mapped[str | None] = mapped_column(String(500)) # 포스터 이미지 원본 주소. 그림은 저장하지 않음
    collected_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CalendarEntry(Base):
    """관심 공고 등록 기록. 구글 캘린더 연동(11/25) 후 google_event_id 채움."""
    __tablename__ = "calendar_entry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contest.id"))
    google_event_id: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class CrawlLog(Base):
    """크롤러 실행 기록."""
    __tablename__ = "crawl_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(20))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    collected: Mapped[int] = mapped_column(Integer, default=0)
    result: Mapped[str] = mapped_column(String(50), default="ok")
