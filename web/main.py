"""웹 화면(NiceGUI).

실행: python -m web.main   →  http://127.0.0.1:8080
"""
from datetime import date

import httpx
from nicegui import ui

from . import api

SOURCE_NAMES = {"linkareer": "링커리어", "thinkgood": "씽굿", "campuspick": "캠퍼스픽"}
CATEGORY_ICONS = {"IT·SW": "computer", "디자인": "palette", "영상·UCC": "movie",
                  "기획·마케팅": "lightbulb"}


def get_category_icon(category: str | None) -> str:
    return CATEGORY_ICONS.get(category or "", "emoji_events")


def show_poster(contest: dict, size: str = "w-48 h-64"):
    """포스터는 원본 주소로만 불러온다(저장하지 않음). 없거나 안 뜨면 분야 아이콘."""
    with ui.element("div").classes(f"{size} rounded-lg bg-blue-50 flex items-center justify-center overflow-hidden"):
        icon = ui.icon(get_category_icon(contest.get("category")), size="64px").classes("text-primary")
        if contest.get("poster_url"):
            icon.set_visibility(False)
            image = ui.element("img").props(f'src="{contest["poster_url"]}" referrerpolicy="no-referrer"') \
                .classes("w-full h-full object-cover")

            def show_icon_instead():
                image.set_visibility(False)
                icon.set_visibility(True)
            image.on("error", show_icon_instead)


def format_d_day(deadline: str | None) -> str:
    if not deadline:
        return "상시"
    days_left = (date.fromisoformat(deadline) - date.today()).days
    return "D-day" if days_left == 0 else (f"D-{days_left}" if days_left > 0 else "마감")


def show_header(title: str):
    ui.colors(primary="#2C7BE5")
    with ui.header().classes("items-center bg-white text-black shadow-sm"):
        ui.link("캠퍼스 메이트", "/").classes("text-lg font-bold no-underline text-primary")
        ui.space()
        for label, path in [("공고", "/contests"), ("AI 질문", "/chat"), ("내 일정", "/calendar")]:
            ui.link(label, path).classes("no-underline text-black mx-2")
    ui.page_title(f"{title} | 캠퍼스 메이트")


def show_contest_card(contest: dict):
    with ui.card().classes("w-full cursor-pointer hover:shadow-md").on(
            "click", lambda contest=contest: ui.navigate.to(f"/contests/{contest['id']}")):
        with ui.row().classes("w-full items-center"):
            ui.icon(get_category_icon(contest.get("category"))).classes("text-primary")
            ui.badge(contest.get("category") or "기타").props("outline")
            ui.label(SOURCE_NAMES.get(contest["source"], contest["source"])).classes("text-xs text-grey-6")
            ui.space()
            ui.label(format_d_day(contest.get("deadline"))).classes("font-bold text-primary")
        ui.label(contest["title"]).classes("text-base font-semibold")
        ui.label(f"{contest.get('host') or ''} · 마감 {contest.get('deadline') or '-'}").classes("text-sm text-grey-7")


def show_server_error():
    ui.label("메인 서버에 연결할 수 없습니다. 메인 서버(8000번 포트)를 먼저 실행하세요.").classes("text-negative")


@ui.page("/")
async def home_page():
    show_header("홈")
    with ui.column().classes("w-full max-w-4xl mx-auto gap-6 p-4"):
        ui.label("흩어진 공모전, 한곳에서 찾고 AI에게 물어보세요").classes("text-2xl font-bold")
        with ui.row().classes("w-full items-center"):
            question_input = ui.input(placeholder="예: 이번 달 마감하는 IT 공모전 알려 줘").classes("flex-grow")
            ui.button("AI에게 질문", on_click=lambda: ui.navigate.to(f"/chat?question={question_input.value}"))
        try:
            categories = await api.get("/api/categories")
            contests = await api.get("/api/contests", limit=4)
        except httpx.HTTPError:
            show_server_error()
            return
        ui.label("분야").classes("text-lg font-semibold")
        with ui.row():
            for category in categories:
                ui.button(category, on_click=lambda category=category: ui.navigate.to(f"/contests?category={category}")) \
                    .props("outline")
        ui.label("마감 임박").classes("text-lg font-semibold")
        for contest in contests:
            show_contest_card(contest)


@ui.page("/contests")
async def contest_list_page(category: str | None = None, keyword: str | None = None):
    show_header("공고")
    with ui.column().classes("w-full max-w-4xl mx-auto gap-4 p-4"):
        ui.label("공모전 공고").classes("text-2xl font-bold")
        try:
            categories = await api.get("/api/categories")
        except httpx.HTTPError:
            show_server_error()
            return
        with ui.row().classes("w-full items-center"):
            category_select = ui.select(["전체"] + categories, value=category or "전체", label="분야").classes("w-40")
            keyword_input = ui.input("검색어", value=keyword or "").classes("flex-grow")

            def search():
                params = []
                if category_select.value and category_select.value != "전체":
                    params.append(f"category={category_select.value}")
                if keyword_input.value:
                    params.append(f"keyword={keyword_input.value}")
                ui.navigate.to("/contests" + ("?" + "&".join(params) if params else ""))
            keyword_input.on("keydown.enter", search)
            ui.button("검색", on_click=search)
        contests = await api.get("/api/contests", category=category, keyword=keyword)
        if not contests:
            ui.label("조건에 맞는 공고가 없습니다.").classes("text-grey-7")
        for contest in contests:
            show_contest_card(contest)


