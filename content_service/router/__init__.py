"""
Content Service API routes.
"""

from fastapi import APIRouter

from .categories import router as categories_router
from .tags import router as tags_router
from .stories import router as stories_router
from .quizzes import router as quizzes_router
from .lessons import router as lessons_router
from .assets import router as assets_router
from .collections import router as collections_router

# Main API router
router = APIRouter()

# Include sub-routers
router.include_router(categories_router, prefix="/categories", tags=["categories"])
router.include_router(tags_router, prefix="/tags", tags=["tags"])
router.include_router(stories_router, prefix="/stories", tags=["stories"])
router.include_router(quizzes_router, prefix="/quizzes", tags=["quizzes"])
router.include_router(lessons_router, prefix="/lessons", tags=["lessons"])
router.include_router(assets_router, prefix="/assets", tags=["assets"])
router.include_router(collections_router, prefix="/collections", tags=["collections"]) 