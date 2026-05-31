"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ehazop_backend.app.core.config import get_settings
from ehazop_backend.app.core.database import init_db, close_db

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="EHAZOP Platform API - SAFOP/EHAZOP Study Management System",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """Handle validation errors with detailed messages."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation Error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    """Handle unexpected exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal Server Error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


# Import and include routers
from ehazop_backend.app.routes import (
    auth_router,
    users_router,
    studies_router,
    hazards_router,
    analysis_router,
    risk_router,
    llm_router,
    knowledge_router,
    actions_router,
    reports_router,
    guidewords_router,
    ws_router,
)

# Mount routers under /api/v1 prefix
app.include_router(auth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(studies_router, prefix="/api/v1")
app.include_router(hazards_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(risk_router, prefix="/api/v1")
app.include_router(llm_router, prefix="/api/v1")
app.include_router(knowledge_router, prefix="/api/v1")
app.include_router(actions_router, prefix="/api/v1")
app.include_router(reports_router, prefix="/api/v1")
app.include_router(guidewords_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/api/v1/openapi.json")
async def get_openapi():
    """Custom OpenAPI endpoint."""
    return app.openapi()