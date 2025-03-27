import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from common.config import settings
from common.exceptions import APIError

from .routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("text_generator")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle management
    Execute initialization when the application starts, and cleanup when it shuts down
    """
    # Execute initialization when the application starts
    logger.info("Text generation service starting...")
    
    # Perform any necessary initialization
    # For example, connecting to the database, initializing models, etc.
    
    yield
    
    # Execute cleanup when the application shuts down
    logger.info("Text generation service shutting down...")
    
    # Perform any necessary cleanup
    # For example, closing database connections, etc.


app = FastAPI(
    title="AI Children Education Platform - Text Generation Service",
    description="Provides story and quiz generation functionality for the AI Children Education Platform",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, this should be limited to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api/v1/ai")


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
    Root path response
    """
    return {
        "name": "AI Children Education Platform - Text Generation Service",
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
        "version": "0.1.0"
    } 