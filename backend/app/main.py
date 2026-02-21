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
	"""Configure and verify Tesseract on startup"""
	import pytesseract
	
	# Set Tesseract path - will try to find it in PATH
	# Render container has it at /usr/bin/tesseract from Dockerfile
	pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"
	
	# Verify it works
	try:
		result = subprocess.run(["/usr/bin/tesseract", "--version"], capture_output=True, text=True, timeout=5)
		if result.returncode == 0:
			version_info = result.stdout.split('\n')[0] if result.stdout else "installed"
			logger.info(f"✓ Tesseract OCR ready: {version_info}")
		else:
			logger.error(f"✗ Tesseract test failed with code {result.returncode}")
			logger.error(f"  stderr: {result.stderr}")
	except FileNotFoundError:
		logger.error("✗ Tesseract binary not found at /usr/bin/tesseract")
		logger.error("  Image uploads will fail. Check Dockerfile installation.")
	except Exception as e:
		logger.error(f"✗ Tesseract verification failed: {e}")


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
