"""
Category CRUD operations for the content service.
"""

from typing import List, Optional
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas

async def create_category(db: AsyncSession, category: schemas.CategoryCreate) -> models.Category:
    """Create a new category"""
    db_category = models.Category(**category.dict())
    db.add(db_category)
    await db.commit()
    await db.refresh(db_category)
    return db_category

async def get_category(db: AsyncSession, category_id: int) -> Optional[models.Category]:
    """Get a category by ID"""
    result = await db.execute(
        select(models.Category).where(models.Category.id == category_id)
    )
    return result.scalars().first()

async def get_category_by_name(db: AsyncSession, name: str) -> Optional[models.Category]:
    """Get a category by name"""
    result = await db.execute(
        select(models.Category).where(func.lower(models.Category.name) == func.lower(name))
    )
    return result.scalars().first()

async def get_categories(
    db: AsyncSession, 
    skip: int = 0, 
    limit: int = 100,
    parent_id: Optional[int] = None
) -> List[models.Category]:
    """Get all categories with optional parent filter"""
    query = select(models.Category).offset(skip).limit(limit)
    
    if parent_id is not None:
        query = query.where(models.Category.parent_id == parent_id)
    else:
        # If parent_id is None, we can optionally fetch root categories
        query = query.where(models.Category.parent_id.is_(None))
    
    result = await db.execute(query)
    return result.scalars().all()

async def update_category(
    db: AsyncSession, 
    db_category: models.Category,
    category: schemas.CategoryUpdate
) -> models.Category:
    """Update a category"""
    update_data = category.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_category, field, value)
    
    await db.commit()
    await db.refresh(db_category)
    return db_category

async def delete_category(db: AsyncSession, db_category: models.Category) -> bool:
    """Delete a category"""
    await db.delete(db_category)
    await db.commit()
    return True 