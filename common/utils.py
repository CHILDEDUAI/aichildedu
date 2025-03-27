import json
import logging
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Union

logger = logging.getLogger(__name__)

T = TypeVar('T')

def generate_uuid() -> str:
    """Generate a random UUID string"""
    return str(uuid.uuid4())

def validate_uuid(uuid_string: str) -> bool:
    """Validate that a string is a valid UUID"""
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False

def timestamp_now() -> int:
    """Get current timestamp in seconds"""
    return int(datetime.utcnow().timestamp())

def iso_now() -> str:
    """Get current ISO 8601 datetime string"""
    return datetime.utcnow().isoformat()

def to_camel_case(snake_str: str) -> str:
    """Convert snake_case to camelCase"""
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

def to_snake_case(camel_str: str) -> str:
    """Convert camelCase to snake_case"""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel_str)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def dict_keys_to_camel_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all dictionary keys from snake_case to camelCase"""
    return {to_camel_case(k): v for k, v in data.items()}

def dict_keys_to_snake_case(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all dictionary keys from camelCase to snake_case"""
    return {to_snake_case(k): v for k, v in data.items()}

def safe_parse_json(json_str: str, default: Optional[T] = None) -> Union[Dict[str, Any], List[Any], T]:
    """
    Safely parse JSON string
    
    Args:
        json_str: JSON string to parse
        default: Default value to return if parsing fails
        
    Returns:
        Parsed JSON data or default value
    """
    if not json_str:
        return default
        
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        logger.exception(f"Failed to parse JSON: {json_str[:100]}...")
        return default

def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length
    
    Args:
        text: String to truncate
        max_length: Maximum length including suffix
        suffix: String to append if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
        
    return text[:max_length - len(suffix)] + suffix

def remove_html_tags(html_text: str) -> str:
    """
    Remove HTML tags from a string
    
    Args:
        html_text: HTML text to clean
        
    Returns:
        Text with HTML tags removed
    """
    clean = re.compile('<.*?>')
    return re.sub(clean, '', html_text)

def age_group_to_range(age_group: str) -> Dict[str, int]:
    """
    Convert age group string to min/max age range
    
    Args:
        age_group: Age group string, e.g. "3-5", "6-8"
        
    Returns:
        Dictionary with min_age and max_age keys
        
    Raises:
        ValueError: If age_group format is invalid
    """
    try:
        min_age, max_age = map(int, age_group.split('-'))
        return {"min_age": min_age, "max_age": max_age}
    except (ValueError, AttributeError):
        raise ValueError(f"Invalid age group format: {age_group}")

def content_type_to_bucket(content_type: str) -> str:
    """
    Convert content type to storage bucket name
    
    Args:
        content_type: Content type string
        
    Returns:
        Bucket name string
    """
    content_type_map = {
        "storybook": "storybooks",
        "image": "images",
        "audio": "audio",
        "video": "videos",
        "quiz": "quizzes",
        "game": "games",
    }
    
    return content_type_map.get(content_type.lower(), "content")

def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Filename string
        
    Returns:
        File extension without dot
    """
    return filename.split('.')[-1] if '.' in filename else ""

def is_valid_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email is valid, False otherwise
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email)) 