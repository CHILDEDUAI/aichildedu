from datetime import datetime
from typing import List
from uuid import uuid4

from sqlalchemy import (Boolean, Column, DateTime, Enum, ForeignKey, Index,
                        Integer, String, Table, Text)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from aichildedu.common.database import Base

# Content categories association table
content_categories = Table(
    "content_categories",
    Base.metadata,
    Column("content_id", UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True),
    Column("category_id", Integer, ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True)
)

# Content tags association table
content_tags = Table(
    "content_tags",
    Base.metadata,
    Column("content_id", UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
)

# Child content history association table (for tracking viewed content)
child_content_history = Table(
    "child_content_history",
    Base.metadata,
    Column("child_id", UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), primary_key=True),
    Column("content_id", UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True),
    Column("viewed_at", DateTime(timezone=True), server_default=func.now(), primary_key=True),
    Column("progress", Integer, default=0),  # Progress percentage
    Column("completion_status", String, default="started"),  # started, in_progress, completed
    Column("rating", Integer),  # User rating
    Column("notes", Text)
)

class Category(Base):
    """Content category model"""
    __tablename__ = "categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    parent_id = Column(Integer, ForeignKey("categories.id", ondelete="SET NULL"))
    icon = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    parent = relationship("Category", remote_side=[id], backref="subcategories")
    contents = relationship("Content", secondary=content_categories, back_populates="categories")

class Tag(Base):
    """Content tag model"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    contents = relationship("Content", secondary=content_tags, back_populates="tags")

class Content(Base):
    """Base content model for all types of educational content"""
    __tablename__ = "contents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    content_type = Column(String, nullable=False, index=True)  # story, quiz, lesson, etc.
    status = Column(String, default="draft", index=True)  # draft, published, archived
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    is_ai_generated = Column(Boolean, default=False)
    generation_task_id = Column(String, index=True)  # Reference to AI generation task
    min_age = Column(Integer, default=3)
    max_age = Column(Integer, default=12)
    language = Column(String, default="en", index=True)
    reading_time_minutes = Column(Integer)
    difficulty_level = Column(String, default="medium")  # easy, medium, hard
    content_rating = Column(String, default="G")  # G, PG, etc.
    educational_value = Column(ARRAY(String), default=[])
    subjects = Column(ARRAY(String), default=[])
    metadata = Column(JSONB, default={})
    thumbnail_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True))
    
    # Type discriminator
    type = Column(String(50))
    
    __mapper_args__ = {
        "polymorphic_on": type,
        "polymorphic_identity": "content"
    }
    
    # Relationships
    categories = relationship("Category", secondary=content_categories, back_populates="contents")
    tags = relationship("Tag", secondary=content_tags, back_populates="contents")
    assets = relationship("ContentAsset", back_populates="content", cascade="all, delete-orphan")
    reactions = relationship("ContentReaction", back_populates="content", cascade="all, delete-orphan")
    
    # Create an index on multiple columns for efficient content filtering
    __table_args__ = (
        Index('ix_content_filter', content_type, language, min_age, max_age, status),
    )

class Story(Content):
    """Story content model"""
    __tablename__ = "stories"
    
    id = Column(UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True)
    story_content = Column(JSONB, nullable=False)  # Structured story content with pages
    characters = Column(JSONB, default=[])
    themes = Column(ARRAY(String), default=[])
    moral_lesson = Column(String)
    has_images = Column(Boolean, default=False)
    has_audio = Column(Boolean, default=False)
    has_interactive_elements = Column(Boolean, default=False)
    word_count = Column(Integer)
    
    __mapper_args__ = {
        "polymorphic_identity": "story",
    }

class Quiz(Content):
    """Quiz content model"""
    __tablename__ = "quizzes"
    
    id = Column(UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True)
    questions = Column(JSONB, nullable=False)  # Array of question objects
    answer_key = Column(JSONB, nullable=False)  # Correct answers
    topic = Column(String, index=True)
    question_count = Column(Integer)
    time_limit_minutes = Column(Integer)
    passing_score = Column(Integer)
    
    __mapper_args__ = {
        "polymorphic_identity": "quiz",
    }

class Lesson(Content):
    """Lesson content model"""
    __tablename__ = "lessons"
    
    id = Column(UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), primary_key=True)
    lesson_content = Column(JSONB, nullable=False)  # Structured lesson content
    learning_objectives = Column(ARRAY(String), default=[])
    prerequisites = Column(ARRAY(String), default=[])
    related_content_ids = Column(ARRAY(UUID(as_uuid=True)), default=[])
    
    __mapper_args__ = {
        "polymorphic_identity": "lesson",
    }

class ContentAsset(Base):
    """Content asset model for multimedia assets"""
    __tablename__ = "content_assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), nullable=False)
    asset_type = Column(String, nullable=False)  # image, audio, video, document
    file_url = Column(String, nullable=False)
    file_key = Column(String, nullable=False)  # Storage key
    mime_type = Column(String)
    size_bytes = Column(Integer)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    content = relationship("Content", back_populates="assets")

class ContentReaction(Base):
    """Content reaction model for likes, ratings, etc."""
    __tablename__ = "content_reactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    content_id = Column(UUID(as_uuid=True), ForeignKey("contents.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"))
    reaction_type = Column(String, nullable=False)  # like, favorite, rating
    rating_value = Column(Integer)  # 1-5 star rating
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    content = relationship("Content", back_populates="reactions")
    
    # Unique constraint to prevent duplicate reactions
    __table_args__ = (
        Index('ix_unique_reaction', content_id, user_id, child_id, reaction_type, unique=True),
    )

class ContentCollection(Base):
    """Content collection model for curated content sets"""
    __tablename__ = "content_collections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    description = Column(Text)
    creator_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    is_public = Column(Boolean, default=False)
    content_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=[])
    collection_type = Column(String, default="custom")  # custom, curriculum, featured
    thumbnail_url = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 