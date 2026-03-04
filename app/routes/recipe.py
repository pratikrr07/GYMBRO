"""
Recipe routes — GET /api/recipes/random
"""

from fastapi import APIRouter, Depends
from app.services.recipes import get_random_recipe
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/recipes", tags=["Recipes"])


@router.get("/random")
async def random_recipe(current_user: dict = Depends(get_current_user)):
    """Return a random high-protein recipe."""
    return get_random_recipe()