@ui.page("/contests/{contest_id}")
async def contest_detail_page(contest_id: int):
    show_header("공고 상세")
    with ui.column().classes("w-full max-w-3xl mx-auto gap-4 p-4"):
        try:
            contest = await api.get(f"/api/contests/{contest_id}")
        except httpx.HTTPError:
            ui.label("공고를 불러올 수 없습니다.").classes("text-negative")
            return
        with ui.row().classes("items-center"):
            ui.badge(contest.get("category") or "기타").props("outline")
            ui.label(format_d_day(contest.get("deadline"))).classes("font-bold text-primary")
        ui.label(contest["title"]).classes("text-2xl font-bold")
        with ui.row().classes("w-full items-start no-wrap gap-4"):
            show_poster(contest)
            with ui.card().classes("flex-grow"):
                for label, key in [("주최", "host"), ("주관", "organizer"), ("접수 시작", "start_date"),
                                   ("마감일", "deadline"), ("참가 자격", "eligibility"), ("시상", "prize")]:
                    if key == "organizer" and not contest.get(key):
                        continue
                    with ui.row().classes("w-full no-wrap"):
                        ui.label(label).classes("w-24 shrink-0 text-grey-7")
                        ui.label(contest.get(key) or "-")
        ui.label("요약").classes("text-lg font-semibold")
        ui.label(contest.get("summary") or "요약 준비 중")
        with ui.row():
            async def add_to_calendar():
                await api.post("/api/calendar", {"contest_id": contest_id})
                ui.notify("내 일정에 등록했습니다", type="positive")
            if contest.get("apply_url"):
                ui.button("지원하기", icon="send",
                          on_click=lambda: ui.navigate.to(contest["apply_url"], new_tab=True))
            ui.button("내 일정에 등록", icon="event", on_click=add_to_calendar).props("outline")
            ui.button(f"{SOURCE_NAMES.get(contest['source'], '원문')}에서 보기", icon="open_in_new",
                      on_click=lambda: ui.navigate.to(contest["source_url"], new_tab=True)).props("flat")
        ui.label(f"출처: {SOURCE_NAMES.get(contest['source'], contest['source'])} · 상세 내용은 원문에서 확인하세요. "
                 "포스터는 원문 사이트의 이미지를 그대로 불러옵니다.").classes("text-xs text-grey-6")


@ui.page("/chat")
async def chat_page(question: str | None = None):
    show_header("AI 질문")
    with ui.column().classes("w-full max-w-3xl mx-auto gap-4 p-4"):
        ui.label("AI에게 질문하기").classes("text-2xl font-bold")
        ui.label("답변은 수집된 공고만 근거로 하며, 출처를 함께 보여 줍니다.").classes("text-sm text-grey-7")
        message_box = ui.column().classes("w-full gap-2")
        with ui.row().classes("w-full items-center"):
            question_input = ui.input(placeholder="질문을 입력하세요").classes("flex-grow")

            async def send_question():
                question_text = (question_input.value or "").strip()
                if not question_text:
                    return
                question_input.value = ""
                with message_box:
                    ui.chat_message(question_text, name="나", sent=True)
                    spinner = ui.spinner()
                try:
                    reply = await api.post("/api/chat", {"question": question_text})
                except httpx.HTTPError:
                    reply = {"answer": "AI 서버에 연결할 수 없습니다. AI 서버(8001번 포트)를 실행하세요.", "sources": []}
                spinner.delete()
                with message_box:
                    ui.chat_message(reply["answer"].split("\n"), name="캠퍼스 메이트")
                    if reply.get("sources"):
                        with ui.row().classes("ml-12"):
                            for source in reply["sources"]:
                                ui.button(source["title"],
                                          on_click=lambda source=source: ui.navigate.to(f"/contests/{source['id']}")) \
                                    .props("outline dense no-caps size=sm")
            question_input.on("keydown.enter", send_question)
            ui.button("보내기", on_click=send_question)
        if question:
            question_input.value = question
            await send_question()


@ui.page("/calendar")
async def calendar_page():
    show_header("내 일정")
    with ui.column().classes("w-full max-w-3xl mx-auto gap-4 p-4"):
        ui.label("내 일정").classes("text-2xl font-bold")
        ui.label("구글 캘린더 연동은 준비 중입니다. 지금은 이 서비스 안에만 저장됩니다.").classes("text-sm text-grey-7")
        try:
            entries = await api.get("/api/calendar")
        except httpx.HTTPError:
            show_server_error()
            return
        if not entries:
            ui.label("등록한 공고가 없습니다.").classes("text-grey-7")
        for entry in entries:
            contest = entry["contest"]
            with ui.card().classes("w-full"):
                with ui.row().classes("w-full items-center"):
                    ui.label(format_d_day(contest.get("deadline"))).classes("font-bold text-primary w-16")
                    ui.link(contest["title"], f"/contests/{contest['id']}").classes("flex-grow")
                    ui.label(f"마감 {contest.get('deadline') or '-'}").classes("text-sm text-grey-7")

                    async def remove_entry(entry_id=entry["id"]):
                        await api.delete(f"/api/calendar/{entry_id}")
                        ui.navigate.reload()
                    ui.button(icon="delete", on_click=remove_entry).props("flat dense")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(port=8080, title="캠퍼스 메이트", language="ko-KR", reload=False, show=False)
