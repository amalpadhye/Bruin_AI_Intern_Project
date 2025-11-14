"""Service for normalizing scraped menu data to Postgres format."""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class MenuNormalizer:
    """Normalizes raw scraped menu data to database schema format."""
    
    @staticmethod
    def normalize_menu_item(
        item_data: Dict[str, Any],
        dining_hall: str,
        service: str,
        date: str
    ) -> Dict[str, Any]:
        """
        Normalize a single menu item to database format.
        
        Args:
            item_data: Raw item data from scraper
            dining_hall: Dining hall name (e.g., "Bruin Plate")
            service: Meal service (e.g., "Breakfast", "Lunch", "Dinner")
            date: Date in YYYY-MM-DD format
            
        Returns:
            Normalized menu item dictionary
        """
        normalized = {
            "id": str(uuid.uuid4()),
            "dining_hall": dining_hall,
            "service": service,
            "date": date,
            "name": item_data.get("name", "Unknown"),
            "ucla_item_id": item_data.get("recipe_id") or item_data.get("ingredient_id"),
            "raw_key": None,  # S3 key for raw data
            "image_key": None,
            "nutrition_facts": []
        }
        
        # Extract nutrition if available
        nutrition = item_data.get("nutrition", {})
        if nutrition:
            nutrition_entry = {
                "item_id": normalized["id"],
                "source": "menu_scraper",
                "calories": nutrition.get("calories"),
                "protein_g": nutrition.get("protein_g") or nutrition.get("protein"),
                "fat_g": nutrition.get("fat_g") or nutrition.get("fat"),
                "carbs_g": nutrition.get("carbs_g") or nutrition.get("carbohydrates"),
                "fiber_g": nutrition.get("fiber_g") or nutrition.get("fiber"),
                "confidence": 1.0,  # Menu data is authoritative
            }
            normalized["nutrition_facts"].append(nutrition_entry)
        
        return normalized
    
    @staticmethod
    def normalize_scraped_menu(
        scraped_data: Dict[str, Any],
        s3_raw_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Normalize entire scraped menu data to list of menu items.
        
        Args:
            scraped_data: Raw menu data from scraper
            s3_raw_key: Optional S3 key where raw data is stored
            
        Returns:
            List of normalized menu item dictionaries
        """
        normalized_items = []
        date_str = scraped_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        dining_halls = scraped_data.get("dining_halls", {})
        
        for hall_service_key, items in dining_halls.items():
            # Parse "Hall Service" format
            parts = hall_service_key.rsplit(" ", 1)
            if len(parts) == 2:
                dining_hall = parts[0]
                service = parts[1]
            else:
                # Fallback parsing
                dining_hall = parts[0]
                service = "Unknown"
            
            for item_data in items:
                normalized = MenuNormalizer.normalize_menu_item(
                    item_data,
                    dining_hall,
                    service,
                    date_str
                )
                normalized["raw_key"] = s3_raw_key
                normalized_items.append(normalized)
        
        logger.info(f"Normalized {len(normalized_items)} menu items from scraped data")
        return normalized_items
    
    @staticmethod
    def extract_nutrition_from_recipe(recipe_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract nutrition facts from recipe JSON structure.
        
        Args:
            recipe_data: Recipe data from UCLA scraper
            
        Returns:
            Nutrition facts dictionary
        """
        nutrition = recipe_data.get("Nutrition Info", {})
        
        # Parse calories (may be string like "250 kcal")
        calories = None
        if "Calories" in nutrition:
            cal_str = nutrition["Calories"]
            if isinstance(cal_str, str):
                calories = int(cal_str.split()[0]) if cal_str.split() else None
            else:
                calories = cal_str
        
        # Extract other nutrients
        result = {
            "calories": calories,
            "protein_g": MenuNormalizer._parse_nutrient(nutrition, "Protein"),
            "fat_g": MenuNormalizer._parse_nutrient(nutrition, "Fat"),
            "carbs_g": MenuNormalizer._parse_nutrient(nutrition, "Carbohydrates"),
            "fiber_g": MenuNormalizer._parse_nutrient(nutrition, "Fiber"),
        }
        
        return result
    
    @staticmethod
    def _parse_nutrient(nutrition: Dict[str, Any], nutrient_name: str) -> Optional[float]:
        """Parse a nutrient value from nutrition dict."""
        if nutrient_name in nutrition:
            value = nutrition[nutrient_name]
            if isinstance(value, str):
                # Extract number from string like "25 g"
                try:
                    return float(value.split()[0])
                except (ValueError, IndexError):
                    return None
            return float(value) if value is not None else None
        return None

