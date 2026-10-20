"""화면 개발용 샘플 데이터. 실제 공고가 아니며, 크롤러가 동작하면 지워도 된다."""
from datetime import date, timedelta

from sqlalchemy import func, select

from . import models
from .db import SessionLocal

SAMPLES = [
    ("[샘플] 대학생 AI 서비스 아이디어 공모전", "샘플재단", "IT·SW", 20, "대학(원)생, 개인 또는 4인 이하 팀", "대상 300만 원 외",
     "생성형 AI를 활용한 서비스 아이디어를 기획서로 제출하는 공모전."),
    ("[샘플] 공공데이터 활용 앱 개발 경진대회", "샘플시청", "IT·SW", 9, "누구나", "총 상금 1,000만 원",
     "공공데이터를 활용한 웹·앱 결과물을 제출한다. 시연 영상 필수."),
    ("[샘플] 친환경 캠페인 영상 공모전", "샘플환경협회", "영상·UCC", 14, "대학생", "최우수 200만 원",
     "1분 이내의 친환경 캠페인 영상을 제출한다."),
    ("[샘플] 지역 관광 마케팅 기획 공모전", "샘플관광공사", "기획·마케팅", 30, "대학생 3인 이하 팀", "대상 500만 원, 인턴 기회",
     "지역 관광지를 알리는 마케팅 전략을 제안한다."),
    ("[샘플] 캐릭터 디자인 공모전", "샘플문화재단", "디자인", 5, "제한 없음", "대상 150만 원",
     "지역 대표 캐릭터 디자인 시안을 제출한다."),
    ("[샘플] 청년 정책 제안 공모전", "샘플청년센터", "기획·마케팅", 45, "만 19~34세", "우수상 50만 원 외",
     "청년이 체감할 수 있는 정책 아이디어를 제안한다."),
]


def seed_if_empty():
    with SessionLocal() as db:
        if db.scalar(select(func.count()).select_from(models.Contest)):
            return
        today = date.today()
        sources = ["linkareer", "thinkgood", "campuspick"]
        for number, (title, host, category, days_left, eligibility, prize, summary) in enumerate(SAMPLES, 1):
            db.add(models.Contest(
                source=sources[number % 3], source_url=f"https://example.com/sample/{number}",
                title=title, host=host, category=category,
                start_date=today - timedelta(days=7), deadline=today + timedelta(days=days_left),
                eligibility=eligibility, prize=prize, summary=summary,
                organizer="샘플운영사무국" if number % 2 else None,
                apply_url=f"https://example.com/apply/{number}"))
        db.commit()
