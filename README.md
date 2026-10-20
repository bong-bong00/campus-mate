# 캠퍼스 메이트 (기초 코드)

공모전 공고를 모아 보여 주고, AI에게 질문하면 관련 공고를 찾아 출처와 함께 답하는 웹 서비스의 뼈대입니다.
지금은 **샘플 데이터 + 임시 AI 흐름**으로 화면과 서버 연결만 동작합니다.

## 구조

```
웹 화면(NiceGUI, 8080) → 메인 서버(FastAPI, 8000) → AI 서버(FastAPI, 8001)
                              │                          │ 도구 호출(검색·상세·캘린더)
                              ▼                          └──────→ 메인 서버 API
                         DB(SQLite → MariaDB)
크롤러(python -m crawler.run) ──→ DB
```

- 웹 화면은 **메인 서버만** 호출합니다. AI 서버도 DB에 직접 접근하지 않고 메인 서버 API를 도구로 씁니다.
- 원문 전체는 저장하지 않습니다. 핵심 항목(주최, 마감일, 자격, 시상, 분야) + 요약 + 원문 링크만 저장합니다.

| 폴더 | 내용 |
| --- | --- |
| `main_server/` | 공고 조회·검색, AI 질문 전달, 캘린더 API, DB 모델, 샘플 데이터 |
| `ai_server/` | 에이전트(`app.py`)와 도구(`tools.py`) |
| `web/` | 화면 5개: 홈, 공고 목록, 공고 상세, AI 질문, 내 일정 |
| `crawler/` | 수집 공통 규칙(`base.py`), 사이트별 수집기(`sites/`), 실행(`run.py`) |

## 실행

```bash
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

한 번에 켜기(권장): `python run_all.py` → 끌 때 Ctrl+C

따로 켜려면 터미널 3개를 열고 프로젝트 폴더에서 각각 실행합니다.

```bash
uvicorn main_server.app:app --port 8000 --reload   # 1. 메인 서버 (먼저)
uvicorn ai_server.app:app --port 8001 --reload     # 2. AI 서버
python -m web.main                                 # 3. 웹 화면
```

- 화면: http://127.0.0.1:8080
- 메인 서버 API 문서: http://127.0.0.1:8000/docs
- 처음 실행하면 `campusmate.db`(SQLite)가 생기고 `[샘플]` 공고 6건이 들어갑니다. 실제 공고가 아닙니다.

## MariaDB로 바꾸기 (WBS 2.2)

1. MariaDB에서 `CREATE DATABASE campusmate CHARACTER SET utf8mb4;`
2. `.env.example`을 `.env`로 복사하고 `DATABASE_URL=mysql+pymysql://아이디:비밀번호@localhost:3306/campusmate?charset=utf8mb4`
3. 메인 서버를 다시 실행하면 테이블이 자동 생성됩니다.

## 테이블 구조를 바꿨을 때

`main_server/models.py`에 칸을 추가하면 이미 만들어진 테이블에는 자동으로 반영되지 않습니다.
서버를 끈 상태에서 `python -m main_server.reset_db`를 실행하면 테이블을 새로 만들고 샘플 공고를 다시 넣습니다.
**저장된 데이터가 모두 지워지므로** 실제 수집 데이터가 쌓인 뒤에는 쓰지 마세요.

## 다음 작업 위치 (WBS 번호)

| 작업 | 파일 | 할 일 |
| --- | --- | --- |
| 3.1~3.3 크롤러 | `crawler/sites/*.py` | `crawl()` 채우기. 요청 간격·User-Agent는 `base.py`가 처리 |
| 3.4 스케줄러 | `crawler/run.py` | 하루 1~2회 자동 실행 |
| 4.1, 4.4 에이전트 | `ai_server/app.py`의 `run_agent` | 임시 키워드 검색을 LLM 도구 호출 반복으로 교체. 도구 정의는 `tools.TOOL_SPECS` |
| 4.2 수집 에이전트 | `crawler/run.py`의 `save` | `page_text`를 AI 서버로 보내 핵심 추출·요약 후 저장 |
| 5.1~5.2 구글 캘린더 | `main_server/app.py`의 `add_calendar` | 구글 로그인, 일정 생성 후 `google_event_id` 저장 |

## 수집 운영 원칙

1. 사실 정보만 저장, 요약은 새로 작성, 원문은 링크로 제공
2. 하루 1~2회, 요청 사이 3초 간격 (`crawler/base.py`의 `REQUEST_DELAY_SEC`)
3. 비영리 학교 프로젝트, 공개 주소로 배포하지 않음
4. 링커리어 내부 API 호출 금지, 씽굿 첨부파일 수집 금지 (robots.txt)
