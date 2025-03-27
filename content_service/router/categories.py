"""
Categories API routes for the content service.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from common.database import get_db_session
from .. import crud, schemas
from ..dependencies import get_current_user

router = APIRouter()
db_dependency = Depends(get_db_session())
current_user_dependency = Depends(get_current_user)


@router.post("/", response_model=schemas.CategoryInDB, status_code=status.HTTP_201_CREATED)
async def create_category(
    category: schemas.CategoryCreate,
    db: AsyncSession = db_dependency,
    current_user: dict = current_user_dependency
):
    """
    Create a new category (admin only).
    """
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can create categories"
        )
    
    # Check if category with same name already exists
    existing = await crud.get_category_by_name(db, category.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Category with name '{category.name}' already exists"
        )
    
    # Validate parent category if provided
    if category.parent_id:
        parent = await crud.get_category(db, category.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with ID {category.parent_id} not found"
            )
    
    return await crud.create_category(db, category)


@router.get("/", response_model=List[schemas.CategoryInDB])
async def get_categories(
    skip: int = 0, 
    limit: int = 100,
    parent_id: Optional[int] = None,
    db: AsyncSession = db_dependency
):
    """
    Get all categories, optionally filtered by parent ID.
    If parent_id is provided, returns subcategories.
    If parent_id is not provided, returns top-level categories.
    """
    return await crud.get_categories(db, skip=skip, limit=limit, parent_id=parent_id)


@router.get("/{category_id}", response_model=schemas.CategoryInDB)
async def get_category(
    category_id: int,
    db: AsyncSession = db_dependency
):
    """
    Get a specific category by ID.
    """
    category = await crud.get_category(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    return category


@router.put("/{category_id}", response_model=schemas.CategoryInDB)
async def update_category(
    category_id: int,
    category_update: schemas.CategoryUpdate,
    db: AsyncSession = db_dependency,
    current_user: dict = current_user_dependency
):
    """
    Update an existing category (admin only).
    """
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can update categories"
        )
    
    # Check if category exists
    db_category = await crud.get_category(db, category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    # Validate name uniqueness if changed
    if category_update.name and category_update.name != db_category.name:
        existing = await crud.get_category_by_name(db, category_update.name)
        if existing and existing.id != category_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Category with name '{category_update.name}' already exists"
            )
    
    # Validate parent category if provided
    if category_update.parent_id and category_update.parent_id != db_category.parent_id:
        # Prevent circular references
        if category_update.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )
        
        parent = await crud.get_category(db, category_update.parent_id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with ID {category_update.parent_id} not found"
            )
    
    return await crud.update_category(db, db_category, category_update)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    db: AsyncSession = db_dependency,
    current_user: dict = current_user_dependency
):
    """
    Delete a category (admin only).
    """
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete categories"
        )
    
    # Check if category exists
    db_category = await crud.get_category(db, category_id)
    if not db_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    await crud.delete_category(db, db_category) 