"""AI 서버(에이전트). 메인 서버만 이 서버를 호출한다.

실행: uvicorn ai_server.app:app --port 8001 --reload

지금은 LLM 없이 '검색 → 결과 확인 → 조건 완화 후 재검색 → 출처 첨부' 흐름만 흉내 낸다.
4.1(LLM 연동) 작업에서 run_agent 안쪽을 LLM 도구 호출 반복 구조로 바꾸면 된다.
"""
from fastapi import FastAPI
from pydantic import BaseModel

from config import LLM_API_KEY
from . import tools

app = FastAPI(title="캠퍼스 메이트 AI 서버")

STOP_WORDS = {"알려", "알려줘", "공모전", "있어", "있어?", "추천", "해줘", "좀", "뭐", "어떤", "이번", "관련", "관련된"}


class ChatIn(BaseModel):
    question: str


def _extract_keywords(question: str) -> list[str]:
    words = [word.strip("?.!,") for word in question.split()]
    return [word for word in words if len(word) >= 2 and word not in STOP_WORDS]


async def run_agent(question: str) -> dict:
    if LLM_API_KEY:
        pass  # TODO(4.1, 4.4): LLM에 tools.TOOL_SPECS를 넘기고 도구 호출이 끝날 때까지 반복

    # 임시 흐름: 키워드별로 검색하고, 하나도 없으면 조건을 빼고 다시 검색
    found_contests: dict[int, dict] = {}
    for keyword in _extract_keywords(question):
        for contest in await tools.search_contests(keyword=keyword):
            found_contests[contest["id"]] = contest
    is_retried = False
    if not found_contests:
        is_retried = True
        for contest in (await tools.search_contests())[:3]:
            found_contests[contest["id"]] = contest

    if not found_contests:
        return {"answer": "조건에 맞는 공고를 찾지 못했습니다.", "sources": []}

    contests = list(found_contests.values())[:5]
    lines = [f"- {contest['title']} (마감 {contest['deadline']})" for contest in contests]
    intro = "질문과 정확히 맞는 공고가 없어 마감이 가까운 공고를 보여 드립니다." if is_retried \
        else f"관련 공고 {len(contests)}건을 찾았습니다."
    return {
        "answer": intro + "\n" + "\n".join(lines),
        "sources": [{"id": contest["id"], "title": contest["title"], "source_url": contest["source_url"]}
                    for contest in contests],
    }


@app.post("/agent/chat")
async def answer_question(body: ChatIn):
    return await run_agent(body.question)


@app.get("/health")
def check_health():
    return {"ok": True, "llm": bool(LLM_API_KEY)}
