"""Endpoint to store scraped menu items in database."""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.crud import bulk_insert_menu_items
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/store", tags=["store"])


@router.post("/menu-items")
async def store_menu_items(
    items: List[Dict[str, Any]] = Body(..., description="List of menu items to store"),
    db: Session = Depends(get_db)
):
    """
    Store scraped menu items in the database.
    
    Expected format:
    [
        {
            "name": "Grilled Chicken Breast",
            "calories": 200,
            "serving_size": "4 oz",
            "ingredients": ["chicken", "olive oil"],
            "protein_g": 30,
            "fat_g": 8,
            "carbs_g": 0,
            "dining_halls": ["Bruin Plate"],
            "services": ["Lunch", "Dinner"],
            "dates_seen": ["2025-01-01", "2025-01-02"]
        },
        ...
    ]
    """
    try:
        result = bulk_insert_menu_items(db, items)
        return {
            "status": "success",
            **result
        }
    except Exception as e:
        logger.error(f"Error storing menu items: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to store menu items: {str(e)}")

