"""FastAPI entry point — ROIlytics backend."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# Import routers
from .routers import predict, analytics, models, instagram, discover
from .services.predictor import PredictorService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-load the ML model on startup so first request is fast."""
    logger.info("🚀 ROIlytics API starting up…")
    try:
        svc = PredictorService.get()
        logger.info(f"✅ Model loaded: {svc.model_name}")
    except Exception as exc:
        logger.error(f"❌ Failed to load model: {exc}")
    yield
    logger.info("🛑 ROIlytics API shutting down…")


app = FastAPI(
    title="ROIlytics API",
    description="Influencer ROI Prediction — FastAPI backend",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS — allow Vite dev server and any localhost port
ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled error on {request.url}")
    return JSONResponse(status_code=500, content={"detail": str(exc)})


# Register routers
app.include_router(predict.router)
app.include_router(analytics.router)
app.include_router(models.router)
app.include_router(instagram.router)
app.include_router(discover.router)


@app.get("/health", tags=["health"])
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "2.0.0"}


@app.get("/", tags=["root"])
async def root():
    return {"message": "ROIlytics API v2.0 — see /docs for interactive API documentation"}
