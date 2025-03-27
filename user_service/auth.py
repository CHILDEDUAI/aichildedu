import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from aichildedu.common.config import settings
from aichildedu.common.security import (create_access_token, get_password_hash,
                                      verify_password)

from . import crud, models, schemas

# Configure OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

def authenticate_user(
    db: Session, 
    email: str, 
    password: str
) -> Optional[models.User]:
    """
    Authenticate a user with email and password
    
    Args:
        db: Database session
        email: User email
        password: User password
        
    Returns:
        User if authentication is successful, None otherwise
    """
    user = crud.get_user_by_email(db, email)
    if not user:
        return None
        
    if not verify_password(password, user.password):
        return None
        
    if not user.is_active:
        return None
        
    return user

def get_current_user(
    db: Session, 
    token: str = Depends(oauth2_scheme)
) -> models.User:
    """
    Get the current user from token
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        User model
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # Extract user ID
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
        
    # Get user from database
    user = crud.get_user(db, user_id)
    if user is None or not user.is_active:
        raise credentials_exception
        
    return user

def login_user(
    db: Session, 
    email: str, 
    password: str,
    request: Optional[Request] = None
) -> Tuple[models.User, str, datetime]:
    """
    Login a user and generate a token
    
    Args:
        db: Database session
        email: User email
        password: User password
        request: FastAPI request object (for logging IP and user agent)
        
    Returns:
        Tuple of (user, token, expiry_time)
        
    Raises:
        HTTPException: If login fails
    """
    # Authenticate user
    user = authenticate_user(db, email, password)
    
    if not user:
        # Log failed login attempt if we found a user with this email
        existing_user = crud.get_user_by_email(db, email)
        if existing_user:
            crud.create_login_history(
                db,
                user_id=existing_user.id,
                ip_address=str(request.client.host) if request and request.client else None,
                user_agent=request.headers.get("user-agent") if request else None,
                success=False
            )
            
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with user information
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role.name  # Assumes relationship is loaded
    }
    
    access_token = create_access_token(
        data=token_data, 
        expires_delta=access_token_expires
    )
    
    # Calculate expiry time
    expiry_time = datetime.utcnow() + access_token_expires
    
    # Log successful login
    if request:
        crud.create_login_history(
            db,
            user_id=user.id,
            ip_address=str(request.client.host) if request.client else None,
            user_agent=request.headers.get("user-agent"),
            success=True
        )
    
    return user, access_token, expiry_time

def generate_password_reset_token(db: Session, email: str) -> Optional[str]:
    """
    Generate a password reset token for a user
    
    Args:
        db: Database session
        email: User email
        
    Returns:
        Reset token if user is found, None otherwise
    """
    user = crud.get_user_by_email(db, email)
    if not user:
        return None
        
    # Generate secure token
    token = secrets.token_urlsafe(32)
    
    # Store token in database
    crud.create_password_reset(db, user.id, token)
    
    return token

def reset_password_with_token(
    db: Session, 
    token: str, 
    new_password: str
) -> bool:
    """
    Reset a user's password using a reset token
    
    Args:
        db: Database session
        token: Reset token
        new_password: New password
        
    Returns:
        True if password was reset, False if token is invalid
    """
    # Get token from database
    db_token = crud.get_password_reset_by_token(db, token)
    if not db_token:
        return False
        
    # Get user
    user = crud.get_user(db, db_token.user_id)
    if not user:
        return False
        
    # Update password
    user.password = get_password_hash(new_password)
    db.commit()
    
    # Mark token as used
    crud.use_password_reset(db, token)
    
    return True

def check_admin_access(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Check if user has admin access
    
    Args:
        user: Current user
        
    Returns:
        User if they have admin access
        
    Raises:
        HTTPException: If user does not have admin access
    """
    if user.role.name != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return user

def check_parent_or_admin_access(user: models.User = Depends(get_current_user)) -> models.User:
    """
    Check if user has parent or admin access
    
    Args:
        user: Current user
        
    Returns:
        User if they have parent or admin access
        
    Raises:
        HTTPException: If user does not have parent or admin access
    """
    if user.role.name not in ["parent", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return user 