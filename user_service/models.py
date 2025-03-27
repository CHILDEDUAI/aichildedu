from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from sqlalchemy import (Boolean, Column, Date, DateTime, ForeignKey, Integer,
                        String, Table, Text)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from aichildedu.common.database import Base

# User roles table
class Role(Base):
    """User role model"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    
    # Relationships
    users = relationship("User", back_populates="role")

# User model
class User(Base):
    """User model representing parent, teacher or admin accounts"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    profile_image = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    role = relationship("Role", back_populates="users")
    children = relationship("Child", back_populates="parent", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")

# User settings
class UserSettings(Base):
    """User settings model for preferences"""
    __tablename__ = "user_settings"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    language = Column(String, default="en")
    theme = Column(String, default="light")
    email_notifications = Column(Boolean, default=True)
    push_notifications = Column(Boolean, default=True)
    preferences = Column(JSONB, default={})
    
    # Relationships
    user = relationship("User", back_populates="settings")

# Child model
class Child(Base):
    """Child model representing a child account"""
    __tablename__ = "children"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    display_name = Column(String, nullable=False)
    avatar = Column(String)
    birth_date = Column(Date)
    grade = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("User", back_populates="children")
    preferences = relationship("ChildPreferences", back_populates="child", uselist=False, cascade="all, delete-orphan")
    restrictions = relationship("ChildRestrictions", back_populates="child", uselist=False, cascade="all, delete-orphan")

# Child preferences
class ChildPreferences(Base):
    """Child preferences model"""
    __tablename__ = "child_preferences"
    
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), primary_key=True)
    subjects = Column(ARRAY(String), default=[])
    difficulty_level = Column(String, default="medium")
    preferred_characters = Column(JSONB, default=[])
    preferred_styles = Column(JSONB, default=[])
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    child = relationship("Child", back_populates="preferences")

# Child restrictions
class ChildRestrictions(Base):
    """Child restrictions model for parental controls"""
    __tablename__ = "child_restrictions"
    
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), primary_key=True)
    daily_time_limit = Column(Integer)  # Minutes per day
    content_rating = Column(String, default="G")
    restricted_topics = Column(ARRAY(String), default=[])
    require_approval = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    child = relationship("Child", back_populates="restrictions")

# Login history
class LoginHistory(Base):
    """Login history model for tracking user logins"""
    __tablename__ = "login_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    login_time = Column(DateTime(timezone=True), server_default=func.now())
    ip_address = Column(String)
    user_agent = Column(String)
    device_info = Column(JSONB)
    success = Column(Boolean, default=True)

# Password reset tokens
class PasswordReset(Base):
    """Password reset token model"""
    __tablename__ = "password_resets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False) 