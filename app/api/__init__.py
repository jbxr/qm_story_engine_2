"""FastAPI route handlers and endpoints"""

from fastapi import APIRouter

# Import only working route modules
from . import scenes

# Create main API router
api_router = APIRouter()

# Include working route modules
api_router.include_router(scenes.router, prefix="/scenes", tags=["scenes"])

__all__ = ["api_router"]