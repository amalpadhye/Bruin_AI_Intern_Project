"""Menu endpoints for UCLA dining data."""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from sqlalchemy.orm import Session
from app.services.ucla_scraper import UCLAScraper
from app.services.s3_service import S3Service
from app.db.database import get_db
from app.db.crud import get_menu_items_dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/menus", tags=["menus"])


@router.get("")
async def get_menus(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    hall: Optional[str] = Query(None, description="Dining hall name"),
    scraper: UCLAScraper = Depends(lambda: UCLAScraper()),
    s3_service: S3Service = Depends(lambda: S3Service()),
    db: Session = Depends(get_db)
):
    """
    Get menu data for a specific date and optional dining hall.
    
    Returns menu items from database (preferred) or scrapes fresh data.
    
    Args:
        date: Date string in YYYY-MM-DD format (defaults to today)
        hall: Optional dining hall filter
    """
    try:
        # First, try to get from database
        dining_hall_list = [hall] if hall else None
        menu_items = get_menu_items_dict(db, dining_hall_list)
        
        if menu_items:
            # Format as menu data structure
            menu_data = {
                "date": date or datetime.now().strftime("%Y-%m-%d"),
                "source": "database",
                "dining_halls": {}
            }
            
            # Group items by dining hall and service
            for item in menu_items:
                dining_hall = item.get("dining_hall") or "Unknown"
                service = item.get("service") or "Unknown"
                key = f"{dining_hall} {service}"
                
                if key not in menu_data["dining_halls"]:
                    menu_data["dining_halls"][key] = []
                
                menu_data["dining_halls"][key].append({
                    "name": item.get("name"),
                    "calories": item.get("calories"),
                    "serving_size": item.get("serving_size"),
                    "ingredients": item.get("ingredients", []),
                    "protein_g": item.get("protein_g"),
                    "fat_g": item.get("fat_g"),
                    "carbs_g": item.get("carbs_g"),
                    "fiber_g": item.get("fiber_g")
                })
            
            return menu_data
        
        # If no database items, try S3 cache
        if date:
            try:
                cache_key = f"raw/menus/{date}/menu.json"
                cached = s3_service.download_json(s3_service.bucket_raw, cache_key)
                if cached:
                    logger.info(f"Returning cached menu from S3 for {date}")
                    return cached
            except Exception as e:
                logger.warning(f"Could not fetch from S3 cache: {e}")
        
        # Last resort: scrape fresh data
        logger.info(f"Scraping fresh menu data for {date}")
        menu_data = await scraper.scrape_daily_menu(date)
        
        # Cache in S3
        if date:
            try:
                s3_service.upload_raw_menu(date, menu_data)
            except Exception as e:
                logger.warning(f"Could not cache menu in S3: {e}")
        
        # Filter by hall if requested
        if hall and "dining_halls" in menu_data:
            filtered = {k: v for k, v in menu_data["dining_halls"].items() if hall.lower() in k.lower()}
            menu_data["dining_halls"] = filtered
        
        return menu_data
        
    except Exception as e:
        logger.error(f"Error fetching menu: {e}", exc_info=True)
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

