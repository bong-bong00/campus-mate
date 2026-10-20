"""에이전트가 쓰는 도구. AI 서버는 DB에 직접 접근하지 않고 메인 서버 API만 호출한다."""
import httpx

from config import MAIN_SERVER_URL

# LLM에 넘길 도구 정의(4.4 질의응답 에이전트 작업에서 사용)
TOOL_SPECS = [
    {
        "name": "search_contests",
        "description": "조건에 맞는 공모전 공고를 검색한다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string", "description": "검색어"},
                "category": {"type": "string", "description": "분야"},
            },
        },
    },
    {
        "name": "get_contest",
        "description": "공고 ID로 상세 내용을 조회한다.",
        "input_schema": {
            "type": "object",
            "properties": {"contest_id": {"type": "integer"}},
            "required": ["contest_id"],
        },
    },
    {
        "name": "add_calendar_entry",
        "description": "공고 마감일을 사용자 캘린더에 등록한다.",
        "input_schema": {
            "type": "object",
            "properties": {"contest_id": {"type": "integer"}},
            "required": ["contest_id"],
        },
    },
]


async def search_contests(keyword: str | None = None, category: str | None = None) -> list[dict]:
    params = {key: value for key, value in {"keyword": keyword, "category": category}.items() if value}
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{MAIN_SERVER_URL}/api/contests", params=params)
        response.raise_for_status()
        return response.json()


async def get_contest(contest_id: int) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(f"{MAIN_SERVER_URL}/api/contests/{contest_id}")
        response.raise_for_status()
        return response.json()


async def add_calendar_entry(contest_id: int) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(f"{MAIN_SERVER_URL}/api/calendar", json={"contest_id": contest_id})
        response.raise_for_status()
        return response.json()


TOOLS = {"search_contests": search_contests, "get_contest": get_contest, "add_calendar_entry": add_calendar_entry}
