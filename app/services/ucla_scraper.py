"""UCLA Dining Menu Scraper - supports both API and web scraping fallback."""
import httpx
import requests
import json
import logging
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from app.config import settings

logger = logging.getLogger(__name__)


class UCLAScraper:
    """Scraper for UCLA dining menu data."""
    
    def __init__(self):
        self.api_base_url = settings.ucla_api_base_url
        self.api_key = settings.ucla_api_key
        self.fallback_enabled = True  # Enable web scraping fallback
        
    async def fetch_menu_via_api(
        self,
        date_str: Optional[str] = None,
        dining_hall: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch menu data using UCLA's official API.
        
        Args:
            date_str: Date in YYYY-MM-DD format (defaults to today)
            dining_hall: Optional dining hall filter
            
        Returns:
            Menu data dictionary or None if API unavailable
        """
        if not self.api_key:
            logger.warning("UCLA API key not configured, skipping API fetch")
            return None
        
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json"
            }
            
            params = {"date": date_str}
            if dining_hall:
                params["dining_hall"] = dining_hall
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Adjust endpoint based on actual UCLA API structure
                endpoint = f"{self.api_base_url}/v1/menu"
                response = await client.get(
                    endpoint,
                    headers=headers,
                    params=params
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully fetched menu via API for {date_str}")
                    return response.json()
                elif response.status_code == 403:
                    logger.warning("UCLA API access denied - may need approval")
                    return None
                else:
                    logger.warning(f"UCLA API returned {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error fetching menu via API: {e}")
            return None
    
    def fetch_menu_via_web_scraping(
        self,
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fallback web scraping method for UCLA dining menus.
        Attempts to scrape from dining.ucla.edu or alternative sources.
        
        Args:
            date_str: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary of menu data organized by dining hall and meal period
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        menu_data = {
            "date": date_str,
            "dining_halls": {}
        }
        
        # Try the old JSON endpoint first (may still work for some dates)
        menu_url = f'https://dining.ucla.edu/wp-content/uploads/jamix/menus/{date_str}.json'
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(menu_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                menu_json = response.json()
                return self._parse_jamix_menu(menu_json, date_str)
            else:
                logger.warning(f"Menu JSON not found at {menu_url}, trying alternative methods")
        except Exception as e:
            logger.warning(f"Failed to fetch menu JSON: {e}")
        
        # Alternative: Try scraping the HTML menu page
        try:
            return self._scrape_html_menu(date_str)
        except Exception as e:
            logger.error(f"HTML scraping also failed: {e}")
            return menu_data
    
    def _parse_jamix_menu(
        self,
        menu_json: Dict[str, Any],
        date_str: str
    ) -> Dict[str, Any]:
        """Parse the Jamix JSON format menu data."""
        menu_data = {
            "date": date_str,
            "dining_halls": {}
        }
        
        dining_halls = ['Bruin Plate', 'Epicuria', 'De Neve']
        meal_periods = ['Breakfast', 'Lunch', 'Dinner']
        
        for hall in dining_halls:
            for meal_period in meal_periods:
                if hall == "Epicuria" and meal_period == "Breakfast":
                    continue
                
                key = f"{hall} {meal_period}"
                menu_data["dining_halls"][key] = []
                
                # Find matching menu entries
                for dining in menu_json:
                    menu_name = dining.get('menuName', '')
                    if f"{hall} {meal_period}" not in menu_name:
                        continue
                    
                    # Extract menu items for the specified date
                    for week in dining.get('menuWeeks', []):
                        for day in week.get('menuDays', []):
                            if day.get('dayDate') != date_str:
                                continue
                            
                            for section in day.get('menuDayMealOptions', []):
                                for item in section.get('menuRows', []):
                                    item_data = {
                                        "name": item.get('menuRowName'),
                                        "recipe_id": item.get('recipeId'),
                                        "ingredient_id": item.get('ingredientId'),
                                        "section": section.get('menuDayMealOptionName')
                                    }
                                    menu_data["dining_halls"][key].append(item_data)
        
        return menu_data
    
    def _scrape_html_menu(self, date_str: str) -> Dict[str, Any]:
        """Scrape menu from HTML page (fallback method)."""
        # This would need to be implemented based on current UCLA website structure
        # For now, return empty structure
        logger.warning("HTML scraping not fully implemented - website structure may have changed")
        return {
            "date": date_str,
            "dining_halls": {},
            "source": "html_scraping",
            "note": "HTML scraping requires website structure analysis"
        }
    
    async def fetch_recipe_details(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed recipe information including nutrition."""
        url = f'https://dining.ucla.edu/wp-content/uploads/jamix/recipes/{recipe_id}.json'
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return self._extract_recipe_data(response.json())
        except Exception as e:
            logger.error(f"Error fetching recipe {recipe_id}: {e}")
        
        return None
    
    async def fetch_ingredient_details(self, ingredient_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed ingredient information including nutrition."""
        url = f'https://dining.ucla.edu/wp-content/uploads/jamix/ingredients/{ingredient_id}.json'
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return self._extract_ingredient_data(response.json())
        except Exception as e:
            logger.error(f"Error fetching ingredient {ingredient_id}: {e}")
        
        return None
    
    def _extract_recipe_data(self, recipe_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract nutrition and ingredient info from recipe JSON."""
        nutrition_info = {}
        
        if 'recipeNutritiveValues' in recipe_json:
            nutritive = recipe_json['recipeNutritiveValues']
            
            # Serving size
            if 'portionSize' in nutritive and 'portitionSizeUnit' in nutritive:
                nutrition_info['serving_size'] = f"{nutritive['portionSize']} {nutritive['portitionSizeUnit']}"
            
            # Calories
            if 'energyKcal' in nutritive and isinstance(nutritive['energyKcal'], dict):
                kcal_obj = nutritive['energyKcal']
                if 'value' in kcal_obj:
                    nutrition_info['calories'] = kcal_obj['value']
            
            # Other nutrients
            for key, value in nutritive.items():
                if key in ['portionSize', 'portitionSizeUnit', 'energyKcal']:
                    continue
                if isinstance(value, dict) and 'value' in value:
                    nutrient_name = value.get('name', key)
                    nutrition_info[nutrient_name.lower().replace(' ', '_')] = value['value']
        
        # Ingredients
        ingredients = None
        if 'recipeListOfIngredientsTranslations' in recipe_json:
            ing = recipe_json['recipeListOfIngredientsTranslations']
            if isinstance(ing, dict) and 'EN' in ing:
                ingredients = ing['EN']
            elif isinstance(ing, str):
                ingredients = ing
        
        return {
            "name": recipe_json.get('recipeNameTranslations', {}).get('EN', 'Unknown'),
            "nutrition": nutrition_info,
            "ingredients": ingredients
        }
    
    def _extract_ingredient_data(self, ingredient_json: Dict[str, Any]) -> Dict[str, Any]:
        """Extract nutrition info from ingredient JSON."""
        nutrition_info = {}
        
        if 'ingredientNutritiveValues' in ingredient_json:
            nutritive = ingredient_json['ingredientNutritiveValues']
            
            # Serving size
            if 'portionSize' in nutritive and 'portitionSizeUnit' in nutritive:
                nutrition_info['serving_size'] = f"{nutritive['portionSize']} {nutritive['portitionSizeUnit']}"
            
            # Calories
            if 'energyKcal' in nutritive and isinstance(nutritive['energyKcal'], dict):
                kcal_obj = nutritive['energyKcal']
                if 'value' in kcal_obj:
                    nutrition_info['calories'] = kcal_obj['value']
            
            # Other nutrients
            for key, value in nutritive.items():
                if key in ['portionSize', 'portitionSizeUnit', 'energyKcal']:
                    continue
                if isinstance(value, dict) and 'value' in value:
                    nutrient_name = value.get('name', key)
                    nutrition_info[nutrient_name.lower().replace(' ', '_')] = value['value']
        
        return {
            "name": ingredient_json.get('ingredientNameTranslations', {}).get('EN', 'Unknown'),
            "nutrition": nutrition_info
        }
    
    async def scrape_daily_menu(
        self,
        date_str: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main method to scrape menu data, trying API first, then web scraping.
        
        Args:
            date_str: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Complete menu data dictionary
        """
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        
        # Try API first
        api_data = await self.fetch_menu_via_api(date_str)
        if api_data:
            return {
                **api_data,
                "source": "ucla_api",
                "scraped_at": datetime.now().isoformat()
            }
        
        # Fallback to web scraping
        if self.fallback_enabled:
            logger.info(f"Falling back to web scraping for {date_str}")
            web_data = self.fetch_menu_via_web_scraping(date_str)
            return {
                **web_data,
                "source": "web_scraping",
                "scraped_at": datetime.now().isoformat()
            }
        
        return {
            "date": date_str,
            "dining_halls": {},
            "source": "none",
            "error": "No data source available"
        }

