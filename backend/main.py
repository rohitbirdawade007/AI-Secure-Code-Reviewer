import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import get_settings
from backend.routers import upload, scan, github_api, report

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure runtime directories exist
    os.makedirs(settings.uploads_dir, exist_ok=True)
    os.makedirs(settings.reports_dir, exist_ok=True)
    yield


app = FastAPI(
    title="AI Secure Code Reviewer",
    description=(
        "Upload Python code, run Semgrep static analysis, and get AI-powered "
        "vulnerability explanations with secure fix suggestions."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API Routers ───────────────────────────────────────────────────────────────
app.include_router(upload.router,     prefix="/api", tags=["Upload"])
app.include_router(scan.router,       prefix="/api", tags=["Scan"])
app.include_router(github_api.router, prefix="/api", tags=["GitHub"])
app.include_router(report.router,     prefix="/api", tags=["Report"])

# ── Serve generated reports as static files ───────────────────────────────────
app.mount("/reports", StaticFiles(directory=settings.reports_dir), name="reports")

# ── Serve frontend ────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory="frontend"), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("frontend/index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
    }
