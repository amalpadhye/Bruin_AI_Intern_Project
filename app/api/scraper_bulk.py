"""Bulk scraper endpoint for historical data."""
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import logging
from app.services.historical_scraper import HistoricalScraper
from app.db.database import get_db
from app.db.crud import bulk_insert_menu_items
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraper", tags=["scraper"])


async def verify_admin_secret(x_secret: Optional[str] = Header(None)):
    """Verify admin secret for protected endpoints."""
    if x_secret != settings.api_secret_key:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    return True


@router.post("/bulk-scrape")
async def bulk_scrape_historical(
    start_date: str = Query(..., description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(..., description="End date in YYYY-MM-DD format"),
    dining_halls: Optional[str] = Query(None, description="Comma-separated dining hall names"),
    store_in_db: bool = Query(True, description="Automatically store results in database"),
    _: bool = Depends(verify_admin_secret),
    db: Session = Depends(get_db)
):
    """
    Scrape historical menu data for a date range.
    Protected by admin secret (X-Secret header).
    
    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        dining_halls: Optional comma-separated list of dining halls to filter
    """
    try:
        # Validate dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start > end:
            raise HTTPException(status_code=400, detail="Start date must be before end date")
        
        # Limit to reasonable range (e.g., 90 days max)
        days_diff = (end - start).days
        if days_diff > 90:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 90 days")
        
        # Parse dining halls
        dining_hall_list = None
        if dining_halls:
            dining_hall_list = [h.strip() for h in dining_halls.split(",")]
        
        # Run scraper
        scraper = HistoricalScraper()
        result = await scraper.scrape_date_range(start_date, end_date, dining_hall_list)
        
        # Store in database if requested
        storage_result = None
        if store_in_db and result.get("items"):
            try:
                storage_result = bulk_insert_menu_items(db, result["items"])
                result["storage"] = storage_result
            except Exception as e:
                logger.error(f"Error storing items in database: {e}")
                result["storage_error"] = str(e)
        
        return {
            "status": "completed",
            **result
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk scraping failed: {str(e)}")


@router.post("/scrape-recent")
async def scrape_recent_days(
    days: int = Query(30, description="Number of days to scrape (default 30, max 90)"),
    dining_halls: Optional[str] = Query(None, description="Comma-separated dining hall names"),
    store_in_db: bool = Query(True, description="Automatically store results in database"),
    _: bool = Depends(verify_admin_secret),
    db: Session = Depends(get_db)
):
    """
    Scrape recent menu data (last N days).
    Protected by admin secret (X-Secret header).
    
    Args:
        days: Number of days to scrape (default 30, max 90)
        dining_halls: Optional comma-separated list of dining halls to filter
    """
    if days > 90:
        raise HTTPException(status_code=400, detail="Cannot scrape more than 90 days at once")
    
    end_date = datetime.now().strftime("%Y-%m-%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    
    return await bulk_scrape_historical(start_date, end_date, dining_halls, store_in_db, _, db)

