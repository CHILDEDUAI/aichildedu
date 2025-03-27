"""
Quizzes API routes for the content service.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from aichildedu.common.database import get_db_session
from .. import crud, schemas
from ..dependencies import get_current_user, get_optional_user

router = APIRouter()
db_dependency = Depends(get_db_session())
current_user_dependency = Depends(get_current_user)
optional_user_dependency = Depends(get_optional_user)


@router.post("/", response_model=schemas.QuizInDB, status_code=status.HTTP_201_CREATED)
async def create_quiz(
    quiz: schemas.QuizCreate,
    db: AsyncSession = db_dependency,
    current_user: dict = current_user_dependency
):
    """
    Create a new quiz.
    """
    # Create the quiz with the current user as creator
    creator_id = UUID(current_user["id"]) if current_user and "id" in current_user else None
    return await crud.create_quiz(
        db, 
        quiz, 
        is_ai_generated=False,
        creator_id=creator_id
    )


@router.get("/", response_model=List[schemas.QuizInDB])
async def get_quizzes(
    category_ids: Optional[List[int]] = Query(None),
    tag_ids: Optional[List[int]] = Query(None),
    status: Optional[List[schemas.ContentStatus]] = Query(None),
    language: Optional[str] = None,
    min_age: Optional[int] = None,
    max_age: Optional[int] = None,
    difficulty_level: Optional[List[schemas.DifficultyLevel]] = Query(None),
    content_rating: Optional[List[schemas.ContentRating]] = Query(None),
    creator_id: Optional[UUID] = None,
    is_ai_generated: Optional[bool] = None,
    subjects: Optional[List[str]] = Query(None),
    search_query: Optional[str] = None,
    sort_by: Optional[schemas.ContentSort] = schemas.ContentSort.CREATED_DESC,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = db_dependency,
    current_user: Optional[dict] = optional_user_dependency
):
    """
    Get all quizzes with filtering, sorting and pagination.
    """
    # Build the filter
    content_filter = schemas.ContentFilter(
        content_type=[schemas.ContentType.QUIZ],  # Always filter for quizzes
        category_ids=category_ids,
        tag_ids=tag_ids,
        status=status,
        language=language,
        min_age=min_age,
        max_age=max_age,
        difficulty_level=difficulty_level,
        content_rating=content_rating,
        creator_id=creator_id,
        is_ai_generated=is_ai_generated,
        subjects=subjects,
        search_query=search_query
    )
    
    # If user is not an admin, only return published content
    if not current_user or not current_user.get("is_admin", False):
        content_filter.status = [schemas.ContentStatus.PUBLISHED]
    
    # Get quizzes from database
    contents = await crud.get_contents(
        db, content_filter, sort_by, skip, limit
    )
    
    # Convert generic contents to quizzes
    quizzes = []
    for content in contents:
        if content.type == "quiz":
            quiz = await crud.get_quiz(db, content.id)
            if quiz:
                quizzes.append(quiz)
    
    return quizzes


@router.get("/{quiz_id}", response_model=schemas.QuizInDB)
async def get_quiz(
    quiz_id: UUID,
    db: AsyncSession = db_dependency,
    current_user: Optional[dict] = optional_user_dependency
):
    """
    Get a specific quiz by ID.
    """
    quiz = await crud.get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID {quiz_id} not found"
        )
    
    # If user is not admin and quiz is not published, deny access
    if (not current_user or not current_user.get("is_admin", False)) and quiz.status != schemas.ContentStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to unpublished quiz denied"
        )
    
    return quiz


@router.put("/{quiz_id}", response_model=schemas.QuizInDB)
async def update_quiz(
    quiz_id: UUID,
    quiz_update: schemas.QuizUpdate,
    db: AsyncSession = db_dependency,
    current_user: dict = current_user_dependency
):
    """
    Update an existing quiz.
    """
    # Check if quiz exists
    db_quiz = await crud.get_quiz(db, quiz_id)
    if not db_quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID {quiz_id} not found"
        )
    
    # Check if user has permission to update
    user_id = UUID(current_user["id"]) if "id" in current_user else None
    is_admin = current_user.get("is_admin", False)
    
    if not is_admin and (not db_quiz.creator_id or db_quiz.creator_id != user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to update this quiz"
        )
    
    # Update the quiz
    updated_quiz = await crud.update_quiz(db, db_quiz, quiz_update)
    return updated_quiz


@router.delete("/{quiz_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quiz(
    quiz_id: UUID,
    db: AsyncSession = db_dependency,
    current_user: dict = current_user_dependency
):
    """
    Delete a quiz.
    """
    # Check if quiz exists
    db_quiz = await crud.get_quiz(db, quiz_id)
    if not db_quiz:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quiz with ID {quiz_id} not found"
        )
    
    # Check if user has permission to delete
    user_id = UUID(current_user["id"]) if "id" in current_user else None
    is_admin = current_user.get("is_admin", False)
    
    if not is_admin and (not db_quiz.creator_id or db_quiz.creator_id != user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to delete this quiz"
        )
    
    # Delete the quiz
    await crud.delete_content(db, db_quiz) 