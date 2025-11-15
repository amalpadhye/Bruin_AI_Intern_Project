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
                                        "recipeId": item.get('recipeId'),  # Also store as recipeId for compatibility
                                        "ingredientId": item.get('ingredientId'),  # Also store as ingredientId
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
        # Try JSON endpoint first
        url = f'https://dining.ucla.edu/wp-content/uploads/jamix/recipes/{recipe_id}.json'
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return self._extract_recipe_data(response.json())
        except Exception as e:
            logger.debug(f"JSON recipe endpoint failed for {recipe_id}: {e}")
        
        # Fallback: Try scraping HTML page
        try:
            html_url = f'https://dining.ucla.edu/menu-item/?recipe={recipe_id}'
            response = requests.get(html_url, timeout=10)
            if response.status_code == 200:
                return self._extract_recipe_data_from_html(response.text, recipe_id)
        except Exception as e:
            logger.debug(f"HTML recipe page failed for {recipe_id}: {e}")
        
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
    
    def _extract_recipe_data_from_html(self, html_content: str, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Extract nutrition data from HTML menu item page (e.g., /menu-item/?recipe=1193)."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            nutrition_info = {}
            ingredients = []
            
            # Try to find nutrition information in the page
            # Look for nutrition facts section
            nutrition_section = soup.find('div', class_=lambda x: x and ('nutrition' in str(x).lower() or 'calorie' in str(x).lower()))
            
            if nutrition_section:
                # Try to extract calories
                import re
                text = nutrition_section.get_text()
                
                # Look for calories
                cal_match = re.search(r'calories?[:\s]+(\d+)', text, re.IGNORECASE)
                if cal_match:
                    nutrition_info['calories'] = int(cal_match.group(1))
                
                # Look for protein
                protein_match = re.search(r'protein[:\s]+(\d+\.?\d*)\s*g', text, re.IGNORECASE)
                if protein_match:
                    nutrition_info['protein_g'] = float(protein_match.group(1))
                
                # Look for fat
                fat_match = re.search(r'fat[:\s]+(\d+\.?\d*)\s*g', text, re.IGNORECASE)
                if fat_match:
                    nutrition_info['fat_g'] = float(fat_match.group(1))
                
                # Look for carbs/carbohydrates
                carbs_match = re.search(r'carbohydrates?[:\s]+(\d+\.?\d*)\s*g', text, re.IGNORECASE)
                if carbs_match:
                    nutrition_info['carbs_g'] = float(carbs_match.group(1))
                
                # Look for fiber
                fiber_match = re.search(r'fiber[:\s]+(\d+\.?\d*)\s*g', text, re.IGNORECASE)
                if fiber_match:
                    nutrition_info['fiber_g'] = float(fiber_match.group(1))
                
                # Look for serving size
                serving_match = re.search(r'serving\s+size[:\s]+(\d+\.?\d*)\s*(oz|ounce|cup|g|gram)', text, re.IGNORECASE)
                if serving_match:
                    nutrition_info['serving_size'] = f"{serving_match.group(1)} {serving_match.group(2)}"
            
            # Try to find ingredients
            ingredients_section = soup.find('div', class_=lambda x: x and 'ingredient' in str(x).lower()) or \
                                soup.find('ul', class_=lambda x: x and 'ingredient' in str(x).lower()) or \
                                soup.find('section', class_=lambda x: x and 'ingredient' in str(x).lower())
            
            if ingredients_section:
                ingredient_items = ingredients_section.find_all('li')
                if ingredient_items:
                    ingredients = [item.get_text(strip=True) for item in ingredient_items]
                else:
                    # Try to extract from text
                    ing_text = ingredients_section.get_text()
                    if ',' in ing_text:
                        ingredients = [ing.strip() for ing in ing_text.split(',')]
            
            # Try to find item name
            name_elem = soup.find('h1') or soup.find('h2', class_=lambda x: x and 'recipe' in str(x).lower())
            name_text = name_elem.get_text(strip=True) if name_elem else 'Unknown'
            
            if nutrition_info:
                return {
                    "name": name_text,
                    "nutrition": nutrition_info,
                    "ingredients": ingredients if ingredients else None
                }
            
        except Exception as e:
            logger.error(f"Error parsing HTML for recipe {recipe_id}: {e}")
        
        return None
    
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

