from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.auth import router as auth_router
from .routes.ask import router as ask_router
from .routes.memory import router as memory_router
from .routes.upload import router as upload_router


app = FastAPI(
	title="MemoryVault AI Backend",
	version="0.1.0",
)


app.add_middleware(
	CORSMiddleware,
	allow_origins=["http://localhost:3000"],
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
def health() -> dict[str, str]:
	return {
		"status": "ok",
		"timestamp": datetime.now(timezone.utc).isoformat(),
	}
