"""ECS task for scraping UCLA menus (triggered by EventBridge)."""
import asyncio
import logging
from typing import Optional
from datetime import datetime
from app.services.ucla_scraper import UCLAScraper
from app.services.s3_service import S3Service
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def scrape_ucla_menu_task(date_str: Optional[str] = None):
    """
    Main task function for ECS Fargate container.
    This is called by EventBridge scheduler or manually via admin endpoint.
    
    Args:
        date_str: Optional date in YYYY-MM-DD format (defaults to today)
    """
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Starting menu scrape for {date_str}")
    
    try:
        scraper = UCLAScraper()
        s3_service = S3Service()
        
        # Scrape menu data
        menu_data = await scraper.scrape_daily_menu(date_str)
        
        # Upload raw data to S3
        s3_key = s3_service.upload_raw_menu(date_str, menu_data)
        
        logger.info(f"Successfully scraped and uploaded menu for {date_str} to {s3_key}")
        
        # TODO: Trigger normalization job (ECS task or Lambda)
        # This would parse the raw JSON and insert into Postgres
        
        return {
            "status": "success",
            "date": date_str,
            "s3_key": s3_key,
            "dining_halls_count": len(menu_data.get("dining_halls", {}))
        }
        
    except Exception as e:
        logger.error(f"Error in scraper task: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    # For local testing or direct ECS execution
    import sys
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    result = asyncio.run(scrape_ucla_menu_task(date_arg))
    print(result)

