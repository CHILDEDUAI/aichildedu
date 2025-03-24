"""
Content Reaction CRUD operations for the content service.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas

async def create_reaction(
    db: AsyncSession, 
    reaction: schemas.ContentReactionCreate,
    user_id: UUID
) -> models.ContentReaction:
    """Create a new content reaction"""
    # Check if reaction already exists
    existing_reaction = await db.execute(
        select(models.ContentReaction).where(
            and_(
                models.ContentReaction.content_id == reaction.content_id,
                models.ContentReaction.user_id == user_id,
                models.ContentReaction.child_id == reaction.child_id,
                models.ContentReaction.reaction_type == reaction.reaction_type
            )
        )
    )
    db_existing = existing_reaction.scalars().first()
    
    if db_existing:
        # Update existing reaction
        update_data = reaction.dict(exclude={"content_id", "child_id"})
        for field, value in update_data.items():
            setattr(db_existing, field, value)
        await db.commit()
        await db.refresh(db_existing)
        return db_existing
    
    # Create new reaction
    db_reaction = models.ContentReaction(
        **reaction.dict(),
        user_id=user_id
    )
    db.add(db_reaction)
    await db.commit()
    await db.refresh(db_reaction)
    return db_reaction

async def get_content_reactions(
    db: AsyncSession,
    content_id: UUID,
    reaction_type: Optional[schemas.ReactionType] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ContentReaction]:
    """Get reactions for a specific content"""
    query = select(models.ContentReaction).where(models.ContentReaction.content_id == content_id)
    
    if reaction_type:
        query = query.where(models.ContentReaction.reaction_type == reaction_type)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def get_user_reactions(
    db: AsyncSession,
    user_id: UUID,
    child_id: Optional[UUID] = None,
    reaction_type: Optional[schemas.ReactionType] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ContentReaction]:
    """Get reactions by a specific user"""
    query = select(models.ContentReaction).where(models.ContentReaction.user_id == user_id)
    
    if child_id:
        query = query.where(models.ContentReaction.child_id == child_id)
    
    if reaction_type:
        query = query.where(models.ContentReaction.reaction_type == reaction_type)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def delete_reaction(
    db: AsyncSession,
    user_id: UUID,
    content_id: UUID,
    reaction_type: schemas.ReactionType,
    child_id: Optional[UUID] = None
) -> bool:
    """Delete a reaction by user, content, and type"""
    conditions = [
        models.ContentReaction.user_id == user_id,
        models.ContentReaction.content_id == content_id,
        models.ContentReaction.reaction_type == reaction_type
    ]
    
    if child_id:
        conditions.append(models.ContentReaction.child_id == child_id)
    
    query = select(models.ContentReaction).where(and_(*conditions))
    result = await db.execute(query)
    db_reaction = result.scalars().first()
    
    if db_reaction:
        await db.delete(db_reaction)
        await db.commit()
        return True
    
    return False 