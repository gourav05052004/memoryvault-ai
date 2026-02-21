from datetime import datetime, timezone
import logging
import os
import subprocess

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
	import subprocess
	import shutil
	
	# Check Tesseract in multiple locations
	tesseract_locations = [
		"/usr/bin/tesseract",
		"/usr/local/bin/tesseract",
		"/bin/tesseract",
		"tesseract",
	]
	
	found_path = None
	for path in tesseract_locations:
		try:
			result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
			if result.returncode == 0:
				found_path = path
				logger.info(f"✓ Tesseract OCR found at: {path}")
				logger.info(f"  Version: {result.stdout.split(chr(10))[0]}")
				break
		except (FileNotFoundError, subprocess.TimeoutExpired):
			continue
	
	if found_path:
		# Set the path for pytesseract
		import pytesseract
		pytesseract.pytesseract.tesseract_cmd = found_path
		logger.info(f"✓ Pytesseract configured to use: {found_path}")
	else:
		logger.error("✗ Tesseract OCR not found in any standard location")
		logger.error("  Checked: " + ", ".join(tesseract_locations))


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
