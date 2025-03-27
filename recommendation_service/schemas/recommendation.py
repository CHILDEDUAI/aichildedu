"""
Recommendation Service Schemas
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

class InteractionType(str, Enum):
    VIEW = "view"
    COMPLETE = "complete"
    LIKE = "like"
    BOOKMARK = "bookmark"

class RecommendationType(str, Enum):
    COLLABORATIVE = "collaborative"
    CONTENT_BASED = "content_based"
    HYBRID = "hybrid"

class LearningStyle(str, Enum):
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    READING_WRITING = "reading_writing"

# User Preference Schemas
class UserPreferenceBase(BaseModel):
    preferred_subjects: List[str] = Field(default_factory=list)
    preferred_content_types: List[str] = Field(default_factory=list)
    preferred_difficulty_levels: List[str] = Field(default_factory=list)
    learning_style: Optional[LearningStyle] = None
    interests: List[str] = Field(default_factory=list)
    metadata: Dict = Field(default_factory=dict)

class UserPreferenceCreate(UserPreferenceBase):
    user_id: UUID

class UserPreferenceUpdate(UserPreferenceBase):
    pass

class UserPreferenceInDB(UserPreferenceBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# User Content Interaction Schemas
class UserContentInteractionBase(BaseModel):
    interaction_type: InteractionType
    engagement_score: float = 0.0
    time_spent: int = 0
    progress: float = 0.0
    metadata: Dict = Field(default_factory=dict)

class UserContentInteractionCreate(UserContentInteractionBase):
    user_id: UUID
    content_id: UUID

class UserContentInteractionInDB(UserContentInteractionBase):
    id: UUID
    user_id: UUID
    content_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

# Recommendation History Schemas
class RecommendationHistoryBase(BaseModel):
    recommendation_type: RecommendationType
    score: float
    is_clicked: bool = False
    metadata: Dict = Field(default_factory=dict)

class RecommendationHistoryCreate(RecommendationHistoryBase):
    user_id: UUID
    content_id: UUID

class RecommendationHistoryInDB(RecommendationHistoryBase):
    id: UUID
    user_id: UUID
    content_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True

# Content Feature Vector Schemas
class ContentFeatureVectorBase(BaseModel):
    feature_vector: List[float]
    metadata: Dict = Field(default_factory=dict)

class ContentFeatureVectorCreate(ContentFeatureVectorBase):
    content_id: UUID

class ContentFeatureVectorInDB(ContentFeatureVectorBase):
    id: UUID
    content_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# Recommendation Request/Response Schemas
class RecommendationRequest(BaseModel):
    user_id: UUID
    content_type: Optional[str] = None
    subject: Optional[str] = None
    difficulty_level: Optional[str] = None
    limit: int = Field(default=10, ge=1, le=50)

class RecommendationResponse(BaseModel):
    content_id: UUID
    score: float
    recommendation_type: RecommendationType
    metadata: Dict = Field(default_factory=dict)

class RecommendationList(BaseModel):
    recommendations: List[RecommendationResponse]
    total: int
    metadata: Dict = Field(default_factory=dict) 