"""웹 화면(NiceGUI).

실행: python -m web.main   →  http://127.0.0.1:8080
"""
from datetime import date

import httpx
from nicegui import ui

from . import api

SOURCE_NAME = {"linkareer": "링커리어", "thinkgood": "씽굿", "campuspick": "캠퍼스픽"}
CATEGORY_ICON = {"IT·SW": "computer", "디자인": "palette", "영상·UCC": "movie",
                 "기획·마케팅": "lightbulb"}


def category_icon(category: str | None) -> str:
    return CATEGORY_ICON.get(category or "", "emoji_events")


def poster(c: dict, size: str = "w-48 h-64"):
    """포스터는 원본 주소로만 불러온다(저장하지 않음). 없거나 안 뜨면 분야 아이콘."""
    with ui.element("div").classes(f"{size} rounded-lg bg-blue-50 flex items-center justify-center overflow-hidden"):
        icon = ui.icon(category_icon(c.get("category")), size="64px").classes("text-primary")
        if c.get("poster_url"):
            icon.set_visibility(False)
            img = ui.element("img").props(f'src="{c["poster_url"]}" referrerpolicy="no-referrer"') \
                .classes("w-full h-full object-cover")

            def fallback():
                img.set_visibility(False)
                icon.set_visibility(True)
            img.on("error", fallback)


def d_day(deadline: str | None) -> str:
    if not deadline:
        return "상시"
    n = (date.fromisoformat(deadline) - date.today()).days
    return "D-day" if n == 0 else (f"D-{n}" if n > 0 else "마감")


def layout(title: str):
    ui.colors(primary="#2C7BE5")
    with ui.header().classes("items-center bg-white text-black shadow-sm"):
        ui.link("캠퍼스 메이트", "/").classes("text-lg font-bold no-underline text-primary")
        ui.space()
        for label, path in [("공고", "/contests"), ("AI 질문", "/chat"), ("내 일정", "/calendar")]:
            ui.link(label, path).classes("no-underline text-black mx-2")
    ui.page_title(f"{title} | 캠퍼스 메이트")


def contest_card(c: dict):
    with ui.card().classes("w-full cursor-pointer hover:shadow-md").on(
            "click", lambda c=c: ui.navigate.to(f"/contests/{c['id']}")):
        with ui.row().classes("w-full items-center"):
            ui.icon(category_icon(c.get("category"))).classes("text-primary")
            ui.badge(c.get("category") or "기타").props("outline")
            ui.label(SOURCE_NAME.get(c["source"], c["source"])).classes("text-xs text-grey-6")
            ui.space()
            ui.label(d_day(c.get("deadline"))).classes("font-bold text-primary")
        ui.label(c["title"]).classes("text-base font-semibold")
        ui.label(f"{c.get('host') or ''} · 마감 {c.get('deadline') or '-'}").classes("text-sm text-grey-7")


def server_error():
    ui.label("메인 서버에 연결할 수 없습니다. 메인 서버(8000번 포트)를 먼저 실행하세요.").classes("text-negative")


@ui.page("/")
async def index():
    layout("홈")
    with ui.column().classes("w-full max-w-4xl mx-auto gap-6 p-4"):
        ui.label("흩어진 공모전, 한곳에서 찾고 AI에게 물어보세요").classes("text-2xl font-bold")
        with ui.row().classes("w-full items-center"):
            q = ui.input(placeholder="예: 이번 달 마감하는 IT 공모전 알려 줘").classes("flex-grow")
            ui.button("AI에게 질문", on_click=lambda: ui.navigate.to(f"/chat?q={q.value}"))
        try:
            cats = await api.get("/api/categories")
            items = await api.get("/api/contests", limit=4)
        except httpx.HTTPError:
            server_error()
            return
        ui.label("분야").classes("text-lg font-semibold")
        with ui.row():
            for cat in cats:
                ui.button(cat, on_click=lambda cat=cat: ui.navigate.to(f"/contests?category={cat}")).props("outline")
        ui.label("마감 임박").classes("text-lg font-semibold")
        for c in items:
            contest_card(c)


@ui.page("/contests")
async def contests(category: str | None = None, q: str | None = None):
    layout("공고")
    with ui.column().classes("w-full max-w-4xl mx-auto gap-4 p-4"):
        ui.label("공모전 공고").classes("text-2xl font-bold")
        try:
            cats = await api.get("/api/categories")
        except httpx.HTTPError:
            server_error()
            return
        with ui.row().classes("w-full items-center"):
            cat_sel = ui.select(["전체"] + cats, value=category or "전체", label="분야").classes("w-40")
            kw = ui.input("검색어", value=q or "").classes("flex-grow")

            def go():
                params = []
                if cat_sel.value and cat_sel.value != "전체":
                    params.append(f"category={cat_sel.value}")
                if kw.value:
                    params.append(f"q={kw.value}")
                ui.navigate.to("/contests" + ("?" + "&".join(params) if params else ""))
            kw.on("keydown.enter", go)
            ui.button("검색", on_click=go)
        items = await api.get("/api/contests", category=category, q=q)
        if not items:
            ui.label("조건에 맞는 공고가 없습니다.").classes("text-grey-7")
        for c in items:
            contest_card(c)


