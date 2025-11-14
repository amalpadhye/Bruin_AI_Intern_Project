"""Admin endpoints for triggering background tasks."""
from fastapi import APIRouter, HTTPException, Header, Depends
from typing import Optional
from app.tasks.scraper_task import scrape_ucla_menu_task
from app.config import settings
import asyncio

router = APIRouter(prefix="/tasks", tags=["admin"])


async def verify_admin_secret(x_secret: Optional[str] = Header(None)):
    """Verify admin secret for protected endpoints."""
    if x_secret != settings.api_secret_key:
        raise HTTPException(status_code=403, detail="Invalid admin secret")
    return True


@router.post("/scrape-ucla")
async def trigger_scrape_task(
    date: Optional[str] = None,
    _: bool = Depends(verify_admin_secret)
):
    """
    Manually trigger UCLA menu scraping task.
    Protected by admin secret (X-Secret header).
    
    Args:
        date: Optional date in YYYY-MM-DD format (defaults to today)
    """
    try:
        result = await scrape_ucla_menu_task(date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping task failed: {str(e)}")

