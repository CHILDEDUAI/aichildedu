import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine

from common.config import settings
from common.database import Base, get_postgres_engine

from . import models, router

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Database setup
engine = get_postgres_engine()

# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle management for the FastAPI application
    """
    # Startup: Create database tables
    logger.info("Creating database tables if they don't exist")
    Base.metadata.create_all(bind=engine)
    
    # Initialize default roles if they don't exist
    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    
    from . import crud, schemas
    
    # Create default roles if they don't exist
    roles = [
        {"name": "admin", "description": "Administrator with full access"},
        {"name": "parent", "description": "Parent user with children management access"},
        {"name": "teacher", "description": "Teacher with limited content management access"},
    ]
    
    for role_data in roles:
        role = crud.get_role_by_name(db, role_data["name"])
        if not role:
            logger.info(f"Creating default role: {role_data['name']}")
            crud.create_role(db, schemas.RoleCreate(**role_data))
    
    # Create admin user if it doesn't exist
    admin_email = "admin@example.com"
    admin = crud.get_user_by_email(db, admin_email)
    if not admin:
        logger.info(f"Creating default admin user: {admin_email}")
        admin_role = crud.get_role_by_name(db, "admin")
        crud.create_user(
            db,
            schemas.UserCreate(
                email=admin_email,
                password="adminpassword",  # This should be changed after first login
                full_name="System Admin",
                role_id=admin_role.id,
            ),
        )
    
    db.close()
    
    logger.info("User service startup complete")
    yield
    
    # Shutdown
    logger.info("User service shutting down")

# Create FastAPI application
app = FastAPI(
    title="AI Children Education Platform - User Service",
    description="User management and authentication service",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Should be restricted in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Error handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred"},
    )

# Include API routes
app.include_router(router.router, prefix="/api/v1")

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "User Service",
        "version": "0.1.0",
        "status": "healthy",
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    # Run application with uvicorn
    uvicorn.run(
        "aichildedu.user_service.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG,
    ) 