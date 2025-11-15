"""Database CRUD operations for menu items."""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from app.db.models import MenuItem
import logging

logger = logging.getLogger(__name__)


def get_menu_items(
    db: Session,
    dining_halls: Optional[List[str]] = None,
    skip: int = 0,
    limit: int = 1000
) -> List[MenuItem]:
    """
    Get menu items from database, optionally filtered by dining halls.
    
    Args:
        db: Database session
        dining_halls: Optional list of dining hall names to filter by
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of MenuItem objects
    """
    query = db.query(MenuItem)
    
    if dining_halls:
        query = query.filter(MenuItem.dining_hall.in_(dining_halls))
    
    return query.offset(skip).limit(limit).all()


def get_menu_items_dict(
    db: Session,
    dining_halls: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Get menu items as dictionaries (for API responses).
    
    Args:
        db: Database session
        dining_halls: Optional list of dining hall names to filter by
        
    Returns:
        List of menu item dictionaries
    """
    items = get_menu_items(db, dining_halls, limit=10000)  # Get up to 10k items
    
    return [
        {
            "id": str(item.id),
            "name": item.name,
            "calories": item.calories,
            "serving_size": item.serving_size,
            "protein_g": float(item.protein_g) if item.protein_g else None,
            "fat_g": float(item.fat_g) if item.fat_g else None,
            "carbs_g": float(item.carbs_g) if item.carbs_g else None,
            "fiber_g": float(item.fiber_g) if item.fiber_g else None,
            "ingredients": item.ingredients if item.ingredients else [],
            "dining_hall": item.dining_hall,
            "service": item.service,
            "dates_seen": item.dates_seen if item.dates_seen else []
        }
        for item in items
    ]


def create_or_update_menu_item(
    db: Session,
    item_data: Dict[str, Any]
) -> MenuItem:
    """
    Create or update a menu item in the database.
    
    Args:
        db: Database session
        item_data: Dictionary with menu item data
        
    Returns:
        MenuItem object
    """
    # Try to find existing item by name, dining_hall, and service
    existing = db.query(MenuItem).filter(
        MenuItem.name == item_data.get("name"),
        MenuItem.dining_hall == item_data.get("dining_hall"),
        MenuItem.service == item_data.get("service")
    ).first()
    
    if existing:
        # Update existing item
        if item_data.get("calories"):
            existing.calories = item_data["calories"]
        if item_data.get("serving_size"):
            existing.serving_size = item_data["serving_size"]
        if item_data.get("protein_g") is not None:
            existing.protein_g = item_data["protein_g"]
        if item_data.get("fat_g") is not None:
            existing.fat_g = item_data["fat_g"]
        if item_data.get("carbs_g") is not None:
            existing.carbs_g = item_data["carbs_g"]
        if item_data.get("fiber_g") is not None:
            existing.fiber_g = item_data["fiber_g"]
        if item_data.get("ingredients"):
            existing.ingredients = item_data["ingredients"]
        
        # Update dates_seen
        new_dates = item_data.get("dates_seen", [])
        if new_dates:
            existing_dates = existing.dates_seen or []
            combined_dates = list(set(existing_dates + new_dates))
            existing.dates_seen = combined_dates
        
        # Don't commit here - let bulk_insert_menu_items handle it
        return existing
    else:
        # Create new item
        new_item = MenuItem(
            name=item_data.get("name"),
            calories=item_data.get("calories"),
            serving_size=item_data.get("serving_size"),
            protein_g=item_data.get("protein_g"),
            fat_g=item_data.get("fat_g"),
            carbs_g=item_data.get("carbs_g"),
            fiber_g=item_data.get("fiber_g"),
            ingredients=item_data.get("ingredients", []),
            dining_hall=item_data.get("dining_hall"),
            service=item_data.get("service"),
            dates_seen=item_data.get("dates_seen", [])
        )
        db.add(new_item)
        # Don't commit here - let bulk_insert_menu_items handle it
        return new_item


def bulk_insert_menu_items(
    db: Session,
    items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Bulk insert/update menu items from scraped data.
    
    Args:
        db: Database session
        items: List of menu item dictionaries from scraper
        
    Returns:
        Dictionary with summary statistics
    """
    created = 0
    updated = 0
    errors = []
    
    for item_data in items:
        try:
            # For each dining hall and service combination
            dining_halls = item_data.get("dining_halls", [])
            services = item_data.get("services", [])
            
            if not dining_halls:
                dining_halls = [None]
            if not services:
                services = [None]
            
            for dining_hall in dining_halls:
                for service in services:
                    item_to_store = {
                        "name": item_data.get("name"),
                        "calories": item_data.get("calories"),
                        "serving_size": item_data.get("serving_size"),
                        "protein_g": item_data.get("protein_g"),
                        "fat_g": item_data.get("fat_g"),
                        "carbs_g": item_data.get("carbs_g"),
                        "fiber_g": item_data.get("fiber_g"),
                        "ingredients": item_data.get("ingredients", []),
                        "dining_hall": dining_hall,
                        "service": service,
                        "dates_seen": item_data.get("dates_seen", [])
                    }
                    
                    # Check if exists
                    existing = db.query(MenuItem).filter(
                        MenuItem.name == item_to_store["name"],
                        MenuItem.dining_hall == item_to_store["dining_hall"],
                        MenuItem.service == item_to_store["service"]
                    ).first()
                    
                    if existing:
                        updated += 1
                    else:
                        created += 1
                    
                    create_or_update_menu_item(db, item_to_store)
                    
        except Exception as e:
            logger.error(f"Error storing item {item_data.get('name')}: {e}", exc_info=True)
            errors.append({"item": item_data.get("name"), "error": str(e)})
    
    try:
        db.commit()  # Commit all changes at once
        logger.info(f"Committed {created} created, {updated} updated items to database")
    except Exception as e:
        logger.error(f"Error committing to database: {e}", exc_info=True)
        db.rollback()
        errors.append({"item": "COMMIT", "error": str(e)})
    
    return {
        "created": created,
        "updated": updated,
        "total_processed": len(items),
        "errors": errors
    }

