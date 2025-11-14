"""Menu endpoints for UCLA dining data."""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from datetime import date
from app.services.ucla_scraper import UCLAScraper
from app.services.s3_service import S3Service

router = APIRouter(prefix="/menus", tags=["menus"])


@router.get("")
async def get_menus(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    hall: Optional[str] = Query(None, description="Dining hall name"),
    scraper: UCLAScraper = Depends(lambda: UCLAScraper()),
    s3_service: S3Service = Depends(lambda: S3Service())
):
    """
    Get menu data for a specific date and optional dining hall.
    
    Args:
        date: Date string in YYYY-MM-DD format (defaults to today)
        hall: Optional dining hall filter
    """
    try:
        # Try to fetch from S3 cache first
        if date:
            cache_key = f"raw/menus/{date}/menu.json"
            cached = s3_service.download_json(s3_service.bucket_raw, cache_key)
            if cached:
                return cached
        
        # If not cached, scrape fresh data
        menu_data = await scraper.scrape_daily_menu(date)
        
        # Cache in S3
        if date:
            s3_service.upload_raw_menu(date, menu_data)
        
        # Filter by hall if requested
        if hall and "dining_halls" in menu_data:
            filtered = {k: v for k, v in menu_data["dining_halls"].items() if hall.lower() in k.lower()}
            menu_data["dining_halls"] = filtered
        
        return menu_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching menu: {str(e)}")


@router.get("/items/{item_id}")
async def get_item_details(
    item_id: str,
    scraper: UCLAScraper = Depends(lambda: UCLAScraper())
):
    """
    Get detailed information about a specific menu item.
    
    Args:
        item_id: Menu item ID (recipe_id or ingredient_id)
    """
    try:
        # Try recipe first
        recipe_data = await scraper.fetch_recipe_details(item_id)
        if recipe_data:
            return {
                "item_id": item_id,
                "type": "recipe",
                **recipe_data
            }
        
        # Try ingredient
        ingredient_data = await scraper.fetch_ingredient_details(item_id)
        if ingredient_data:
            return {
                "item_id": item_id,
                "type": "ingredient",
                **ingredient_data
            }
        
        raise HTTPException(status_code=404, detail="Item not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching item: {str(e)}")

