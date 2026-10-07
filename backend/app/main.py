from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from slowapi.errors import RateLimitExceeded

from app.api.routes.auth import router as auth_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from app.core.rate_limit import limiter, rate_limit_exceeded_handler

app = FastAPI(
    title="GARUDA API",
    description="Multimodal scam, phishing and suspicious-content detection platform for Indian users.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Attach in-memory SlowAPI rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS Middleware (Source of Truth: ARCHITECTURE Section 9 and 10)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standardized Error Handlers (ARCHITECTURE Section 6)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API Routers
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")


@app.get("/", include_in_schema=False)
def root():
    return {
        "service": "GARUDA API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/health",
    }
