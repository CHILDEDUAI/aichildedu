from datetime import datetime
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .models import StoryContent, TaskStatus


class Character(BaseModel):
    """Character for story generation"""
    name: str
    description: str
    traits: Optional[List[str]] = None
    appearance: Optional[str] = None


class GenerateStoryRequest(BaseModel):
    """
    Request schema for story generation
    """
    title: str = Field(..., description="Story title")
    theme: str = Field(..., description="Main theme of the story")
    age_group: str = Field(..., description="Target age group (e.g. '3-5', '6-8')")
    characters: List[Character] = Field(..., description="Characters in the story")
    educational_focus: Optional[str] = Field(None, description="Educational focus of the story")
    length: str = Field("medium", description="Story length (short, medium, long)")
    language: str = Field("en", description="Language of the story")
    art_style: Optional[str] = Field(None, description="Art style for illustrations")
    additional_instructions: Optional[str] = Field(None, description="Additional instructions for generation")
    
    @validator('age_group')
    def validate_age_group(cls, v):
        """Validate age group format"""
        try:
            min_age, max_age = map(int, v.split('-'))
            assert 1 <= min_age <= max_age <= 12
            return v
        except (ValueError, AssertionError):
            raise ValueError("Age group must be in format 'min-max' where min and max are between 1 and 12")


class GenerateQuizRequest(BaseModel):
    """
    Request schema for quiz generation
    """
    title: str = Field(..., description="Quiz title")
    subject: str = Field(..., description="Subject of the quiz (math, science, etc.)")
    topic: str = Field(..., description="Specific topic within the subject")
    age_group: str = Field(..., description="Target age group (e.g. '3-5', '6-8')")
    difficulty: str = Field("medium", description="Quiz difficulty (easy, medium, hard)")
    num_questions: int = Field(5, description="Number of questions to generate", ge=1, le=20)
    question_types: List[str] = Field(default_factory=lambda: ["multiple_choice"], description="Types of questions")
    language: str = Field("en", description="Language of the quiz")
    additional_instructions: Optional[str] = Field(None, description="Additional instructions for generation")
    
    @validator('age_group')
    def validate_age_group(cls, v):
        """Validate age group format"""
        try:
            min_age, max_age = map(int, v.split('-'))
            assert 1 <= min_age <= max_age <= 12
            return v
        except (ValueError, AssertionError):
            raise ValueError("Age group must be in format 'min-max' where min and max are between 1 and 12")


class TaskResponse(BaseModel):
    """
    Response schema for task creation
    """
    task_id: str
    status: TaskStatus
    estimated_time_seconds: int
    webhook: Optional[str] = None
    status_check_url: str


class TaskStatusResponse(BaseModel):
    """
    Response schema for task status check
    """
    task_id: str
    status: TaskStatus
    progress: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_url: Optional[str] = None
    error: Optional[str] = None


class StoryResponse(BaseModel):
    """
    Response schema for completed story
    """
    task_id: str
    title: str
    content: List[Dict[str, Union[str, dict]]]
    summary: Optional[str] = None
    characters: List[Dict[str, str]] = []
    themes: List[str] = []
    age_range: List[int]
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    educational_value: Optional[List[str]] = None
    language: str
    metadata: Dict = Field(default_factory=dict)
    
    
class QuizResponse(BaseModel):
    """
    Response schema for completed quiz
    """
    task_id: str
    title: str
    description: Optional[str] = None
    questions: List[Dict[str, Union[str, List[str], dict]]]
    subject: str
    topic: Optional[str] = None
    age_range: List[int]
    difficulty: str
    language: str
    metadata: Dict = Field(default_factory=dict)


class TextGenerationError(BaseModel):
    """
    Error response for text generation
    """
    error: str
    detail: Optional[str] = None
    task_id: Optional[str] = None


class TemplateResponse(BaseModel):
    """
    Response schema for story template
    """
    id: str
    name: str
    description: str
    structure: Dict
    themes: List[str]
    age_range: List[int]
    educational_focus: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool


class TemplateListResponse(BaseModel):
    """
    Response schema for list of templates
    """
    templates: List[TemplateResponse]
    count: int 