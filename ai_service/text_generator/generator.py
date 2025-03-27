import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import httpx
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from common.config import settings
from common.utils import generate_uuid

from .db import db
from .models import QuizContent, StoryContent, TaskStatus
from .schemas import GenerateQuizRequest, GenerateStoryRequest

# Configure logging
logger = logging.getLogger(__name__)

# LLM Configuration
DEFAULT_MODEL = "gpt-4"  # Default model for high-quality content
FALLBACK_MODEL = "gpt-3.5-turbo"  # Fallback model
STORY_TEMPERATURE = 0.7  # Higher temperature for creative storytelling
QUIZ_TEMPERATURE = 0.2  # Lower temperature for factual quiz generation


class TextGenerator:
    """Text content generator for stories and quizzes"""
    
    def __init__(self):
        """Initialize the text generator"""
        self.primary_model = ChatOpenAI(
            temperature=STORY_TEMPERATURE,
            model=DEFAULT_MODEL,
            api_key=settings.OPENAI_API_KEY
        )
        
        self.fallback_model = ChatOpenAI(
            temperature=STORY_TEMPERATURE,
            model=FALLBACK_MODEL,
            api_key=settings.OPENAI_API_KEY
        )
        
        # Load prompt templates
        self._load_prompt_templates()
        
    def _load_prompt_templates(self):
        """Load prompt templates for different generation tasks"""
        # Story generation prompt
        self.story_prompt = PromptTemplate(
            input_variables=[
                "title", "theme", "age_group", "characters", 
                "educational_focus", "length", "language"
            ],
            template="""
            Create an engaging and educational story for children based on the following requirements:
            
            Title: {title}
            Theme: {theme}
            Age Group: {age_group} years old
            Characters: {characters}
            Educational Focus: {educational_focus}
            Approximate Length: {length} words
            Language: {language}
            
            Your story should be engaging, age-appropriate, and contain the following elements:
            1. An introduction that sets the scene and introduces the main characters
            2. A clear problem or challenge related to the educational focus
            3. Character development and learning through the story
            4. A resolution that reinforces the educational message
            5. A brief moral or lesson summary at the end
            
            Format your response as a JSON object with the following structure:
            {{
                "title": "Story title",
                "content": "Full story content with paragraphs",
                "summary": "Brief 2-3 sentence summary of the story",
                "characters": ["Character 1", "Character 2"],
                "themes": ["Theme 1", "Theme 2"],
                "educational_value": "Description of educational value",
                "age_range": [min_age, max_age],
                "word_count": approximate_word_count,
                "reading_time_minutes": estimated_reading_time
            }}
            
            Make sure the content is appropriate for the specified age group, engaging, and educational.
            """
        )
        
        # Quiz generation prompt
        self.quiz_prompt = PromptTemplate(
            input_variables=[
                "title", "subject", "topic", "age_group", 
                "difficulty", "num_questions", "question_types", "language"
            ],
            template="""
            Create an educational quiz for children based on the following requirements:
            
            Title: {title}
            Subject: {subject}
            Topic: {topic}
            Age Group: {age_group} years old
            Difficulty: {difficulty}
            Number of Questions: {num_questions}
            Question Types: {question_types}
            Language: {language}
            
            Create age-appropriate questions that are educational and engaging.
            For multiple-choice questions, include 3-4 options with only one correct answer.
            For true/false questions, make sure they are not too obvious.
            
            Format your response as a JSON object with the following structure:
            {{
                "title": "Quiz title",
                "description": "Brief description of the quiz",
                "questions": [
                    {{
                        "question": "Question text",
                        "type": "multiple_choice|true_false|short_answer",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Correct option or answer",
                        "explanation": "Explanation of why the answer is correct"
                    }}
                ],
                "difficulty": "easy|medium|hard",
                "subject": "Subject of the quiz",
                "topic": "Specific topic of the quiz",
                "age_range": [min_age, max_age]
            }}
            
            Make sure the questions are factually correct, clear, and appropriate for the specified age group.
            """
        )
    
    async def create_story_task(self, request: GenerateStoryRequest, user_id: Optional[str] = None) -> str:
        """
        Create a story generation task
        
        Args:
            request: Story generation request
            user_id: Optional user ID
            
        Returns:
            Task ID
        """
        # Create task in database
        task_id = await db.create_task(
            task_type="story",
            prompt=request.dict(),
            user_id=user_id
        )
        
        # Start generation in background
        asyncio.create_task(self._generate_story(task_id, request))
        
        return task_id
    
    async def create_quiz_task(self, request: GenerateQuizRequest, user_id: Optional[str] = None) -> str:
        """
        Create a quiz generation task
        
        Args:
            request: Quiz generation request
            user_id: Optional user ID
            
        Returns:
            Task ID
        """
        # Create task in database
        task_id = await db.create_task(
            task_type="quiz",
            prompt=request.dict(),
            user_id=user_id
        )
        
        # Start generation in background
        asyncio.create_task(self._generate_quiz(task_id, request))
        
        return task_id
    
    async def _generate_story(self, task_id: str, request: GenerateStoryRequest):
        """
        Generate a story based on the provided parameters
        
        Args:
            task_id: Task ID
            request: Story generation request
        """
        # Update task status to processing
        await db.update_task_status(task_id, TaskStatus.PROCESSING)
        
        try:
            # Convert characters to string representation
            characters_str = ", ".join([f"{c.name} ({c.description})" for c in request.characters]) if request.characters else "Create appropriate characters"
            
            # Extract min-max age from age_group
            age_min, age_max = map(int, request.age_group.split("-"))
            
            # Create story chain
            story_chain = LLMChain(
                llm=self.primary_model,
                prompt=self.story_prompt
            )
            
            # Generate story
            result = await story_chain.arun(
                title=request.title,
                theme=request.theme,
                age_group=f"{age_min}-{age_max}",
                characters=characters_str,
                educational_focus=request.educational_focus,
                length=request.length,
                language=request.language
            )
            
            # Log model used
            await db.update_task_model(task_id, DEFAULT_MODEL)
            
            # Parse the JSON response
            story_data = json.loads(result)
            
            # Create story content model
            story = StoryContent(
                title=story_data["title"],
                content=story_data["content"],
                summary=story_data["summary"],
                characters=story_data["characters"],
                themes=story_data["themes"],
                age_range=[age_min, age_max],
                language=request.language,
                word_count=story_data["word_count"],
                reading_time_minutes=story_data["reading_time_minutes"],
                educational_value=story_data["educational_value"]
            )
            
            # Update task with result
            await db.update_task_result(task_id, story.dict())
            
            # Send webhook if specified
            if request.webhook:
                await self._send_webhook(request.webhook, task_id, "COMPLETED")
                
        except Exception as e:
            logger.error(f"Story generation failed for task {task_id}: {str(e)}")
            
            # Try fallback model if available
            if settings.USE_FALLBACK_MODEL:
                await self._fallback_story_generation(task_id, request)
            else:
                # Update task status to failed
                await db.update_task_status(
                    task_id, 
                    TaskStatus.FAILED,
                    error=f"Story generation failed: {str(e)}"
                )
                
                # Send webhook if specified
                if request.webhook:
                    await self._send_webhook(
                        request.webhook, 
                        task_id, 
                        "FAILED", 
                        error=str(e)
                    )
    
    async def _fallback_story_generation(self, task_id: str, request: GenerateStoryRequest):
        """
        Fallback story generation with simpler model
        
        Args:
            task_id: Task ID
            request: Story generation request
        """
        try:
            # Convert characters to string representation
            characters_str = ", ".join([f"{c.name} ({c.description})" for c in request.characters]) if request.characters else "Create appropriate characters"
            
            # Extract min-max age from age_group
            age_min, age_max = map(int, request.age_group.split("-"))
            
            # Create story chain with fallback model
            story_chain = LLMChain(
                llm=self.fallback_model,
                prompt=self.story_prompt
            )
            
            # Generate story
            result = await story_chain.arun(
                title=request.title,
                theme=request.theme,
                age_group=f"{age_min}-{age_max}",
                characters=characters_str,
                educational_focus=request.educational_focus,
                length=request.length,
                language=request.language
            )
            
            # Log model used
            await db.update_task_model(task_id, FALLBACK_MODEL)
            
            # Parse the JSON response
            story_data = json.loads(result)
            
            # Create story content model
            story = StoryContent(
                title=story_data["title"],
                content=story_data["content"],
                summary=story_data["summary"],
                characters=story_data["characters"],
                themes=story_data["themes"],
                age_range=[age_min, age_max],
                language=request.language,
                word_count=story_data["word_count"],
                reading_time_minutes=story_data["reading_time_minutes"],
                educational_value=story_data["educational_value"]
            )
            
            # Update task with result
            await db.update_task_result(task_id, story.dict())
            
            # Send webhook if specified
            if request.webhook:
                await self._send_webhook(request.webhook, task_id, "COMPLETED")
                
        except Exception as e:
            logger.error(f"Fallback story generation failed for task {task_id}: {str(e)}")
            
            # Update task status to failed
            await db.update_task_status(
                task_id, 
                TaskStatus.FAILED,
                error=f"Story generation failed (fallback model): {str(e)}"
            )
            
            # Send webhook if specified
            if request.webhook:
                await self._send_webhook(
                    request.webhook, 
                    task_id, 
                    "FAILED", 
                    error=str(e)
                )
    
    async def _generate_quiz(self, task_id: str, request: GenerateQuizRequest):
        """
        Generate a quiz based on the provided parameters
        
        Args:
            task_id: Task ID
            request: Quiz generation request
        """
        # Update task status to processing
        await db.update_task_status(task_id, TaskStatus.PROCESSING)
        
        try:
            # Configure LLM with lower temperature for factual content
            quiz_llm = ChatOpenAI(
                temperature=QUIZ_TEMPERATURE,
                model=DEFAULT_MODEL,
                api_key=settings.OPENAI_API_KEY
            )
            
            # Extract min-max age from age_group
            age_min, age_max = map(int, request.age_group.split("-"))
            
            # Create quiz chain
            quiz_chain = LLMChain(
                llm=quiz_llm,
                prompt=self.quiz_prompt
            )
            
            # Generate quiz
            result = await quiz_chain.arun(
                title=request.title,
                subject=request.subject,
                topic=request.topic,
                age_group=f"{age_min}-{age_max}",
                difficulty=request.difficulty,
                num_questions=request.num_questions,
                question_types=", ".join(request.question_types),
                language=request.language
            )
            
            # Log model used
            await db.update_task_model(task_id, DEFAULT_MODEL)
            
            # Parse the JSON response
            quiz_data = json.loads(result)
            
            # Create quiz content model
            quiz = QuizContent(
                title=quiz_data["title"],
                description=quiz_data["description"],
                questions=quiz_data["questions"],
                subject=quiz_data["subject"],
                topic=quiz_data["topic"],
                age_range=[age_min, age_max],
                difficulty=quiz_data["difficulty"],
                language=request.language
            )
            
            # Update task with result
            await db.update_task_result(task_id, quiz.dict())
            
            # Send webhook if specified
            if request.webhook:
                await self._send_webhook(request.webhook, task_id, "COMPLETED")
                
        except Exception as e:
            logger.error(f"Quiz generation failed for task {task_id}: {str(e)}")
            
            # Try fallback model if available
            if settings.USE_FALLBACK_MODEL:
                await self._fallback_quiz_generation(task_id, request)
            else:
                # Update task status to failed
                await db.update_task_status(
                    task_id, 
                    TaskStatus.FAILED,
                    error=f"Quiz generation failed: {str(e)}"
                )
                
                # Send webhook if specified
                if request.webhook:
                    await self._send_webhook(
                        request.webhook, 
                        task_id, 
                        "FAILED", 
                        error=str(e)
                    )
    
    async def _fallback_quiz_generation(self, task_id: str, request: GenerateQuizRequest):
        """
        Fallback quiz generation with simpler model
        
        Args:
            task_id: Task ID
            request: Quiz generation request
        """
        try:
            # Configure fallback LLM with lower temperature for factual content
            quiz_llm = ChatOpenAI(
                temperature=QUIZ_TEMPERATURE,
                model=FALLBACK_MODEL,
                api_key=settings.OPENAI_API_KEY
            )
            
            # Extract min-max age from age_group
            age_min, age_max = map(int, request.age_group.split("-"))
            
            # Create quiz chain
            quiz_chain = LLMChain(
                llm=quiz_llm,
                prompt=self.quiz_prompt
            )
            
            # Generate quiz
            result = await quiz_chain.arun(
                title=request.title,
                subject=request.subject,
                topic=request.topic,
                age_group=f"{age_min}-{age_max}",
                difficulty=request.difficulty,
                num_questions=request.num_questions,
                question_types=", ".join(request.question_types),
                language=request.language
            )
            
            # Log model used
            await db.update_task_model(task_id, FALLBACK_MODEL)
            
            # Parse the JSON response
            quiz_data = json.loads(result)
            
            # Create quiz content model
            quiz = QuizContent(
                title=quiz_data["title"],
                description=quiz_data["description"],
                questions=quiz_data["questions"],
                subject=quiz_data["subject"],
                topic=quiz_data["topic"],
                age_range=[age_min, age_max],
                difficulty=quiz_data["difficulty"],
                language=request.language
            )
            
            # Update task with result
            await db.update_task_result(task_id, quiz.dict())
            
            # Send webhook if specified
            if request.webhook:
                await self._send_webhook(request.webhook, task_id, "COMPLETED")
                
        except Exception as e:
            logger.error(f"Fallback quiz generation failed for task {task_id}: {str(e)}")
            
            # Update task status to failed
            await db.update_task_status(
                task_id, 
                TaskStatus.FAILED,
                error=f"Quiz generation failed (fallback model): {str(e)}"
            )
            
            # Send webhook if specified
            if request.webhook:
                await self._send_webhook(
                    request.webhook, 
                    task_id, 
                    "FAILED", 
                    error=str(e)
                )
    
    async def _send_webhook(
        self, 
        webhook_url: str, 
        task_id: str, 
        status: str, 
        error: Optional[str] = None
    ):
        """
        Send webhook notification
        
        Args:
            webhook_url: Webhook URL
            task_id: Task ID
            status: Task status
            error: Optional error message
        """
        payload = {
            "task_id": task_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if error:
            payload["error"] = error
            
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    webhook_url,
                    json=payload,
                    timeout=10.0
                )
        except Exception as e:
            logger.error(f"Failed to send webhook for task {task_id}: {str(e)}")
    
    async def get_task_status(self, task_id: str) -> Dict:
        """
        Get task status
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status data
        """
        task = await db.get_task(task_id)
        if not task:
            return None
            
        return {
            "task_id": task["id"],
            "status": task["status"],
            "created_at": task.get("created_at"),
            "started_at": task.get("started_at"),
            "completed_at": task.get("completed_at"),
            "error": task.get("error")
        }
    
    async def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        Get task result
        
        Args:
            task_id: Task ID
            
        Returns:
            Task result data or None if not completed
        """
        task = await db.get_task(task_id)
        if not task:
            return None
            
        if task["status"] != TaskStatus.COMPLETED:
            return None
            
        return task.get("result")
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a pending task
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was cancelled, False otherwise
        """
        task = await db.get_task(task_id)
        if not task:
            return False
            
        if task["status"] not in [TaskStatus.PENDING, TaskStatus.PROCESSING]:
            return False
            
        return await db.update_task_status(task_id, TaskStatus.CANCELLED)


# Create global generator instance
generator = TextGenerator() 