import logging
from typing import Any, Dict, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from .config import settings

# Set up logging
logger = logging.getLogger(__name__)

# PostgreSQL Setup
Base = declarative_base()

def get_postgres_engine(database_url: Optional[str] = None):
    """Create SQLAlchemy engine"""
    db_url = database_url or settings.DATABASE_URL
    
    if not db_url:
        logger.warning("DATABASE_URL not set. PostgreSQL connection disabled.")
        return None
    
    try:
        engine = create_engine(
            db_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )
        return engine
    except Exception as e:
        logger.error(f"Failed to create PostgreSQL engine: {e}")
        return None

def get_db_session(engine=None):
    """Create a sessionmaker for PostgreSQL"""
    if engine is None:
        engine = get_postgres_engine()
        
    if engine is None:
        return None
        
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Define dependency
    def get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
            
    return get_db

# MongoDB Setup
_mongo_client: Optional[AsyncIOMotorClient] = None
_mongo_db: Optional[AsyncIOMotorDatabase] = None

async def get_mongodb_client() -> AsyncIOMotorClient:
    """Get MongoDB client singleton"""
    global _mongo_client
    
    if _mongo_client is None:
        try:
            mongo_uri = settings.MONGODB_URI
            _mongo_client = AsyncIOMotorClient(mongo_uri)
            # Ping the server to confirm connection
            await _mongo_client.admin.command('ping')
            logger.info("Connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
            
    return _mongo_client

async def get_mongodb_database() -> AsyncIOMotorDatabase:
    """Get MongoDB database singleton"""
    global _mongo_db
    
    if _mongo_db is None:
        client = await get_mongodb_client()
        _mongo_db = client[settings.MONGODB_DB]
        
    return _mongo_db

async def get_mongodb_collection(collection_name: str):
    """Get MongoDB collection"""
    db = await get_mongodb_database()
    return db[collection_name]

async def close_mongodb_connection():
    """Close MongoDB connection"""
    global _mongo_client
    
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        logger.info("Closed MongoDB connection")

# Minio / S3 Object Storage Setup
try:
    from minio import Minio
    
    _minio_client = None
    
    def get_minio_client():
        """Get MinIO client singleton"""
        global _minio_client
        
        if _minio_client is None:
            try:
                _minio_client = Minio(
                    settings.MINIO_ENDPOINT,
                    access_key=settings.MINIO_ACCESS_KEY,
                    secret_key=settings.MINIO_SECRET_KEY,
                    secure=settings.MINIO_SECURE
                )
                logger.info("Connected to MinIO/S3")
            except Exception as e:
                logger.error(f"Failed to connect to MinIO/S3: {e}")
                raise
                
        return _minio_client
    
    def ensure_bucket_exists(bucket_name: str):
        """Ensure that a bucket exists, creating it if necessary"""
        client = get_minio_client()
        
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"Created bucket: {bucket_name}")
            
except ImportError:
    logger.warning("MinIO client not installed. Object storage functionality disabled.")
    
    def get_minio_client():
        return None
        
    def ensure_bucket_exists(bucket_name: str):
        pass 