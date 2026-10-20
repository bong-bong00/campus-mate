"""테이블을 지우고 새로 만든다. 테이블 구조(models.py)를 바꾼 뒤 한 번 실행.

실행: python -m main_server.reset_db        (확인 질문 있음)
      python -m main_server.reset_db --yes  (확인 없이 실행)
주의: 저장된 공고·일정이 모두 지워진다. 실제 수집 데이터가 쌓인 뒤에는 쓰지 말 것.
"""
from .db import Base, engine
from . import models  # noqa: F401  테이블 정의 불러오기
from .seed import seed_if_empty

import sys

if __name__ == "__main__":
    if "--yes" not in sys.argv and input("모든 테이블을 지우고 다시 만듭니다. 계속할까요? (y/n) ").strip().lower() != "y":
        raise SystemExit("취소했습니다.")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    seed_if_empty()
    print("완료: 테이블을 새로 만들고 샘플 공고를 넣었습니다.")
