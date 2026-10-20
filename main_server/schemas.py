from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class ContestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    source_url: str
    title: str
    host: str | None = None
    organizer: str | None = None
    category: str | None = None
    start_date: date | None = None
    deadline: date | None = None
    eligibility: str | None = None
    prize: str | None = None
    summary: str | None = None
    apply_url: str | None = None
    poster_url: str | None = None


class ChatIn(BaseModel):
    question: str


class SourceOut(BaseModel):
    id: int
    title: str
    source_url: str


class ChatOut(BaseModel):
    answer: str
    sources: list[SourceOut] = []


class CalendarIn(BaseModel):
    contest_id: int


class CalendarOut(BaseModel):
    id: int
    contest: ContestOut
    created_at: datetime
