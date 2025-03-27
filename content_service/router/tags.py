"""
Tags API routes for the content service.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from aichildedu.common.database import get_db_session
from .. import crud, schemas
from ..dependencies import get_current_user

router = APIRouter()
db_dependency = Depends(get_db_session())
current_user_dependency = Depends(get_current_user)


@router.post("/", response_model=schemas.TagInDB, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag: schemas.TagCreate,
    db: AsyncSession = db_dependency,
    current_user: dict = current_user_dependency
):
    """
    Create a new tag (admin only).
    """
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create tags"
        )
    
    # Check if tag with same name already exists
    existing = await crud.get_tag_by_name(db, tag.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Tag with name '{tag.name}' already exists"
        )
    
    return await crud.create_tag(db, tag)


@router.get("/", response_model=List[schemas.TagInDB])
async def get_tags(
    skip: int = 0, 
    limit: int = 100,
    db: AsyncSession = db_dependency
):
    """
    Get all tags with pagination.
    """
    return await crud.get_tags(db, skip=skip, limit=limit)


@router.get("/{tag_id}", response_model=schemas.TagInDB)
async def get_tag(
    tag_id: int,
    db: AsyncSession = db_dependency
):
    """
    Get a specific tag by ID.
    """
    tag = await crud.get_tag(db, tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    return tag


@router.put("/{tag_id}", response_model=schemas.TagInDB)
async def update_tag(
    tag_id: int,
    tag_update: schemas.TagUpdate,
    db: AsyncSession = db_dependency,
    current_user: dict = current_user_dependency
):
    """
    Update an existing tag (admin only).
    """
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update tags"
        )
    
    # Check if tag exists
    db_tag = await crud.get_tag(db, tag_id)
    if not db_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    # Validate name uniqueness if changed
    if tag_update.name and tag_update.name != db_tag.name:
        existing = await crud.get_tag_by_name(db, tag_update.name)
        if existing and existing.id != tag_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tag with name '{tag_update.name}' already exists"
            )
    
    return await crud.update_tag(db, db_tag, tag_update)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    db: AsyncSession = db_dependency,
    current_user: dict = current_user_dependency
):
    """
    Delete a tag (admin only).
    """
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete tags"
        )
    
    # Check if tag exists
    db_tag = await crud.get_tag(db, tag_id)
    if not db_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tag with ID {tag_id} not found"
        )
    
    await crud.delete_tag(db, db_tag) 