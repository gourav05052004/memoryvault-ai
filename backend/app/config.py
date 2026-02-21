import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_CHAT_MODEL: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-3-flash-preview")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "")
JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-in-production")
JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
