"""
Quiz CRUD operations for the content service.
"""

from typing import Optional
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import models, schemas
from .content_base import create_content_base, update_content_base

async def create_quiz(
    db: AsyncSession, 
    quiz: schemas.QuizCreate,
    is_ai_generated: bool = False,
    generation_task_id: Optional[str] = None,
    creator_id: Optional[UUID] = None
) -> models.Quiz:
    """Create a new quiz"""
    # Extract quiz-specific fields
    quiz_data = quiz.dict(exclude={"category_ids", "tag_ids", "content_type"})
    questions = quiz_data.pop("questions")
    answer_key = quiz_data.pop("answer_key")
    
    # Create the base content record
    db_content = await create_content_base(
        db, 
        quiz_data,
        quiz.category_ids,
        quiz.tag_ids,
        content_type="quiz",
        is_ai_generated=is_ai_generated,
        creator_id=creator_id
    )
    
    # Create the quiz record with specific fields
    db_quiz = models.Quiz(
        id=db_content.id,
        questions=jsonable_encoder(questions),
        answer_key=jsonable_encoder(answer_key),
        topic=quiz_data.get("topic"),
        question_count=quiz_data.get("question_count", len(questions)),
        time_limit_minutes=quiz_data.get("time_limit_minutes"),
        passing_score=quiz_data.get("passing_score")
    )
    
    db.add(db_quiz)
    await db.commit()
    await db.refresh(db_quiz)
    
    return db_quiz

async def get_quiz(db: AsyncSession, quiz_id: UUID) -> Optional[models.Quiz]:
    """Get a quiz by ID"""
    result = await db.execute(
        select(models.Quiz)
        .options(
            joinedload(models.Quiz.categories),
            joinedload(models.Quiz.tags)
        )
        .where(models.Quiz.id == quiz_id)
    )
    return result.scalars().first()

async def update_quiz(
    db: AsyncSession,
    db_quiz: models.Quiz,
    quiz_update: schemas.QuizUpdate
) -> models.Quiz:
    """Update a quiz"""
    # Extract and handle quiz-specific fields
    update_data = quiz_update.dict(exclude_unset=True)
    questions = update_data.pop("questions", None)
    answer_key = update_data.pop("answer_key", None)
    
    # Update the base content fields first
    await update_content_base(db, db_quiz, quiz_update)
    
    # Update the quiz-specific fields
    if questions is not None:
        db_quiz.questions = jsonable_encoder(questions)
        # Update question count if not explicitly provided
        if "question_count" not in update_data:
            db_quiz.question_count = len(questions)
    
    if answer_key is not None:
        db_quiz.answer_key = jsonable_encoder(answer_key)
    
    for field in ["topic", "question_count", "time_limit_minutes", "passing_score"]:
        if field in update_data:
            setattr(db_quiz, field, update_data[field])
    
    await db.commit()
    await db.refresh(db_quiz)
    
    return db_quiz 