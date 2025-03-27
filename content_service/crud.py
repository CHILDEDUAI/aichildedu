from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from uuid import UUID

from fastapi.encoders import jsonable_encoder
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from . import models, schemas


# Category CRUD operations
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

# Tag CRUD operations
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

# Content base CRUD operations
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

# Story-specific CRUD operations
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

# Quiz-specific CRUD operations
async def create_quiz(
    db: AsyncSession, 
    quiz: schemas.QuizCreate,
    is_ai_generated: bool = False,
    generation_task_id: Optional[str] = None,
    creator_id: Optional[UUID] = None
) -> models.Quiz:
    """Create a new quiz"""
    # Extract quiz-specific fields
    quiz_data = quiz.dict(exclude={"category_ids", "tag_ids", "content_type"})
    questions = quiz_data.pop("questions")
    answer_key = quiz_data.pop("answer_key")
    
    # Create the base content record
    db_content = await create_content_base(
        db, 
        quiz_data,
        quiz.category_ids,
        quiz.tag_ids,
        content_type="quiz",
        is_ai_generated=is_ai_generated,
        creator_id=creator_id
    )
    
    # Create the quiz record with specific fields
    db_quiz = models.Quiz(
        id=db_content.id,
        questions=jsonable_encoder(questions),
        answer_key=jsonable_encoder(answer_key),
        topic=quiz_data.get("topic"),
        question_count=quiz_data.get("question_count", len(questions)),
        time_limit_minutes=quiz_data.get("time_limit_minutes"),
        passing_score=quiz_data.get("passing_score")
    )
    
    db.add(db_quiz)
    await db.commit()
    await db.refresh(db_quiz)
    
    return db_quiz

async def get_quiz(db: AsyncSession, quiz_id: UUID) -> Optional[models.Quiz]:
    """Get a quiz by ID"""
    result = await db.execute(
        select(models.Quiz)
        .options(
            joinedload(models.Quiz.categories),
            joinedload(models.Quiz.tags)
        )
        .where(models.Quiz.id == quiz_id)
    )
    return result.scalars().first()

async def update_quiz(
    db: AsyncSession,
    db_quiz: models.Quiz,
    quiz_update: schemas.QuizUpdate
) -> models.Quiz:
    """Update a quiz"""
    # Extract and handle quiz-specific fields
    update_data = quiz_update.dict(exclude_unset=True)
    questions = update_data.pop("questions", None)
    answer_key = update_data.pop("answer_key", None)
    
    # Update the base content fields first
    await update_content_base(db, db_quiz, quiz_update)
    
    # Update the quiz-specific fields
    if questions is not None:
        db_quiz.questions = jsonable_encoder(questions)
        # Update question count if not explicitly provided
        if "question_count" not in update_data:
            db_quiz.question_count = len(questions)
    
    if answer_key is not None:
        db_quiz.answer_key = jsonable_encoder(answer_key)
    
    for field in ["topic", "question_count", "time_limit_minutes", "passing_score"]:
        if field in update_data:
            setattr(db_quiz, field, update_data[field])
    
    await db.commit()
    await db.refresh(db_quiz)
    
    return db_quiz

# Lesson-specific CRUD operations
async def create_lesson(
    db: AsyncSession, 
    lesson: schemas.LessonCreate,
    is_ai_generated: bool = False,
    generation_task_id: Optional[str] = None,
    creator_id: Optional[UUID] = None
) -> models.Lesson:
    """Create a new lesson"""
    # Extract lesson-specific fields
    lesson_data = lesson.dict(exclude={"category_ids", "tag_ids", "content_type"})
    lesson_content = lesson_data.pop("lesson_content")
    
    # Create the base content record
    db_content = await create_content_base(
        db, 
        lesson_data,
        lesson.category_ids,
        lesson.tag_ids,
        content_type="lesson",
        is_ai_generated=is_ai_generated,
        creator_id=creator_id
    )
    
    # Create the lesson record with specific fields
    db_lesson = models.Lesson(
        id=db_content.id,
        lesson_content=jsonable_encoder(lesson_content),
        learning_objectives=lesson_data.get("learning_objectives", []),
        prerequisites=lesson_data.get("prerequisites", []),
        related_content_ids=lesson_data.get("related_content_ids", [])
    )
    
    db.add(db_lesson)
    await db.commit()
    await db.refresh(db_lesson)
    
    return db_lesson

async def get_lesson(db: AsyncSession, lesson_id: UUID) -> Optional[models.Lesson]:
    """Get a lesson by ID"""
    result = await db.execute(
        select(models.Lesson)
        .options(
            joinedload(models.Lesson.categories),
            joinedload(models.Lesson.tags)
        )
        .where(models.Lesson.id == lesson_id)
    )
    return result.scalars().first()

async def update_lesson(
    db: AsyncSession,
    db_lesson: models.Lesson,
    lesson_update: schemas.LessonUpdate
) -> models.Lesson:
    """Update a lesson"""
    # Extract and handle lesson-specific fields
    update_data = lesson_update.dict(exclude_unset=True)
    lesson_content = update_data.pop("lesson_content", None)
    
    # Update the base content fields first
    await update_content_base(db, db_lesson, lesson_update)
    
    # Update the lesson-specific fields
    if lesson_content is not None:
        db_lesson.lesson_content = jsonable_encoder(lesson_content)
    
    for field in ["learning_objectives", "prerequisites", "related_content_ids"]:
        if field in update_data:
            setattr(db_lesson, field, update_data[field])
    
    await db.commit()
    await db.refresh(db_lesson)
    
    return db_lesson 