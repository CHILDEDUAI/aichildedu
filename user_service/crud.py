from datetime import datetime, timedelta
from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy.orm import Session

from common.security import get_password_hash, verify_password

from . import models, schemas

# Role CRUD operations
def get_role(db: Session, role_id: int) -> Optional[models.Role]:
    """Get a role by ID"""
    return db.query(models.Role).filter(models.Role.id == role_id).first()

def get_role_by_name(db: Session, name: str) -> Optional[models.Role]:
    """Get a role by name"""
    return db.query(models.Role).filter(models.Role.name == name).first()

def get_roles(db: Session, skip: int = 0, limit: int = 100) -> List[models.Role]:
    """Get all roles with pagination"""
    return db.query(models.Role).offset(skip).limit(limit).all()

def create_role(db: Session, role: schemas.RoleCreate) -> models.Role:
    """Create a new role"""
    db_role = models.Role(
        name=role.name,
        description=role.description,
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role

def update_role(db: Session, role_id: int, role: schemas.RoleUpdate) -> Optional[models.Role]:
    """Update a role"""
    db_role = get_role(db, role_id)
    if db_role is None:
        return None
        
    update_data = role.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_role, key, value)
        
    db.commit()
    db.refresh(db_role)
    return db_role

def delete_role(db: Session, role_id: int) -> bool:
    """Delete a role"""
    db_role = get_role(db, role_id)
    if db_role is None:
        return False
        
    db.delete(db_role)
    db.commit()
    return True

