"""
Base Content CRUD operations for the content service.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .. import models, schemas
from .categories import get_category
from .tags import get_tag

async def get_content(
    db: AsyncSession, 
    content_id: UUID,
    load_relationships: bool = True
) -> Optional[models.Content]:
    """Get content by ID with option to load relationships"""
    query = select(models.Content).where(models.Content.id == content_id)
    
    if load_relationships:
        query = query.options(
            joinedload(models.Content.categories),
            joinedload(models.Content.tags)
        )
    
    result = await db.execute(query)
    return result.scalars().first()

async def get_contents(
    db: AsyncSession,
    filters: Optional[schemas.ContentFilter] = None,
    sort_by: Optional[schemas.ContentSort] = schemas.ContentSort.CREATED_DESC,
    skip: int = 0,
    limit: int = 100,
    load_relationships: bool = True
) -> List[models.Content]:
    """Get all contents with filtering, sorting and pagination"""
    query = select(models.Content)
    
    # Apply filters if provided
    if filters:
        filter_conditions = []
        
        if filters.content_type:
            filter_conditions.append(models.Content.content_type.in_([t.value for t in filters.content_type]))
        
        if filters.status:
            filter_conditions.append(models.Content.status.in_([s.value for s in filters.status]))
        
        if filters.language:
            filter_conditions.append(models.Content.language == filters.language)
        
        if filters.min_age is not None:
            filter_conditions.append(models.Content.min_age >= filters.min_age)
        
        if filters.max_age is not None:
            filter_conditions.append(models.Content.max_age <= filters.max_age)
        
        if filters.difficulty_level:
            filter_conditions.append(models.Content.difficulty_level.in_(
                [d.value for d in filters.difficulty_level]
            ))
            
        if filters.content_rating:
            filter_conditions.append(models.Content.content_rating.in_(
                [r.value for r in filters.content_rating]
            ))
        
        if filters.creator_id:
            filter_conditions.append(models.Content.creator_id == filters.creator_id)
        
        if filters.is_ai_generated is not None:
            filter_conditions.append(models.Content.is_ai_generated == filters.is_ai_generated)
            
        if filters.subjects:
            # For array overlap with PostgreSQL
            from sqlalchemy.dialects.postgresql import ARRAY
            subjects_array = filters.subjects
            filter_conditions.append(models.Content.subjects.overlap(subjects_array))
            
        if filters.search_query:
            search_query = f"%{filters.search_query}%"
            filter_conditions.append(or_(
                models.Content.title.ilike(search_query),
                models.Content.description.ilike(search_query)
            ))
            
        if filter_conditions:
            query = query.filter(and_(*filter_conditions))
    
    # Apply sorting
    if sort_by:
        if sort_by == schemas.ContentSort.CREATED_ASC:
            query = query.order_by(models.Content.created_at.asc())
        elif sort_by == schemas.ContentSort.CREATED_DESC:
            query = query.order_by(models.Content.created_at.desc())
        elif sort_by == schemas.ContentSort.UPDATED_ASC:
            query = query.order_by(models.Content.updated_at.asc())
        elif sort_by == schemas.ContentSort.UPDATED_DESC:
            query = query.order_by(models.Content.updated_at.desc())
        elif sort_by == schemas.ContentSort.TITLE_ASC:
            query = query.order_by(models.Content.title.asc())
        elif sort_by == schemas.ContentSort.TITLE_DESC:
            query = query.order_by(models.Content.title.desc())
        # POPULARITY requires additional logic and will be implemented separately
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    
    # Load relationships if requested
    if load_relationships:
        query = query.options(
            joinedload(models.Content.categories),
            joinedload(models.Content.tags)
        )
    
    result = await db.execute(query)
    return result.scalars().all()

async def create_content_base(
    db: AsyncSession,
    content_data: Dict,
    category_ids: List[int] = None,
    tag_ids: List[int] = None,
    content_type: str = None,
    is_ai_generated: bool = False,
    creator_id: Optional[UUID] = None
) -> models.Content:
    """Base function to create content record with common fields"""
    
    # Create base content object
    db_content = models.Content(
        **content_data,
        is_ai_generated=is_ai_generated,
        creator_id=creator_id,
        content_type=content_type,
    )
    
    # Add categories if provided
    if category_ids:
        categories = []
        for cat_id in category_ids:
            cat = await get_category(db, cat_id)
            if cat:
                categories.append(cat)
        db_content.categories = categories
    
    # Add tags if provided
    if tag_ids:
        tags = []
        for tag_id in tag_ids:
            tag = await get_tag(db, tag_id)
            if tag:
                tags.append(tag)
        db_content.tags = tags
    
    # Add to the session and commit
    db.add(db_content)
    await db.commit()
    await db.refresh(db_content)
    
    return db_content

async def update_content_base(
    db: AsyncSession,
    db_content: models.Content,
    content_update: schemas.ContentUpdate
) -> models.Content:
    """Base function to update common content fields"""
    update_data = content_update.dict(exclude_unset=True)
    
    # Handle status changes and publication
    if "status" in update_data and update_data["status"] == schemas.ContentStatus.PUBLISHED:
        if db_content.status != schemas.ContentStatus.PUBLISHED.value:
            db_content.published_at = datetime.utcnow()
    
    # Extract category and tag IDs if they're in the update
    category_ids = update_data.pop("category_ids", None)
    tag_ids = update_data.pop("tag_ids", None)
    
    # Update direct attributes
    for field, value in update_data.items():
        setattr(db_content, field, value)
    
    # Update categories if provided
    if category_ids is not None:
        categories = []
        for cat_id in category_ids:
            cat = await get_category(db, cat_id)
            if cat:
                categories.append(cat)
        db_content.categories = categories
    
    # Update tags if provided
    if tag_ids is not None:
        tags = []
        for tag_id in tag_ids:
            tag = await get_tag(db, tag_id)
            if tag:
                tags.append(tag)
        db_content.tags = tags
    
    await db.commit()
    await db.refresh(db_content)
    
    return db_content

async def delete_content(db: AsyncSession, db_content: models.Content) -> bool:
    """Delete content"""
    await db.delete(db_content)
    await db.commit()
    return True 