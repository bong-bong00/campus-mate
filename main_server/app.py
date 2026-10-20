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
def categories(db: Session = Depends(get_db)):
    rows = db.scalars(select(models.Contest.category).distinct()).all()
    return sorted(c for c in rows if c)


@app.get("/api/contests", response_model=list[ContestOut])
def list_contests(category: str | None = None, q: str | None = None,
                  include_closed: bool = False, limit: int = 50,
                  db: Session = Depends(get_db)):
    stmt = select(models.Contest)
    if category:
        stmt = stmt.where(models.Contest.category == category)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(models.Contest.title.like(like), models.Contest.host.like(like),
                              models.Contest.category.like(like), models.Contest.summary.like(like)))
    if not include_closed:
        stmt = stmt.where(or_(models.Contest.deadline.is_(None), models.Contest.deadline >= date.today()))
    stmt = stmt.order_by(models.Contest.deadline.is_(None), models.Contest.deadline).limit(limit)
    return db.scalars(stmt).all()


@app.get("/api/contests/{contest_id}", response_model=ContestOut)
def get_contest(contest_id: int, db: Session = Depends(get_db)):
    contest = db.get(models.Contest, contest_id)
    if not contest:
        raise HTTPException(404, "공고를 찾을 수 없습니다")
    return contest


# ---------- AI 질의응답: 웹 → 메인 서버 → AI 서버 ----------
@app.post("/api/chat", response_model=ChatOut)
async def chat(body: ChatIn):
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            res = await client.post(f"{AI_SERVER_URL}/agent/chat", json=body.model_dump())
            res.raise_for_status()
            return res.json()
    except httpx.HTTPError:
        raise HTTPException(503, "AI 서버에 연결할 수 없습니다")


# ---------- 캘린더 (구글 캘린더 연동은 5.1~5.2 작업에서) ----------
@app.post("/api/calendar", response_model=CalendarOut)
def add_calendar(body: CalendarIn, db: Session = Depends(get_db)):
    contest = db.get(models.Contest, body.contest_id)
    if not contest:
        raise HTTPException(404, "공고를 찾을 수 없습니다")
    exists = db.scalar(select(models.CalendarEntry).where(models.CalendarEntry.contest_id == body.contest_id))
    if exists:
        return CalendarOut(id=exists.id, contest=contest, created_at=exists.created_at)
    entry = models.CalendarEntry(contest_id=body.contest_id)
    # TODO(5.2): 구글 캘린더 API로 일정 생성 후 entry.google_event_id 저장
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return CalendarOut(id=entry.id, contest=contest, created_at=entry.created_at)


@app.get("/api/calendar", response_model=list[CalendarOut])
def list_calendar(db: Session = Depends(get_db)):
    rows = db.execute(select(models.CalendarEntry, models.Contest)
                      .join(models.Contest, models.Contest.id == models.CalendarEntry.contest_id)
                      .order_by(models.Contest.deadline)).all()
    return [CalendarOut(id=e.id, contest=c, created_at=e.created_at) for e, c in rows]


@app.delete("/api/calendar/{entry_id}")
def delete_calendar(entry_id: int, db: Session = Depends(get_db)):
    entry = db.get(models.CalendarEntry, entry_id)
    if entry:
        db.delete(entry)
        db.commit()
    return {"ok": True}
