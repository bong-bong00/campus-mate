"""공통 설정. .env 파일이 있으면 읽어 온다."""
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./campusmate.db"
MAIN_SERVER_URL = os.getenv("MAIN_SERVER_URL", "http://127.0.0.1:8000")
AI_SERVER_URL = os.getenv("AI_SERVER_URL", "http://127.0.0.1:8001")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
