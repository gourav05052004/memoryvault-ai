import asyncio
from datetime import datetime, timezone
from contextlib import asynccontextmanager
import logging
import os
import time

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import status
from fastapi.responses import JSONResponse

from .db.mongo import mongo
from .services.supabase_service import supabase
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

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
	scheduler.start()
	yield
	scheduler.shutdown()


app = FastAPI(
	title="MemoryVault AI Backend",
	version="0.1.0",
	lifespan=lifespan,
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


async def _ping_mongo(timeout_seconds: float = 3.0) -> bool:
	try:
		await asyncio.wait_for(
			asyncio.to_thread(lambda: mongo.db.command("ping")),
			timeout=timeout_seconds,
		)
		return True
	except Exception:
		logger.exception("MongoDB ping failed")
		return False


async def _ping_supabase(timeout_seconds: float = 3.0) -> bool:
	try:
		await asyncio.wait_for(
			asyncio.to_thread(lambda: supabase.storage.from_("memoryvault").list()),
			timeout=timeout_seconds,
		)
		return True
	except Exception:
		logger.exception("Supabase Storage ping failed")
		return False


@scheduler.scheduled_job("interval", hours=24)
async def keep_supabase_alive():
	await _ping_supabase()


@app.on_event("startup")
def startup_event():
	"""Verify critical dependencies on startup"""
	logger.info("Starting up MemoryVault AI Backend...")
	logger.info("  - Using Gemini API for embeddings and chat")
	logger.info("  - Using OCR.space API for image text extraction")
	logger.info("✓ Backend initialized successfully")


@app.get("/")
def root() -> dict[str, str]:
	return {"message": "MemoryVault AI backend running"}


@app.api_route("/health", methods=["GET", "HEAD"])
async def health() -> dict[str, str | int]:
	return {"status": "ok", "ts": int(time.time()), "version": "1.0.0"}


@app.get("/health/deep")
async def deep_health() -> JSONResponse:
	mongo_ok, supabase_ok = await asyncio.gather(_ping_mongo(), _ping_supabase())
	all_ok = mongo_ok and supabase_ok
	return JSONResponse(
		status_code=status.HTTP_200_OK if all_ok else status.HTTP_503_SERVICE_UNAVAILABLE,
		content={"mongodb": mongo_ok, "supabase": supabase_ok},
	)
