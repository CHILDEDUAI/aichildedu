"""
Common utilities for the AI Children Education Platform.
This package provides shared utilities, database connections,
security implementations, and configuration that can be used
across all microservices.
"""

from .config import settings
from .database import (
    Base, 
    close_mongodb_connection,
    ensure_bucket_exists,
    get_db_session, 
    get_minio_client,
    get_mongodb_client, 
    get_mongodb_collection, 
    get_mongodb_database, 
    get_postgres_engine,
)
from .http_client import ServiceClient, create_service_client
from .security import (
    Token,
    TokenData,
    create_access_token,
    decode_token,
    get_current_user,
    get_password_hash,
    verify_password,
)
from .utils import (
    age_group_to_range,
    content_type_to_bucket,
    dict_keys_to_camel_case,
    dict_keys_to_snake_case,
    generate_uuid,
    get_file_extension,
    is_valid_email,
    iso_now,
    remove_html_tags,
    safe_parse_json,
    timestamp_now,
    to_camel_case,
    to_snake_case,
    truncate_string,
    validate_uuid,
)

__all__ = [
    # Config
    'settings',
    
    # Database
    'Base',
    'close_mongodb_connection',
    'ensure_bucket_exists',
    'get_db_session',
    'get_minio_client',
    'get_mongodb_client',
    'get_mongodb_collection',
    'get_mongodb_database',
    'get_postgres_engine',
    
    # HTTP Client
    'ServiceClient',
    'create_service_client',
    
    # Security
    'Token',
    'TokenData',
    'create_access_token',
    'decode_token',
    'get_current_user',
    'get_password_hash',
    'verify_password',
    
    # Utils
    'age_group_to_range',
    'content_type_to_bucket',
    'dict_keys_to_camel_case',
    'dict_keys_to_snake_case',
    'generate_uuid',
    'get_file_extension',
    'is_valid_email',
    'iso_now',
    'remove_html_tags',
    'safe_parse_json',
    'timestamp_now',
    'to_camel_case',
    'to_snake_case',
    'truncate_string',
    'validate_uuid',
] 