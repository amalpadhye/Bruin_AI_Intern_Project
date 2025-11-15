#!/usr/bin/env python3
"""Script to scrape historical menu data and store in database."""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import httpx
from datetime import datetime, timedelta
from app.config import settings

async def scrape_and_store(days: int = 90, dining_halls: str = None):
    """
    Scrape historical menu data and automatically store in database.
    
    Args:
        days: Number of days to scrape (default 90, max 90)
        dining_halls: Comma-separated dining hall names (optional)
    """
    api_url = "http://localhost:8000"
    secret_key = settings.api_secret_key
    
    print(f"🚀 Starting bulk scrape for last {days} days...")
    if dining_halls:
        print(f"   Filtering by dining halls: {dining_halls}")
    
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Build URL
            url = f"{api_url}/scraper/scrape-recent"
            params = {
                "days": days,
                "store_in_db": True  # Automatically store in database
            }
            if dining_halls:
                params["dining_halls"] = dining_halls
            
            response = await client.post(
                url,
                params=params,
                headers={"X-Secret": secret_key}
            )
            response.raise_for_status()
            result = response.json()
            
            print(f"\n✅ Scraping completed!")
            print(f"   Dates scraped: {result.get('successful_dates', 0)}/{result.get('total_days', 0)}")
            print(f"   Unique items found: {result.get('total_unique_items', 0)}")
            
            if result.get("storage"):
                storage = result["storage"]
                print(f"\n💾 Database storage:")
                print(f"   Created: {storage.get('created', 0)} items")
                print(f"   Updated: {storage.get('updated', 0)} items")
                if storage.get("errors"):
                    print(f"   Errors: {len(storage['errors'])}")
            
            if result.get("failed_date_list"):
                print(f"\n⚠️  Failed dates: {len(result['failed_date_list'])}")
                if len(result['failed_date_list']) <= 10:
                    print(f"   {', '.join(result['failed_date_list'])}")
            
            return result
            
    except httpx.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 90
    dining_halls = sys.argv[2] if len(sys.argv) > 2 else None
    
    if days > 90:
        print("⚠️  Maximum 90 days allowed. Using 90 days.")
        days = 90
    
    result = asyncio.run(scrape_and_store(days, dining_halls))
    
    if result:
        print(f"\n🎉 Done! You now have {result.get('total_unique_items', 0)} menu items in your database.")
        print("   You can now test the scan endpoint with food images!")
    else:
        print("\n❌ Scraping failed. Check the errors above.")
        sys.exit(1)

