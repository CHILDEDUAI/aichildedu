import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer

from aichildedu.common.config import settings
from aichildedu.common.exceptions import APIError

from .middleware import (
    LoggingMiddleware,
    RateLimitingMiddleware,
    RequestValidationMiddleware,
)
from .routes import router
from .services import ServiceRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api_gateway")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    Executes initialization on startup and cleanup on shutdown.
    """
    # Startup
    logger.info("API Gateway starting up...")
    
    # Initialize service registry
    app.state.service_registry = ServiceRegistry()
    await app.state.service_registry.initialize()
    
    yield
    
    # Shutdown
    logger.info("API Gateway shutting down...")
    
    # Cleanup resources
    await app.state.service_registry.close()


app = FastAPI(
    title="AICHILDEDU API Gateway",
    description="API Gateway for the AICHILDEDU platform",
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

# Add custom middleware
app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(RequestValidationMiddleware)

# Include API routes
app.include_router(router)


@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """
    Handle API errors
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "detail": exc.detail,
            "meta": exc.meta
        },
    )


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
        "name": "AICHILDEDU API Gateway",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    # Check the health of all registered services
    service_health = await app.state.service_registry.check_health()
    
    all_healthy = all(service["status"] == "healthy" for service in service_health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": "0.1.0",
        "services": service_health
    } 