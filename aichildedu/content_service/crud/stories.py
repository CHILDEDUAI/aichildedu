"""
Story CRUD operations for the content service.
"""

from typing import Optional
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import models, schemas
from .content_base import create_content_base, update_content_base

async def create_story(
    db: AsyncSession, 
    story: schemas.StoryCreate,
    is_ai_generated: bool = False,
    generation_task_id: Optional[str] = None,
    creator_id: Optional[UUID] = None
) -> models.Story:
    """Create a new story"""
    # Extract story-specific fields
    story_data = story.dict(exclude={"category_ids", "tag_ids", "content_type"})
    story_content = story_data.pop("story_content")
    
    # Create the base content record
    db_content = await create_content_base(
        db, 
        story_data,
        story.category_ids,
        story.tag_ids,
        content_type="story",
        is_ai_generated=is_ai_generated,
        creator_id=creator_id
    )
    
    # Create the story record with specific fields
    db_story = models.Story(
        id=db_content.id,
        story_content=jsonable_encoder(story_content),
        characters=story_data.get("characters", []),
        themes=story_data.get("themes", []),
        moral_lesson=story_data.get("moral_lesson"),
        has_images=story_data.get("has_images", False),
        has_audio=story_data.get("has_audio", False),
        has_interactive_elements=story_data.get("has_interactive_elements", False),
        word_count=story_data.get("word_count")
    )
    
    db.add(db_story)
    await db.commit()
    await db.refresh(db_story)
    
    return db_story

async def get_story(db: AsyncSession, story_id: UUID) -> Optional[models.Story]:
    """Get a story by ID"""
    result = await db.execute(
        select(models.Story)
        .options(
            joinedload(models.Story.categories),
            joinedload(models.Story.tags)
        )
        .where(models.Story.id == story_id)
    )
    return result.scalars().first()

async def update_story(
    db: AsyncSession,
    db_story: models.Story,
    story_update: schemas.StoryUpdate
) -> models.Story:
    """Update a story"""
    # Extract and handle story-specific fields
    update_data = story_update.dict(exclude_unset=True)
    story_content = update_data.pop("story_content", None)
    
    # Update the base content fields first
    await update_content_base(db, db_story, story_update)
    
    # Update the story-specific fields
    if story_content is not None:
        db_story.story_content = jsonable_encoder(story_content)
    
    for field in ["moral_lesson", "has_images", "has_audio", 
                  "has_interactive_elements", "word_count", "characters", "themes"]:
        if field in update_data:
            setattr(db_story, field, update_data[field])
    
    await db.commit()
    await db.refresh(db_story)
    
    return db_story 