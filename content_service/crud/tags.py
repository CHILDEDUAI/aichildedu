"""
Tag CRUD operations for the content service.
"""

from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas

async def create_tag(db: AsyncSession, tag: schemas.TagCreate) -> models.Tag:
    """Create a new tag"""
    db_tag = models.Tag(**tag.dict())
    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)
    return db_tag

async def get_tag(db: AsyncSession, tag_id: int) -> Optional[models.Tag]:
    """Get a tag by ID"""
    result = await db.execute(
        select(models.Tag).where(models.Tag.id == tag_id)
    )
    return result.scalars().first()

async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[models.Tag]:
    """Get a tag by name"""
    result = await db.execute(
        select(models.Tag).where(func.lower(models.Tag.name) == func.lower(name))
    )
    return result.scalars().first()

async def get_tags(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.Tag]:
    """Get all tags with pagination"""
    result = await db.execute(
        select(models.Tag).offset(skip).limit(limit)
    )
    return result.scalars().all()

async def update_tag(
    db: AsyncSession, 
    db_tag: models.Tag,
    tag: schemas.TagUpdate
) -> models.Tag:
    """Update a tag"""
    update_data = tag.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_tag, field, value)
    
    await db.commit()
    await db.refresh(db_tag)
    return db_tag

async def delete_tag(db: AsyncSession, db_tag: models.Tag) -> bool:
    """Delete a tag"""
    await db.delete(db_tag)
    await db.commit()
    return True 