from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config import settings
from routers import apply, tracking, analysis

app = FastAPI(
    title="AI Career Copilot API",
    description="Production-grade AI-powered job application assistant",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(apply.router)
app.include_router(tracking.router)
app.include_router(analysis.router)


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


# Ensure data directory exists on startup
@app.on_event("startup")
async def startup():
    Path(settings.data_file_path).parent.mkdir(parents=True, exist_ok=True)
    data_path = Path(settings.data_file_path)
    if not data_path.exists():
        import json
        from models.schemas import AppData
        with open(data_path, "w") as f:
            json.dump(AppData().model_dump(), f, indent=2)
