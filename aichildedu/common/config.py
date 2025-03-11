import os
from typing import List

from pydantic import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

class Settings(BaseSettings):
    """
    Base settings class that loads configuration from environment variables.
    This class is intended to be inherited by service-specific settings classes.
    """
    # Application settings
    APP_NAME: str = "AI Children Education Platform"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Database URLs
    DATABASE_URL: str = os.getenv("DATABASE_URL", "")
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
    MONGODB_DB: str = os.getenv("MONGODB_DB", "aiedu")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Authentication
    SECRET_KEY: str = os.getenv("SECRET_KEY", "super-secret-key-change-in-production")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # Services URLs
    SERVICE_USER: str = os.getenv("SERVICE_USER", "http://localhost:8001/api/v1")
    SERVICE_CONTENT: str = os.getenv("SERVICE_CONTENT", "http://localhost:8002/api/v1")
    SERVICE_LEARNING: str = os.getenv("SERVICE_LEARNING", "http://localhost:8003/api/v1")
    SERVICE_AI_TEXT: str = os.getenv("SERVICE_AI_TEXT", "http://localhost:8010/api/v1")
    SERVICE_AI_IMAGE: str = os.getenv("SERVICE_AI_IMAGE", "http://localhost:8011/api/v1")
    SERVICE_AI_VOICE: str = os.getenv("SERVICE_AI_VOICE", "http://localhost:8012/api/v1")
    SERVICE_AI_VIDEO: str = os.getenv("SERVICE_AI_VIDEO", "http://localhost:8013/api/v1")
    SERVICE_RECOMMENDATION: str = os.getenv("SERVICE_RECOMMENDATION", "http://localhost:8020/api/v1")
    SERVICE_ANALYTICS: str = os.getenv("SERVICE_ANALYTICS", "http://localhost:8030/api/v1")
    
    # API Gateway specific settings
    USER_SERVICE_URL: str = os.getenv("USER_SERVICE_URL", "http://localhost:8001")
    CONTENT_SERVICE_URL: str = os.getenv("CONTENT_SERVICE_URL", "http://localhost:8002")
    LEARNING_SERVICE_URL: str = os.getenv("LEARNING_SERVICE_URL", "http://localhost:8003")
    AI_TEXT_SERVICE_URL: str = os.getenv("AI_TEXT_SERVICE_URL", "http://localhost:8010")
    AI_IMAGE_SERVICE_URL: str = os.getenv("AI_IMAGE_SERVICE_URL", "http://localhost:8011")
    AI_VOICE_SERVICE_URL: str = os.getenv("AI_VOICE_SERVICE_URL", "http://localhost:8012")
    AI_VIDEO_SERVICE_URL: str = os.getenv("AI_VIDEO_SERVICE_URL", "http://localhost:8013")
    RECOMMENDATION_SERVICE_URL: str = os.getenv("RECOMMENDATION_SERVICE_URL", "http://localhost:8020")
    ANALYTICS_SERVICE_URL: str = os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8030")
    
    # Rate limiting
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    RATE_LIMIT_MAX_REQUESTS: int = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100"))
    
    # CORS settings
    CORS_ORIGINS: List[str] = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # External API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # MinIO / S3 Configuration
    MINIO_ENDPOINT: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    MINIO_SECURE: bool = os.getenv("MINIO_SECURE", "False").lower() in ("true", "1", "t")
    
    # Content generation settings
    USE_FALLBACK_MODEL: bool = os.getenv("USE_FALLBACK_MODEL", "True").lower() in ("true", "1", "t")
    
    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        case_sensitive = True

# Create a singleton instance of settings that can be imported
settings = Settings() 