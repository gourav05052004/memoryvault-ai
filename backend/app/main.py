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
	"""Configure Tesseract path and verify on startup"""
	import pytesseract
	
	# Render container has Tesseract at /usr/bin/tesseract from our Dockerfile
	pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
	
	# Try a quick version check
	try:
		result = subprocess.run(["/usr/bin/tesseract", "--version"], 
							   capture_output=True, text=True, timeout=3)
		if result.returncode == 0:
			version = result.stdout.split('\n')[0]
			logger.info(f"✓ Tesseract OCR configured and ready: {version}")
			return
	except Exception as e:
		logger.error(f"Tesseract check failed: {e}")
		# Continue anyway - may still work


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
