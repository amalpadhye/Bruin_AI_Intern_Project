#!/usr/bin/env python3
"""Script to update nutrition data for existing menu items in database."""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models import MenuItem
from app.services.ucla_scraper import UCLAScraper
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_nutrition_for_item(db: Session, item: MenuItem, scraper: UCLAScraper):
    """Update nutrition data for a single menu item."""
    # Try to find recipe_id or ingredient_id from item name or other fields
    # For now, we'll need to scrape the menu page to find recipe IDs
    # This is a simplified version - in practice, you'd need to match items better
    
    # Since we don't have recipe_id stored, we'll skip items without it
    # In a real scenario, you'd need to scrape the menu page to find recipe IDs
    logger.warning(f"Skipping {item.name} - recipe_id not available in database")
    return False


async def update_all_nutrition(limit: int = None):
    """Update nutrition data for all menu items missing it."""
    db = SessionLocal()
    scraper = UCLAScraper()
    
    try:
        # Get items without calories
        query = db.query(MenuItem).filter(MenuItem.calories.is_(None))
        if limit:
            query = query.limit(limit)
        
        items = query.all()
        logger.info(f"Found {len(items)} items without nutrition data")
        
        updated = 0
        for item in items:
            try:
                # For now, we can't update without recipe_id
                # The best approach is to re-scrape with the new code
                logger.info(f"Skipping {item.name} - need to re-scrape to get recipe_id")
            except Exception as e:
                logger.error(f"Error updating {item.name}: {e}")
        
        db.commit()
        logger.info(f"Updated {updated} items")
        
    finally:
        db.close()


if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else None
    print("⚠️  Note: To get nutrition data, you need to re-scrape menus.")
    print("   The scraper will now fetch nutrition from recipe detail pages.")
    print("   Run: python3 scripts/scrape_and_store.py 90")
    asyncio.run(update_all_nutrition(limit))

