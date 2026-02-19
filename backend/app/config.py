import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")


GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_CHAT_MODEL: str = os.getenv("GROQ_CHAT_MODEL", "llama-3.3-70b-versatile")
GROQ_EMBEDDING_MODEL: str = os.getenv("GROQ_EMBEDDING_MODEL", "text-embedding-3-small")
MONGO_URI: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
TESSERACT_CMD: str = os.getenv("TESSERACT_CMD", "")