# User CRUD operations
def get_user(db: Session, user_id: UUID) -> Optional[models.User]:
    """Get a user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get a user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_users(
    db: Session, 
    skip: int = 0, 
    limit: int = 100, 
    is_active: Optional[bool] = None
) -> List[models.User]:
    """
    Get all users with pagination and optional filtering
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        is_active: Filter by active status if provided
        
    Returns:
        List of users
    """
    query = db.query(models.User)
    
    if is_active is not None:
        query = query.filter(models.User.is_active == is_active)
        
    return query.offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """
    Create a new user
    
    Args:
        db: Database session
        user: User data
        
    Returns:
        Created user
    """
    # Hash the password
    hashed_password = get_password_hash(user.password)
    
    # Create the user
    db_user = models.User(
        email=user.email,
        password=hashed_password,
        full_name=user.full_name,
        role_id=user.role_id,
        profile_image=user.profile_image,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create default user settings
    db_settings = models.UserSettings(user_id=db_user.id)
    db.add(db_settings)
    db.commit()
    
    return db_user

def update_user(
    db: Session, 
    user_id: UUID, 
    user: schemas.UserUpdate
) -> Optional[models.User]:
    """
    Update a user
    
    Args:
        db: Database session
        user_id: User ID
        user: User data to update
        
    Returns:
        Updated user or None if not found
    """
    db_user = get_user(db, user_id)
    if db_user is None:
        return None
        
    update_data = user.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
        
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_password(
    db: Session, 
    user_id: UUID, 
    current_password: str, 
    new_password: str
) -> bool:
    """
    Update user password
    
    Args:
        db: Database session
        user_id: User ID
        current_password: Current password for verification
        new_password: New password to set
        
    Returns:
        True if password was updated, False otherwise
    """
    db_user = get_user(db, user_id)
    if db_user is None:
        return False
        
    # Verify current password
    if not verify_password(current_password, db_user.password):
        return False
        
    # Hash and set new password
    db_user.password = get_password_hash(new_password)
    db.commit()
    
    return True

def delete_user(db: Session, user_id: UUID) -> bool:
    """
    Delete a user
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        True if user was deleted, False if not found
    """
    db_user = get_user(db, user_id)
    if db_user is None:
        return False
        
    db.delete(db_user)
    db.commit()
    return True

# User Settings CRUD operations
def get_user_settings(db: Session, user_id: UUID) -> Optional[models.UserSettings]:
    """Get user settings by user ID"""
    return db.query(models.UserSettings).filter(models.UserSettings.user_id == user_id).first()

def create_user_settings(
    db: Session, 
    user_id: UUID, 
    settings: schemas.UserSettingsCreate
) -> models.UserSettings:
    """Create user settings"""
    db_settings = models.UserSettings(
        user_id=user_id,
        **settings.dict(),
    )
    db.add(db_settings)
    db.commit()
    db.refresh(db_settings)
    return db_settings

def update_user_settings(
    db: Session, 
    user_id: UUID, 
    settings: schemas.UserSettingsUpdate
) -> Optional[models.UserSettings]:
    """Update user settings"""
    db_settings = get_user_settings(db, user_id)
    if db_settings is None:
        return None
        
    update_data = settings.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_settings, key, value)
        
    db.commit()
    db.refresh(db_settings)
    return db_settings

# Child CRUD operations
def get_child(db: Session, child_id: UUID) -> Optional[models.Child]:
    """Get a child by ID"""
    return db.query(models.Child).filter(models.Child.id == child_id).first()

def get_children_by_parent(
    db: Session, 
    parent_id: UUID, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.Child]:
    """Get all children for a parent"""
    return db.query(models.Child).filter(
        models.Child.parent_id == parent_id
    ).offset(skip).limit(limit).all()

def create_child(
    db: Session, 
    parent_id: UUID, 
    child: schemas.ChildCreate
) -> models.Child:
    """Create a new child account"""
    # Create child
    db_child = models.Child(
        parent_id=parent_id,
        **child.dict(),
    )
    db.add(db_child)
    db.commit()
    db.refresh(db_child)
    
    # Create default preferences
    db_preferences = models.ChildPreferences(child_id=db_child.id)
    db.add(db_preferences)
    
    # Create default restrictions
    db_restrictions = models.ChildRestrictions(child_id=db_child.id)
    db.add(db_restrictions)
    
    db.commit()
    
    return db_child

def update_child(
    db: Session, 
    child_id: UUID, 
    child: schemas.ChildUpdate
) -> Optional[models.Child]:
    """Update a child account"""
    db_child = get_child(db, child_id)
    if db_child is None:
        return None
        
    update_data = child.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_child, key, value)
        
    db.commit()
    db.refresh(db_child)
    return db_child

def delete_child(db: Session, child_id: UUID) -> bool:
    """Delete a child account"""
    db_child = get_child(db, child_id)
    if db_child is None:
        return False
        
    db.delete(db_child)
    db.commit()
    return True

# Child Preferences CRUD operations
def get_child_preferences(db: Session, child_id: UUID) -> Optional[models.ChildPreferences]:
    """Get child preferences by child ID"""
    return db.query(models.ChildPreferences).filter(
        models.ChildPreferences.child_id == child_id
    ).first()

def update_child_preferences(
    db: Session, 
    child_id: UUID, 
    preferences: schemas.ChildPreferencesUpdate
) -> Optional[models.ChildPreferences]:
    """Update child preferences"""
    db_preferences = get_child_preferences(db, child_id)
    if db_preferences is None:
        return None
        
    update_data = preferences.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_preferences, key, value)
        
    db_preferences.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_preferences)
    return db_preferences

# Child Restrictions CRUD operations
def get_child_restrictions(db: Session, child_id: UUID) -> Optional[models.ChildRestrictions]:
    """Get child restrictions by child ID"""
    return db.query(models.ChildRestrictions).filter(
        models.ChildRestrictions.child_id == child_id
    ).first()

def update_child_restrictions(
    db: Session, 
    child_id: UUID, 
    restrictions: schemas.ChildRestrictionsUpdate
) -> Optional[models.ChildRestrictions]:
    """Update child restrictions"""
    db_restrictions = get_child_restrictions(db, child_id)
    if db_restrictions is None:
        return None
        
    update_data = restrictions.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_restrictions, key, value)
        
    db_restrictions.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_restrictions)
    return db_restrictions

# Password Reset CRUD operations
def create_password_reset(db: Session, user_id: UUID, token: str, expires_hours: int = 24) -> models.PasswordReset:
    """Create a password reset token"""
    # Expire any existing tokens
    db.query(models.PasswordReset).filter(
        models.PasswordReset.user_id == user_id,
        models.PasswordReset.used == False
    ).update({"used": True})
    
    # Create new token
    expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
    db_reset = models.PasswordReset(
        user_id=user_id,
        token=token,
        expires_at=expires_at,
    )
    db.add(db_reset)
    db.commit()
    db.refresh(db_reset)
    return db_reset

def get_password_reset_by_token(db: Session, token: str) -> Optional[models.PasswordReset]:
    """Get a password reset token"""
    return db.query(models.PasswordReset).filter(
        models.PasswordReset.token == token,
        models.PasswordReset.used == False,
        models.PasswordReset.expires_at > datetime.utcnow()
    ).first()

def use_password_reset(db: Session, token: str) -> bool:
    """Mark a password reset token as used"""
    db_reset = get_password_reset_by_token(db, token)
    if db_reset is None:
        return False
        
    db_reset.used = True
    db.commit()
    return True

# Login History CRUD operations
def create_login_history(
    db: Session, 
    user_id: UUID, 
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    device_info: Optional[dict] = None,
    success: bool = True
) -> models.LoginHistory:
    """Record a login attempt"""
    db_login = models.LoginHistory(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        device_info=device_info,
        success=success,
    )
    db.add(db_login)
    db.commit()
    db.refresh(db_login)
    return db_login

def get_login_history(
    db: Session, 
    user_id: UUID, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.LoginHistory]:
    """Get login history for a user"""
    return db.query(models.LoginHistory).filter(
        models.LoginHistory.user_id == user_id
    ).order_by(
        models.LoginHistory.login_time.desc()
    ).offset(skip).limit(limit).all() 