"""
Content Collection CRUD operations for the content service.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas

async def create_collection(
    db: AsyncSession, 
    collection: schemas.ContentCollectionCreate,
    creator_id: Optional[UUID] = None
) -> models.ContentCollection:
    """Create a new content collection"""
    db_collection = models.ContentCollection(
        **collection.dict(),
        creator_id=creator_id
    )
    db.add(db_collection)
    await db.commit()
    await db.refresh(db_collection)
    return db_collection

async def get_collection(
    db: AsyncSession, 
    collection_id: UUID
) -> Optional[models.ContentCollection]:
    """Get a content collection by ID"""
    result = await db.execute(
        select(models.ContentCollection).where(models.ContentCollection.id == collection_id)
    )
    return result.scalars().first()

async def get_collections(
    db: AsyncSession,
    creator_id: Optional[UUID] = None,
    is_public: Optional[bool] = None,
    collection_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ContentCollection]:
    """Get content collections with filters"""
    conditions = []
    
    if creator_id:
        conditions.append(models.ContentCollection.creator_id == creator_id)
    
    if is_public is not None:
        conditions.append(models.ContentCollection.is_public == is_public)
    
    if collection_type:
        conditions.append(models.ContentCollection.collection_type == collection_type)
    
    query = select(models.ContentCollection)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def update_collection(
    db: AsyncSession,
    db_collection: models.ContentCollection,
    collection_update: schemas.ContentCollectionUpdate
) -> models.ContentCollection:
    """Update a content collection"""
    update_data = collection_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_collection, field, value)
    
    await db.commit()
    await db.refresh(db_collection)
    return db_collection

async def delete_collection(
    db: AsyncSession,
    db_collection: models.ContentCollection
) -> bool:
    """Delete a content collection"""
    await db.delete(db_collection)
    await db.commit()
    return True 