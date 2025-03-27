from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

# Base schemas
class RoleBase(BaseModel):
    """Base schema for user roles"""
    name: str
    description: Optional[str] = None
    
class RoleCreate(RoleBase):
    """Schema for creating a new role"""
    pass
    
class RoleUpdate(RoleBase):
    """Schema for updating a role"""
    name: Optional[str] = None
    
class RoleResponse(RoleBase):
    """Response schema for roles"""
    id: int

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    """Base schema for users"""
    email: EmailStr
    full_name: str
    profile_image: Optional[str] = None
    
class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str
    role_id: int = 1  # Default to parent role
    
class UserUpdate(BaseModel):
    """Schema for updating a user"""
    full_name: Optional[str] = None
    profile_image: Optional[str] = None
    is_active: Optional[bool] = None

class UserPasswordUpdate(BaseModel):
    """Schema for updating user password"""
    current_password: str
    new_password: str

class UserSettingsBase(BaseModel):
    """Base schema for user settings"""
    language: Optional[str] = "en"
    theme: Optional[str] = "light"
    email_notifications: Optional[bool] = True
    push_notifications: Optional[bool] = True
    preferences: Optional[Dict[str, Any]] = {}
    
class UserSettingsCreate(UserSettingsBase):
    """Schema for creating user settings"""
    pass
    
class UserSettingsUpdate(UserSettingsBase):
    """Schema for updating user settings"""
    pass
    
class UserSettingsResponse(UserSettingsBase):
    """Response schema for user settings"""
    user_id: UUID

    class Config:
        orm_mode = True
        
class ChildBase(BaseModel):
    """Base schema for children"""
    display_name: str
    avatar: Optional[str] = None
    birth_date: Optional[date] = None
    grade: Optional[int] = None
    
class ChildCreate(ChildBase):
    """Schema for creating a child"""
    pass
    
class ChildUpdate(BaseModel):
    """Schema for updating a child"""
    display_name: Optional[str] = None
    avatar: Optional[str] = None
    birth_date: Optional[date] = None
    grade: Optional[int] = None

class ChildPreferencesBase(BaseModel):
    """Base schema for child preferences"""
    subjects: Optional[List[str]] = []
    difficulty_level: Optional[str] = "medium"
    preferred_characters: Optional[List[Dict[str, Any]]] = []
    preferred_styles: Optional[List[str]] = []
    
class ChildPreferencesCreate(ChildPreferencesBase):
    """Schema for creating child preferences"""
    pass
    
class ChildPreferencesUpdate(ChildPreferencesBase):
    """Schema for updating child preferences"""
    pass
    
class ChildPreferencesResponse(ChildPreferencesBase):
    """Response schema for child preferences"""
    child_id: UUID
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        
class ChildRestrictionsBase(BaseModel):
    """Base schema for child restrictions"""
    daily_time_limit: Optional[int] = 60  # 60 minutes default
    content_rating: Optional[str] = "G"
    restricted_topics: Optional[List[str]] = []
    require_approval: Optional[bool] = False
    
class ChildRestrictionsCreate(ChildRestrictionsBase):
    """Schema for creating child restrictions"""
    pass
    
class ChildRestrictionsUpdate(ChildRestrictionsBase):
    """Schema for updating child restrictions"""
    pass
    
class ChildRestrictionsResponse(ChildRestrictionsBase):
    """Response schema for child restrictions"""
    child_id: UUID
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Response schemas
class ChildResponse(ChildBase):
    """Response schema for children"""
    id: UUID
    parent_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    preferences: Optional[ChildPreferencesResponse] = None
    restrictions: Optional[ChildRestrictionsResponse] = None

    class Config:
        orm_mode = True

class UserResponse(UserBase):
    """Response schema for users"""
    id: UUID
    role: RoleResponse
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    settings: Optional[UserSettingsResponse] = None
    children: List[ChildResponse] = []

    class Config:
        orm_mode = True

# Authentication schemas
class LoginRequest(BaseModel):
    """Schema for login requests"""
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """Schema for token responses"""
    access_token: str
    token_type: str = "bearer"
    expires_at: int
    user: UserResponse

class PasswordResetRequest(BaseModel):
    """Schema for password reset requests"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Schema for confirming password resets"""
    token: str
    new_password: str 