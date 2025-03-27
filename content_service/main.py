"""
Content Service main application file.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from common.config import settings
from common.database import Base, get_postgres_engine

from . import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("content_service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    Executes initialization on startup and cleanup on shutdown.
    """
    # Startup
    logger.info("Content Service starting up...")
    
    # Initialize database
    engine = get_postgres_engine()
    if engine:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified")
    else:
        logger.warning("Database engine not available, skipping table creation")
    
    yield
    
    # Shutdown
    logger.info("Content Service shutting down...")


app = FastAPI(
    title="AICHILDEDU Content Service",
    description="Content management service for the AICHILDEDU platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router.router, prefix="/api/v1")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle global exceptions
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "detail": "An internal server error occurred"
        },
    )


@app.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "name": "AICHILDEDU Content Service",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
        "service": "content"
    } 