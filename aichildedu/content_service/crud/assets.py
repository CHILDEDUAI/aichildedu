"""
Content Asset CRUD operations for the content service.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas

async def create_content_asset(
    db: AsyncSession, 
    asset: schemas.ContentAssetCreate
) -> models.ContentAsset:
    """Create a new content asset"""
    db_asset = models.ContentAsset(**asset.dict())
    db.add(db_asset)
    await db.commit()
    await db.refresh(db_asset)
    return db_asset

async def get_content_asset(
    db: AsyncSession, 
    asset_id: UUID
) -> Optional[models.ContentAsset]:
    """Get a content asset by ID"""
    result = await db.execute(
        select(models.ContentAsset).where(models.ContentAsset.id == asset_id)
    )
    return result.scalars().first()

async def get_content_assets(
    db: AsyncSession,
    content_id: UUID,
    asset_type: Optional[schemas.AssetType] = None,
    skip: int = 0,
    limit: int = 100
) -> List[models.ContentAsset]:
    """Get content assets by content ID and optional asset type"""
    query = select(models.ContentAsset).where(models.ContentAsset.content_id == content_id)
    
    if asset_type:
        query = query.where(models.ContentAsset.asset_type == asset_type)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()

async def update_content_asset(
    db: AsyncSession,
    db_asset: models.ContentAsset,
    asset_update: schemas.ContentAssetUpdate
) -> models.ContentAsset:
    """Update a content asset"""
    update_data = asset_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(db_asset, field, value)
    
    await db.commit()
    await db.refresh(db_asset)
    return db_asset

async def delete_content_asset(
    db: AsyncSession,
    db_asset: models.ContentAsset
) -> bool:
    """Delete a content asset"""
    await db.delete(db_asset)
    await db.commit()
    return True 