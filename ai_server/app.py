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


class ChatIn(BaseModel):
    question: str


def _keywords(question: str) -> list[str]:
    stop = {"알려", "알려줘", "공모전", "있어", "있어?", "추천", "해줘", "좀", "뭐", "어떤", "이번", "관련", "관련된"}
    words = [w.strip("?.!,") for w in question.split()]
    return [w for w in words if len(w) >= 2 and w not in stop]


async def run_agent(question: str) -> dict:
    if LLM_API_KEY:
        pass  # TODO(4.1, 4.4): LLM에 tools.TOOL_SPECS를 넘기고 도구 호출이 끝날 때까지 반복

    # 임시 흐름: 키워드별로 검색하고, 하나도 없으면 조건을 빼고 다시 검색
    found: dict[int, dict] = {}
    for word in _keywords(question):
        for c in await tools.search_contests(q=word):
            found[c["id"]] = c
    retried = False
    if not found:
        retried = True
        for c in (await tools.search_contests())[:3]:
            found[c["id"]] = c

    if not found:
        return {"answer": "조건에 맞는 공고를 찾지 못했습니다.", "sources": []}

    items = list(found.values())[:5]
    lines = [f"- {c['title']} (마감 {c['deadline']})" for c in items]
    head = "질문과 정확히 맞는 공고가 없어 마감이 가까운 공고를 보여 드립니다." if retried \
        else f"관련 공고 {len(items)}건을 찾았습니다."
    return {
        "answer": head + "\n" + "\n".join(lines),
        "sources": [{"id": c["id"], "title": c["title"], "source_url": c["source_url"]} for c in items],
    }


@app.post("/agent/chat")
async def chat(body: ChatIn):
    return await run_agent(body.question)


@app.get("/health")
def health():
    return {"ok": True, "llm": bool(LLM_API_KEY)}
