"""메인 서버(FastAPI). 웹 화면의 모든 요청은 여기를 거친다.

실행: uvicorn main_server.app:app --port 8000 --reload
API 문서: http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager
from datetime import date

import httpx
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from config import AI_SERVER_URL
from . import models
from .db import Base, engine, get_db
from .schemas import CalendarIn, CalendarOut, ChatIn, ChatOut, ContestOut
from .seed import seed_if_empty


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)   # 테이블이 없으면 생성
    seed_if_empty()                    # 화면 개발용 샘플 데이터
    yield


app = FastAPI(title="캠퍼스 메이트 메인 서버", lifespan=lifespan)


# ---------- 공고 ----------
@app.get("/api/categories", response_model=list[str])
def list_categories(db: Session = Depends(get_db)):
    categories = db.scalars(select(models.Contest.category).distinct()).all()
    return sorted(category for category in categories if category)


@app.get("/api/contests", response_model=list[ContestOut])
def list_contests(category: str | None = None, keyword: str | None = None,
                  include_closed: bool = False, limit: int = 50,
                  db: Session = Depends(get_db)):
    query = select(models.Contest)
    if category:
        query = query.where(models.Contest.category == category)
    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(or_(models.Contest.title.like(pattern), models.Contest.host.like(pattern),
                                models.Contest.category.like(pattern), models.Contest.summary.like(pattern)))
    if not include_closed:
        query = query.where(or_(models.Contest.deadline.is_(None), models.Contest.deadline >= date.today()))
    query = query.order_by(models.Contest.deadline.is_(None), models.Contest.deadline).limit(limit)
    return db.scalars(query).all()


@app.get("/api/contests/{contest_id}", response_model=ContestOut)
def get_contest(contest_id: int, db: Session = Depends(get_db)):
    contest = db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(404, "공고를 찾을 수 없습니다")
    return contest


# ---------- AI 질의응답: 웹 → 메인 서버 → AI 서버 ----------
@app.post("/api/chat", response_model=ChatOut)
async def ask_agent(body: ChatIn):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(f"{AI_SERVER_URL}/agent/chat", json=body.model_dump())
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        raise HTTPException(503, "AI 서버에 연결할 수 없습니다")


# ---------- 캘린더 (구글 캘린더 연동은 5.1~5.2 작업에서) ----------
@app.post("/api/calendar", response_model=CalendarOut)
def add_calendar_entry(body: CalendarIn, db: Session = Depends(get_db)):
    contest = db.get(models.Contest, body.contest_id)
    if not contest:
        raise HTTPException(404, "공고를 찾을 수 없습니다")
    existing_entry = db.scalar(select(models.CalendarEntry)
                               .where(models.CalendarEntry.contest_id == body.contest_id))
    if existing_entry:
        return CalendarOut(id=existing_entry.id, contest=contest, created_at=existing_entry.created_at)
    entry = models.CalendarEntry(contest_id=body.contest_id)
    # TODO(5.2): 구글 캘린더 API로 일정 생성 후 entry.google_event_id 저장
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return CalendarOut(id=entry.id, contest=contest, created_at=entry.created_at)


@app.get("/api/calendar", response_model=list[CalendarOut])
def list_calendar_entries(db: Session = Depends(get_db)):
    rows = db.execute(select(models.CalendarEntry, models.Contest)
                      .join(models.Contest, models.Contest.id == models.CalendarEntry.contest_id)
                      .order_by(models.Contest.deadline)).all()
    return [CalendarOut(id=entry.id, contest=contest, created_at=entry.created_at) for entry, contest in rows]


@app.delete("/api/calendar/{entry_id}")
def delete_calendar_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(models.CalendarEntry, entry_id)
    if entry:
        db.delete(entry)
        db.commit()
    return {"ok": True}
