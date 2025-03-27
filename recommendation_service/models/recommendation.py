"""
Recommendation Service Database Models
"""

from datetime import datetime
from typing import List
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Table
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PgUUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from common.database import Base

# Association tables
content_similarities = Table(
    'content_similarities',
    Base.metadata,
    Column('content_id_1', PgUUID(as_uuid=True), ForeignKey('contents.id'), primary_key=True),
    Column('content_id_2', PgUUID(as_uuid=True), ForeignKey('contents.id'), primary_key=True),
    Column('similarity_score', Float, nullable=False),
    Column('created_at', DateTime(timezone=True), server_default=func.now()),
)

class UserPreference(Base):
    """User preferences for content recommendations"""
    __tablename__ = 'user_preferences'

    id = Column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PgUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    preferred_subjects = Column(ARRAY(String), default=[])
    preferred_content_types = Column(ARRAY(String), default=[])
    preferred_difficulty_levels = Column(ARRAY(String), default=[])
    learning_style = Column(String)
    interests = Column(ARRAY(String), default=[])
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class UserContentInteraction(Base):
    """User interactions with content for recommendation tracking"""
    __tablename__ = 'user_content_interactions'

    id = Column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PgUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content_id = Column(PgUUID(as_uuid=True), ForeignKey('contents.id', ondelete='CASCADE'), nullable=False)
    interaction_type = Column(String, nullable=False)  # view, complete, like, bookmark
    engagement_score = Column(Float, default=0.0)
    time_spent = Column(Integer, default=0)  # seconds
    progress = Column(Float, default=0.0)  # percentage
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class RecommendationHistory(Base):
    """History of recommendations made to users"""
    __tablename__ = 'recommendation_history'

    id = Column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(PgUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content_id = Column(PgUUID(as_uuid=True), ForeignKey('contents.id', ondelete='CASCADE'), nullable=False)
    recommendation_type = Column(String, nullable=False)  # collaborative, content-based, hybrid
    score = Column(Float, nullable=False)
    is_clicked = Column(Boolean, default=False)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ContentFeatureVector(Base):
    """Content feature vectors for content-based recommendations"""
    __tablename__ = 'content_feature_vectors'

    id = Column(PgUUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id = Column(PgUUID(as_uuid=True), ForeignKey('contents.id', ondelete='CASCADE'), nullable=False, unique=True)
    feature_vector = Column(ARRAY(Float), nullable=False)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 