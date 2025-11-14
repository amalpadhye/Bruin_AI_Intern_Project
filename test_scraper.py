"""Test script for UCLA menu scraper."""
import asyncio
import sys
from datetime import datetime
from app.services.ucla_scraper import UCLAScraper
from app.services.s3_service import S3Service
import json

async def test_scraper():
    """Test UCLA menu scraper."""
    
    scraper = UCLAScraper()
    
    # Get date from command line or use today
    date_str = sys.argv[1] if len(sys.argv) > 1 else datetime.now().strftime("%Y-%m-%d")
    
    print(f"Testing UCLA scraper for date: {date_str}")
    print("=" * 50)
    
    try:
        # Try API first
        print("\n1. Attempting API fetch...")
        api_data = await scraper.fetch_menu_via_api(date_str)
        if api_data:
            print("✓ API fetch successful!")
            print(json.dumps(api_data, indent=2)[:500] + "...")
        else:
            print("✗ API fetch failed or not available")
        
        # Try web scraping
        print("\n2. Attempting web scraping fallback...")
        web_data = scraper.fetch_menu_via_web_scraping(date_str)
        if web_data.get("dining_halls"):
            print(f"✓ Web scraping successful! Found {len(web_data['dining_halls'])} dining halls")
            for hall, items in list(web_data["dining_halls"].items())[:3]:
                print(f"  - {hall}: {len(items)} items")
        else:
            print("✗ Web scraping returned no data")
        
        # Full scrape
        print("\n3. Running full scrape (API + fallback)...")
        full_data = await scraper.scrape_daily_menu(date_str)
        print(f"Source: {full_data.get('source', 'unknown')}")
        print(f"Dining halls: {len(full_data.get('dining_halls', {}))}")
        
        # Test recipe/ingredient fetch
        print("\n4. Testing recipe/ingredient fetch...")
        # Try to find a recipe_id from the menu data
        recipe_id = None
        for hall_data in full_data.get("dining_halls", {}).values():
            for item in hall_data[:5]:  # Check first 5 items
                if item.get("recipe_id"):
                    recipe_id = item["recipe_id"]
                    break
            if recipe_id:
                break
        
        if recipe_id:
            print(f"Fetching recipe details for ID: {recipe_id}")
            recipe = await scraper.fetch_recipe_details(recipe_id)
            if recipe:
                print(f"✓ Recipe: {recipe.get('name')}")
                print(f"  Calories: {recipe.get('nutrition', {}).get('calories', 'N/A')}")
        else:
            print("No recipe_id found in menu data to test")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_scraper())