@ui.page("/contests/{contest_id}")
async def contest_detail(contest_id: int):
    layout("공고 상세")
    with ui.column().classes("w-full max-w-3xl mx-auto gap-4 p-4"):
        try:
            c = await api.get(f"/api/contests/{contest_id}")
        except httpx.HTTPError:
            ui.label("공고를 불러올 수 없습니다.").classes("text-negative")
            return
        with ui.row().classes("items-center"):
            ui.badge(c.get("category") or "기타").props("outline")
            ui.label(d_day(c.get("deadline"))).classes("font-bold text-primary")
        ui.label(c["title"]).classes("text-2xl font-bold")
        with ui.row().classes("w-full items-start no-wrap gap-4"):
            poster(c)
            with ui.card().classes("flex-grow"):
                for label, key in [("주최", "host"), ("주관", "organizer"), ("접수 시작", "start_date"),
                                   ("마감일", "deadline"), ("참가 자격", "eligibility"), ("시상", "prize")]:
                    if key == "organizer" and not c.get(key):
                        continue
                    with ui.row().classes("w-full no-wrap"):
                        ui.label(label).classes("w-24 shrink-0 text-grey-7")
                        ui.label(c.get(key) or "-")
        ui.label("요약").classes("text-lg font-semibold")
        ui.label(c.get("summary") or "요약 준비 중")
        with ui.row():
            async def add():
                await api.post("/api/calendar", {"contest_id": contest_id})
                ui.notify("내 일정에 등록했습니다", type="positive")
            if c.get("apply_url"):
                ui.button("지원하기", icon="send",
                          on_click=lambda: ui.navigate.to(c["apply_url"], new_tab=True))
            ui.button("내 일정에 등록", icon="event", on_click=add).props("outline")
            ui.button(f"{SOURCE_NAME.get(c['source'], '원문')}에서 보기", icon="open_in_new",
                      on_click=lambda: ui.navigate.to(c["source_url"], new_tab=True)).props("flat")
        ui.label(f"출처: {SOURCE_NAME.get(c['source'], c['source'])} · 상세 내용은 원문에서 확인하세요. "
                 "포스터는 원문 사이트의 이미지를 그대로 불러옵니다.").classes("text-xs text-grey-6")


@ui.page("/chat")
async def chat(q: str | None = None):
    layout("AI 질문")
    with ui.column().classes("w-full max-w-3xl mx-auto gap-4 p-4"):
        ui.label("AI에게 질문하기").classes("text-2xl font-bold")
        ui.label("답변은 수집된 공고만 근거로 하며, 출처를 함께 보여 줍니다.").classes("text-sm text-grey-7")
        box = ui.column().classes("w-full gap-2")
        with ui.row().classes("w-full items-center"):
            inp = ui.input(placeholder="질문을 입력하세요").classes("flex-grow")

            async def send():
                question = (inp.value or "").strip()
                if not question:
                    return
                inp.value = ""
                with box:
                    ui.chat_message(question, name="나", sent=True)
                    spinner = ui.spinner()
                try:
                    res = await api.post("/api/chat", {"question": question})
                except httpx.HTTPError:
                    res = {"answer": "AI 서버에 연결할 수 없습니다. AI 서버(8001번 포트)를 실행하세요.", "sources": []}
                spinner.delete()
                with box:
                    ui.chat_message(res["answer"].split("\n"), name="캠퍼스 메이트")
                    if res.get("sources"):
                        with ui.row().classes("ml-12"):
                            for s in res["sources"]:
                                ui.button(s["title"], on_click=lambda s=s: ui.navigate.to(f"/contests/{s['id']}")) \
                                    .props("outline dense no-caps size=sm")
            inp.on("keydown.enter", send)
            ui.button("보내기", on_click=send)
        if q:
            inp.value = q
            await send()


@ui.page("/calendar")
async def calendar():
    layout("내 일정")
    with ui.column().classes("w-full max-w-3xl mx-auto gap-4 p-4"):
        ui.label("내 일정").classes("text-2xl font-bold")
        ui.label("구글 캘린더 연동은 준비 중입니다. 지금은 이 서비스 안에만 저장됩니다.").classes("text-sm text-grey-7")
        try:
            rows = await api.get("/api/calendar")
        except httpx.HTTPError:
            server_error()
            return
        if not rows:
            ui.label("등록한 공고가 없습니다.").classes("text-grey-7")
        for r in rows:
            c = r["contest"]
            with ui.card().classes("w-full"):
                with ui.row().classes("w-full items-center"):
                    ui.label(d_day(c.get("deadline"))).classes("font-bold text-primary w-16")
                    ui.link(c["title"], f"/contests/{c['id']}").classes("flex-grow")
                    ui.label(f"마감 {c.get('deadline') or '-'}").classes("text-sm text-grey-7")

                    async def remove(entry_id=r["id"]):
                        await api.delete(f"/api/calendar/{entry_id}")
                        ui.navigate.reload()
                    ui.button(icon="delete", on_click=remove).props("flat dense")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8080, title="캠퍼스 메이트", language="ko-KR", reload=False, show=False)
