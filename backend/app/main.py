from datetime import datetime, timezone
import logging
import os
import subprocess
import shutil

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.auth import router as auth_router
from .routes.ask import router as ask_router
from .routes.memory import router as memory_router
from .routes.upload import router as upload_router


LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
	level=getattr(logging, LOG_LEVEL, logging.INFO),
	format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

logger = logging.getLogger(__name__)


app = FastAPI(
	title="MemoryVault AI Backend",
	version="0.1.0",
)


frontend_urls = os.getenv("FRONTEND_URLS", "http://localhost:3000")
allowed_origins = [url.strip() for url in frontend_urls.split(",") if url.strip()]


app.add_middleware(
	CORSMiddleware,
	allow_origins=allowed_origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


app.include_router(memory_router)
app.include_router(upload_router)
app.include_router(ask_router)
app.include_router(auth_router)


@app.on_event("startup")
def startup_event():
	"""Verify critical dependencies on startup"""
	logger.info("Starting up MemoryVault AI Backend...")
	logger.info("  - Using Gemini API for embeddings and chat")
	logger.info("  - Using EasyOCR for image text extraction (pure Python, no external dependencies)")
	logger.info("✓ Backend initialized successfully")


@app.get("/")
def root() -> dict[str, str]:
	return {"message": "MemoryVault AI backend running"}


@app.api_route("/health", methods=["GET", "HEAD"])
def health() -> dict[str, str]:
	return {
		"status": "healthy",
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"service": "memoryvault-backend",
	}
