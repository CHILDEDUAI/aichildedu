"""
Lesson CRUD operations for the content service.
"""

from typing import Optional
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import models, schemas
from .content_base import create_content_base, update_content_base

async def create_lesson(
    db: AsyncSession, 
    lesson: schemas.LessonCreate,
    is_ai_generated: bool = False,
    generation_task_id: Optional[str] = None,
    creator_id: Optional[UUID] = None
) -> models.Lesson:
    """Create a new lesson"""
    # Extract lesson-specific fields
    lesson_data = lesson.dict(exclude={"category_ids", "tag_ids", "content_type"})
    lesson_content = lesson_data.pop("lesson_content")
    
    # Create the base content record
    db_content = await create_content_base(
        db, 
        lesson_data,
        lesson.category_ids,
        lesson.tag_ids,
        content_type="lesson",
        is_ai_generated=is_ai_generated,
        creator_id=creator_id
    )
    
    # Create the lesson record with specific fields
    db_lesson = models.Lesson(
        id=db_content.id,
        lesson_content=jsonable_encoder(lesson_content),
        learning_objectives=lesson_data.get("learning_objectives", []),
        prerequisites=lesson_data.get("prerequisites", []),
        related_content_ids=lesson_data.get("related_content_ids", [])
    )
    
    db.add(db_lesson)
    await db.commit()
    await db.refresh(db_lesson)
    
    return db_lesson

async def get_lesson(db: AsyncSession, lesson_id: UUID) -> Optional[models.Lesson]:
    """Get a lesson by ID"""
    result = await db.execute(
        select(models.Lesson)
        .options(
            joinedload(models.Lesson.categories),
            joinedload(models.Lesson.tags)
        )
        .where(models.Lesson.id == lesson_id)
    )
    return result.scalars().first()

async def update_lesson(
    db: AsyncSession,
    db_lesson: models.Lesson,
    lesson_update: schemas.LessonUpdate
) -> models.Lesson:
    """Update a lesson"""
    # Extract and handle lesson-specific fields
    update_data = lesson_update.dict(exclude_unset=True)
    lesson_content = update_data.pop("lesson_content", None)
    
    # Update the base content fields first
    await update_content_base(db, db_lesson, lesson_update)
    
    # Update the lesson-specific fields
    if lesson_content is not None:
        db_lesson.lesson_content = jsonable_encoder(lesson_content)
    
    for field in ["learning_objectives", "prerequisites", "related_content_ids"]:
        if field in update_data:
            setattr(db_lesson, field, update_data[field])
    
    await db.commit()
    await db.refresh(db_lesson)
    
    return db_lesson 