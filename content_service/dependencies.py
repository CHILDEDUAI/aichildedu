"""
Dependencies for the content service.
"""

from typing import Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from aichildedu.common.config import settings

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.USER_SERVICE_URL}/api/v1/auth/token"
)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict:
    """
    Validate the access token and return the current user.
    This is a simplified version that just decodes the JWT token.
    In a production environment, we would also verify the token with the user service.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        # Extract user information from the token
        user_data = {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
            "is_admin": payload.get("role") == "admin",
        }
        
        return user_data
        
    except JWTError:
        raise credentials_exception

async def get_optional_user(token: Optional[str] = Depends(oauth2_scheme)) -> Optional[Dict]:
    """
    Similar to get_current_user but doesn't raise an exception if token is invalid or missing.
    Returns None instead.
    """
    if not token:
        return None
    
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        # Extract user information from the token
        user_data = {
            "id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role"),
            "is_admin": payload.get("role") == "admin",
        }
        
        return user_data
        
    except JWTError:
        return None 