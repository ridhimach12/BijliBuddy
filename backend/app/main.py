"""FastAPI application entrypoint for BijliBuddy."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.db.base import Base
from app.db.seed import ensure_service_categories, seed_database
from app.db.session import SessionLocal, engine
from app.ml.issue_classifier import get_issue_classifier
from app.ml.price_estimator import get_price_estimator
from app.routers import admin, auth, bookings, customers, electricians, ml, public


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize DB tables, seed demo data if empty, and warm up ML models."""
    settings = get_settings()
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.ML_ARTIFACTS_DIR).mkdir(parents=True, exist_ok=True)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _, categories_created = ensure_service_categories(db)
        if categories_created > 0:
            db.commit()
        if settings.AUTO_SEED_ON_EMPTY:
            seed_database(db)
    finally:
        db.close()

    get_issue_classifier()
    get_price_estimator()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=(
        "AI-powered hyperlocal electrician marketplace API with TF-IDF issue classification, "
        "Haversine weighted matching, Random Forest INR price estimation, Bayesian reliability "
        "scoring, statistical demand forecasting, and electrical safety guardrails."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

upload_path = Path(settings.UPLOAD_DIR)
upload_path.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(ml.router)
app.include_router(customers.router)
app.include_router(electricians.router)
app.include_router(bookings.router)
app.include_router(admin.router)


@app.get("/api/health", tags=["Health"])
def health_check():
    """Health check endpoint for Render/Vercel monitoring."""
    return {
        "status": "ok",
        "service": "BijliBuddy API",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
