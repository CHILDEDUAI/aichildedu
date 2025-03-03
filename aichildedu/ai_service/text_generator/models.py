from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Status of a generation task"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StoryContent(BaseModel):
    """Content of a generated story"""
    title: str
    content: List[Dict[str, Union[str, dict]]]  # List of pages with text, image_prompt, etc.
    summary: Optional[str] = None
    characters: List[Dict[str, str]] = []  # List of character descriptions
    themes: List[str] = []
    age_range: List[int] = Field(default_factory=lambda: [3, 8])  # min and max age
    language: str = "en"
    word_count: Optional[int] = None
    reading_time_minutes: Optional[int] = None
    educational_value: Optional[List[str]] = None


class QuizContent(BaseModel):
    """Content of a generated quiz"""
    title: str
    description: Optional[str] = None
    questions: List[Dict[str, Union[str, List[str], dict]]]
    age_range: List[int] = Field(default_factory=lambda: [3, 8])  # min and max age
    difficulty: str = "medium"
    subject: str
    topic: Optional[str] = None
    language: str = "en"


class TextGenerationTask(BaseModel):
    """Document model for text generation tasks"""
    id: str = Field(..., description="Task ID")
    user_id: Optional[str] = Field(None, description="User ID who created the task")
    type: str = Field(..., description="Type of content to generate (story, quiz, etc.)")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="Current status of the task")
    prompt: Dict = Field(..., description="Generation prompt parameters")
    result: Optional[Union[StoryContent, QuizContent, Dict]] = Field(None, description="Generated content")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Processing start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    error: Optional[str] = Field(None, description="Error message if failed")
    model_used: Optional[str] = Field(None, description="AI model used for generation")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata")

    class Config:
        schema_extra = {
            "example": {
                "id": "task_123456",
                "user_id": "user_123",
                "type": "story",
                "status": "pending",
                "prompt": {
                    "title": "The Space Adventure",
                    "theme": "space exploration",
                    "characters": [
                        {"name": "Astro", "description": "A curious astronaut kid"},
                        {"name": "Comet", "description": "A friendly space dog"}
                    ],
                    "age_group": "6-8",
                    "language": "en",
                    "educational_focus": "science",
                    "length": "medium"
                },
                "created_at": "2023-07-25T12:34:56.789Z"
            }
        }


class StoryTemplate(BaseModel):
    """Document model for story templates"""
    id: str = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    structure: Dict = Field(..., description="Template structure")
    themes: List[str] = Field(default_factory=list, description="Applicable themes")
    age_range: List[int] = Field(default_factory=lambda: [3, 12], description="Target age range")
    educational_focus: List[str] = Field(default_factory=list, description="Educational focuses")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Whether template is active")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "template_123",
                "name": "Hero's Journey",
                "description": "Classic hero's journey story structure for children",
                "structure": {
                    "intro": "The hero is introduced in their ordinary world",
                    "parts": [
                        "Call to adventure",
                        "Meeting the guide",
                        "Challenges and trials",
                        "The big challenge",
                        "Return with new knowledge"
                    ],
                    "moral": "What the hero learned"
                },
                "themes": ["adventure", "growth", "friendship"],
                "age_range": [6, 10],
                "educational_focus": ["social skills", "problem solving"],
                "created_at": "2023-05-10T09:12:34.567Z",
                "is_active": True
            }
        } 