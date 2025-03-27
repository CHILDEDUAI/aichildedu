from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator

# Enums for validation
class ContentType(str, Enum):
    STORY = "story"
    QUIZ = "quiz"
    LESSON = "lesson"
    ACTIVITY = "activity"

class ContentStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"

class ContentRating(str, Enum):
    G = "G"  # General Audience
    PG = "PG"  # Parental Guidance
    PG13 = "PG13"  # Parental Guidance for children under 13

class AssetType(str, Enum):
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"

class ReactionType(str, Enum):
    LIKE = "like"
    FAVORITE = "favorite"
    RATING = "rating"

# Base schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    icon: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(CategoryBase):
    name: Optional[str] = None

class CategoryInDB(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class TagBase(BaseModel):
    name: str
    description: Optional[str] = None

class TagCreate(TagBase):
    pass

class TagUpdate(TagBase):
    name: Optional[str] = None

class TagInDB(TagBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True

class ContentAssetBase(BaseModel):
    asset_type: AssetType
    file_url: str
    file_key: str
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata: Dict[str, Any] = {}

class ContentAssetCreate(ContentAssetBase):
    content_id: UUID

class ContentAssetUpdate(BaseModel):
    asset_type: Optional[AssetType] = None
    file_url: Optional[str] = None
    file_key: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None

class ContentAssetInDB(ContentAssetBase):
    id: UUID
    content_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

class ContentReactionBase(BaseModel):
    reaction_type: ReactionType
    rating_value: Optional[int] = None
    
    @validator('rating_value')
    def validate_rating(cls, v, values):
        if values.get('reaction_type') == ReactionType.RATING and (v is None or v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

class ContentReactionCreate(ContentReactionBase):
    content_id: UUID
    child_id: Optional[UUID] = None

class ContentReactionUpdate(BaseModel):
    rating_value: Optional[int] = None

class ContentReactionInDB(ContentReactionBase):
    id: UUID
    content_id: UUID
    user_id: UUID
    child_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        orm_mode = True

# Base content schema shared by all content types
class ContentBase(BaseModel):
    title: str
    description: Optional[str] = None
    content_type: ContentType
    min_age: Optional[int] = 3
    max_age: Optional[int] = 12
    language: str = "en"
    reading_time_minutes: Optional[int] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.MEDIUM
    content_rating: ContentRating = ContentRating.G
    educational_value: List[str] = []
    subjects: List[str] = []
    metadata: Dict[str, Any] = {}
    thumbnail_url: Optional[str] = None
    
    @validator('min_age', 'max_age')
    def validate_age_range(cls, v, values, **kwargs):
        if 'min_age' in values and 'max_age' in kwargs['field'].name and v < values['min_age']:
            raise ValueError("max_age must be greater than or equal to min_age")
        return v

class ContentCreate(ContentBase):
    category_ids: List[int] = []
    tag_ids: List[int] = []

class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ContentStatus] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    language: Optional[str] = None
    reading_time_minutes: Optional[int] = None
    difficulty_level: Optional[DifficultyLevel] = None
    content_rating: Optional[ContentRating] = None
    educational_value: Optional[List[str]] = None
    subjects: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    thumbnail_url: Optional[str] = None
    category_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None

class ContentInDB(ContentBase):
    id: UUID
    status: ContentStatus
    creator_id: Optional[UUID] = None
    is_ai_generated: bool
    generation_task_id: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    categories: List[CategoryInDB] = []
    tags: List[TagInDB] = []
    
    class Config:
        orm_mode = True

# Story specific schemas
class StoryContent(BaseModel):
    pages: List[Dict[str, Any]]  # List of page objects with text and image references
    characters: List[Dict[str, str]] = []
    themes: List[str] = []

class StoryBase(BaseModel):
    story_content: StoryContent
    moral_lesson: Optional[str] = None
    has_images: bool = False
    has_audio: bool = False
    has_interactive_elements: bool = False
    word_count: Optional[int] = None

class StoryCreate(ContentCreate, StoryBase):
    content_type: ContentType = ContentType.STORY

class StoryUpdate(ContentUpdate, StoryBase):
    story_content: Optional[StoryContent] = None

class StoryInDB(ContentInDB, StoryBase):
    class Config:
        orm_mode = True

# Quiz specific schemas
class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    explanation: Optional[str] = None
    image_url: Optional[str] = None

class QuizBase(BaseModel):
    questions: List[QuizQuestion]
    answer_key: Dict[int, int]  # Maps question index to correct option index
    topic: Optional[str] = None
    question_count: int
    time_limit_minutes: Optional[int] = None
    passing_score: Optional[int] = None

class QuizCreate(ContentCreate, QuizBase):
    content_type: ContentType = ContentType.QUIZ

class QuizUpdate(ContentUpdate, QuizBase):
    questions: Optional[List[QuizQuestion]] = None
    answer_key: Optional[Dict[int, int]] = None
    question_count: Optional[int] = None

class QuizInDB(ContentInDB, QuizBase):
    class Config:
        orm_mode = True

# Lesson specific schemas
class LessonContent(BaseModel):
    sections: List[Dict[str, Any]]  # List of lesson sections
    activities: Optional[List[Dict[str, Any]]] = None

class LessonBase(BaseModel):
    lesson_content: LessonContent
    learning_objectives: List[str] = []
    prerequisites: List[str] = []
    related_content_ids: List[UUID] = []

class LessonCreate(ContentCreate, LessonBase):
    content_type: ContentType = ContentType.LESSON

class LessonUpdate(ContentUpdate, LessonBase):
    lesson_content: Optional[LessonContent] = None
    learning_objectives: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    related_content_ids: Optional[List[UUID]] = None

class LessonInDB(ContentInDB, LessonBase):
    class Config:
        orm_mode = True

# Content Collection schemas
class ContentCollectionBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_public: bool = False
    content_ids: List[UUID] = []
    collection_type: str = "custom"
    thumbnail_url: Optional[str] = None

class ContentCollectionCreate(ContentCollectionBase):
    pass

class ContentCollectionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    content_ids: Optional[List[UUID]] = None
    collection_type: Optional[str] = None
    thumbnail_url: Optional[str] = None

class ContentCollectionInDB(ContentCollectionBase):
    id: UUID
    creator_id: Optional[UUID] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True

# Query parameter models
class ContentFilter(BaseModel):
    content_type: Optional[List[ContentType]] = None
    category_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None
    status: Optional[List[ContentStatus]] = None
    language: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    difficulty_level: Optional[List[DifficultyLevel]] = None
    content_rating: Optional[List[ContentRating]] = None
    creator_id: Optional[UUID] = None
    is_ai_generated: Optional[bool] = None
    subjects: Optional[List[str]] = None
    search_query: Optional[str] = None
    
class ContentSort(str, Enum):
    CREATED_ASC = "created_asc"
    CREATED_DESC = "created_desc"
    UPDATED_ASC = "updated_asc"
    UPDATED_DESC = "updated_desc"
    TITLE_ASC = "title_asc"
    TITLE_DESC = "title_desc"
    POPULARITY = "popularity"

class PaginationParams(BaseModel):
    skip: int = 0
    limit: int = 100 