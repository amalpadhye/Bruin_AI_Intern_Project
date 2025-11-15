"""Historical menu scraper to fetch multiple days of data."""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.services.ucla_scraper import UCLAScraper
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)


class HistoricalScraper:
    """Scrape historical menu data for multiple days."""
    
    def __init__(self):
        self.scraper = UCLAScraper()
        self.s3_service = S3Service()
    
    async def scrape_date_range(
        self,
        start_date: str,
        end_date: str,
        dining_halls: List[str] = None
    ) -> Dict[str, Any]:
        """
        Scrape menu data for a range of dates.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            dining_halls: Optional list of dining hall names to filter
            
        Returns:
            Dictionary with summary of scraped data
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        all_items = {}
        successful_dates = []
        failed_dates = []
        
        current_date = start
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            logger.info(f"Scraping menu for {date_str}")
            
            try:
                menu_data = await self.scraper.scrape_daily_menu(date_str)
                
                # Store raw data in S3
                s3_key = self.s3_service.upload_raw_menu(date_str, menu_data)
                
                # Extract unique menu items (with nutrition fetching)
                items = await self._extract_menu_items(menu_data, dining_halls)
                
                # Merge items (same item name across dates)
                for item in items:
                    name = item.get("name")
                    if name not in all_items:
                        all_items[name] = {
                            "name": name,
                            "calories": item.get("calories"),
                            "serving_size": item.get("serving_size"),
                            "ingredients": item.get("ingredients"),
                            "protein_g": item.get("protein_g"),
                            "fat_g": item.get("fat_g"),
                            "carbs_g": item.get("carbs_g"),
                            "dates_seen": [],
                            "dining_halls": set(),
                            "services": set()
                        }
                    
                    # Add date and dining hall info
                    all_items[name]["dates_seen"].append(date_str)
                    if item.get("dining_hall"):
                        all_items[name]["dining_halls"].add(item["dining_hall"])
                    if item.get("service"):
                        all_items[name]["services"].add(item["service"])
                
                successful_dates.append(date_str)
                logger.info(f"Successfully scraped {date_str}: {len(items)} items")
                
            except Exception as e:
                logger.error(f"Failed to scrape {date_str}: {e}")
                failed_dates.append(date_str)
            
            # Move to next day
            current_date += timedelta(days=1)
            
            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.5)
        
        # Convert sets to lists for JSON serialization
        for item in all_items.values():
            item["dining_halls"] = list(item["dining_halls"])
            item["services"] = list(item["services"])
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "total_days": (end - start).days + 1,
            "successful_dates": len(successful_dates),
            "failed_dates": len(failed_dates),
            "total_unique_items": len(all_items),
            "items": list(all_items.values()),
            "failed_date_list": failed_dates
        }
    
    async def _extract_menu_items(
        self,
        menu_data: Dict[str, Any],
        dining_halls: List[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract menu items from scraped menu data and fetch nutrition details."""
        items = []
        dining_halls_data = menu_data.get("dining_halls", {})
        
        for hall_service_key, menu_items in dining_halls_data.items():
            # Parse "Hall Service" format
            parts = hall_service_key.rsplit(" ", 1)
            if len(parts) == 2:
                dining_hall = parts[0]
                service = parts[1]
            else:
                dining_hall = parts[0]
                service = "Unknown"
            
            # Filter by dining halls if specified
            if dining_halls and dining_hall not in dining_halls:
                continue
            
            # Process each menu item
            for item_data in menu_items:
                # Try to get nutrition from recipe/ingredient if already in data
                nutrition = item_data.get("nutrition", {})
                
                # If no nutrition data, try to fetch from recipe/ingredient ID
                recipe_id = item_data.get("recipe_id") or item_data.get("recipeId")
                ingredient_id = item_data.get("ingredient_id") or item_data.get("ingredientId")
                
                if not nutrition or not nutrition.get("calories"):
                    # Fetch nutrition details
                    if recipe_id:
                        try:
                            recipe_details = await self.scraper.fetch_recipe_details(str(recipe_id))
                            if recipe_details:
                                nutrition = recipe_details.get("nutrition", {})
                                if not item_data.get("ingredients") and recipe_details.get("ingredients"):
                                    item_data["ingredients"] = recipe_details.get("ingredients")
                        except Exception as e:
                            logger.warning(f"Could not fetch recipe details for {recipe_id}: {e}")
                    elif ingredient_id:
                        try:
                            ingredient_details = await self.scraper.fetch_ingredient_details(str(ingredient_id))
                            if ingredient_details:
                                nutrition = ingredient_details.get("nutrition", {})
                        except Exception as e:
                            logger.warning(f"Could not fetch ingredient details for {ingredient_id}: {e}")
                
                # Extract nutrition values
                calories = nutrition.get("calories") if nutrition else None
                serving_size = nutrition.get("serving_size") if nutrition else "1 serving"
                
                # Extract macros - handle different field names
                protein_g = nutrition.get("protein_g") or nutrition.get("protein") if nutrition else None
                fat_g = nutrition.get("fat_g") or nutrition.get("fat") if nutrition else None
                carbs_g = nutrition.get("carbs_g") or nutrition.get("carbohydrates") or nutrition.get("carbohydrate") if nutrition else None
                fiber_g = nutrition.get("fiber_g") or nutrition.get("fiber") if nutrition else None
                
                # Handle ingredients - could be string, list, or dict
                ingredients = item_data.get("ingredients")
                if isinstance(ingredients, str):
                    # Split comma-separated string
                    ingredients = [ing.strip() for ing in ingredients.split(",")]
                elif isinstance(ingredients, dict):
                    # Extract from dict (e.g., {"EN": "ingredient1, ingredient2"})
                    if "EN" in ingredients:
                        ingredients = [ing.strip() for ing in str(ingredients["EN"]).split(",")]
                    else:
                        ingredients = list(ingredients.values())
                elif not ingredients:
                    ingredients = []
                
                item = {
                    "name": item_data.get("name", "Unknown"),
                    "dining_hall": dining_hall,
                    "service": service,
                    "calories": calories,
                    "serving_size": serving_size,
                    "protein_g": protein_g,
                    "fat_g": fat_g,
                    "carbs_g": carbs_g,
                    "fiber_g": fiber_g,
                    "ingredients": ingredients if isinstance(ingredients, list) else []
                }
                
                items.append(item)
                
                # Small delay to avoid overwhelming the server
                await asyncio.sleep(0.1)
        
        return items

