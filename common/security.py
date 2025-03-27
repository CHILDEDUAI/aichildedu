from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from .config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 token URL will vary by service
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str
    expires_at: datetime

class TokenData(BaseModel):
    """Data contained in JWT token"""
    sub: str  # User ID
    role: str
    exp: datetime
    jti: str  # Unique token ID

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash"""
    return pwd_context.hash(password)

def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token
    
    Args:
        data: Dictionary containing claims to include in the token
        expires_delta: Optional expiration time delta
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Add expiration and issued at times
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": f"{data.get('sub', '')}-{datetime.utcnow().timestamp()}"
    })
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt

def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData object with token claims
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract token data
        token_data = TokenData(
            sub=payload.get("sub"),
            role=payload.get("role"),
            exp=datetime.fromtimestamp(payload.get("exp")),
            jti=payload.get("jti")
        )
        
        return token_data
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    """
    Get current user from token (to be implemented by each service)
    This function should be overridden by each service that needs to
    validate users, typically by making a request to the user service.
    
    Args:
        token: JWT token string
        
    Returns:
        User data dictionary
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token_data = decode_token(token)
    
    # This is a placeholder - actual implementation will depend on the service
    user = {"id": token_data.sub, "role": token_data.role}
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def check_permissions(required_role: Union[str, list]) -> bool:
    """
    Check if user has required role
    
    Args:
        user: User data dictionary
        required_role: Role or list of roles required
        
    Returns:
        True if user has required role
    """
    def _check_user_permissions(user: Dict[str, Any] = Depends(get_current_user)):
        # Convert to list if single role provided
        roles = [required_role] if isinstance(required_role, str) else required_role
        
        # Admin role has access to everything
        if user["role"] == "admin":
            return True
            
        # Check if user has required role
        if user["role"] in roles:
            return True
            
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    
    return _check_user_permissions 