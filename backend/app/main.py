from datetime import datetime, timezone
import logging
import os

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


@app.get("/")
def root() -> dict[str, str]:
	return {"message": "MemoryVault AI backend running"}


@app.get("/health")
def health_check() -> dict[str, str]:
	"""Health check endpoint for monitoring and deployment platforms"""
	return {
		"status": "healthy",
		"timestamp": datetime.now(timezone.utc).isoformat(),
		"service": "memoryvault-backend"
	}


@app.get("/health")
def health() -> dict[str, str]:
	return {
		"status": "ok",
		"timestamp": datetime.now(timezone.utc).isoformat(),
	}
