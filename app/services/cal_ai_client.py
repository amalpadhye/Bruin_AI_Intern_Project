"""Cal AI API client for food image analysis."""
import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class CalAIClient:
    """Client for interacting with Cal AI Food Analysis API."""
    
    def __init__(self):
        self.base_url = settings.cal_ai_base_url
        self.api_key = settings.cal_ai_api_key
        if not self.api_key:
            raise ValueError("Cal AI API key not configured. Set CAL_AI_API_KEY in .env file.")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def scan_image(
        self, 
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        image_bytes: Optional[bytes] = None
    ) -> Dict[str, Any]:
        """
        Analyze a food image using Cal AI's scan-image endpoint.
        
        Based on Cal AI API documentation: https://docs.calai.app/api-reference/introduction
        
        Args:
            image_url: URL of the image to analyze
            image_base64: Base64 encoded image string
            image_bytes: Raw image bytes
            
        Returns:
            Dictionary containing predicted nutritional information
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        endpoint = f"{self.base_url}/scan-image"
        
        # Prepare request payload
        payload = {}
        if image_url:
            payload["image_url"] = image_url
        elif image_base64:
            payload["image_base64"] = image_base64
        elif image_bytes:
            # Convert bytes to base64 if needed, or use multipart form
            import base64
            payload["image_base64"] = base64.b64encode(image_bytes).decode('utf-8')
        else:
            raise ValueError("Must provide image_url, image_base64, or image_bytes")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    endpoint,
                    json=payload,
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()
                
                logger.info(f"Cal AI scan successful: {result.get('confidence', 'unknown')}")
                return result
                
        except httpx.HTTPError as e:
            logger.error(f"Cal AI API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling Cal AI: {e}")
            raise
    
    def normalize_response(self, cal_ai_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize Cal AI response to our standard nutrition format.
        
        Note: The actual Cal AI API response structure may vary.
        Adjust field mappings based on actual API documentation.
        
        Args:
            cal_ai_response: Raw response from Cal AI API
            
        Returns:
            Normalized nutrition data dictionary
        """
        normalized = {
            "calories": None,
            "protein_g": None,
            "fat_g": None,
            "carbs_g": None,
            "fiber_g": None,
            "confidence": None,
            "food_items": [],
            "source": "cal_ai"
        }
        
        # Extract nutrition facts (structure may vary based on Cal AI API)
        # Common patterns to check:
        if "nutrition" in cal_ai_response:
            nutrition = cal_ai_response["nutrition"]
            normalized["calories"] = nutrition.get("calories")
            normalized["protein_g"] = nutrition.get("protein", {}).get("value") if isinstance(nutrition.get("protein"), dict) else nutrition.get("protein")
            normalized["fat_g"] = nutrition.get("fat", {}).get("value") if isinstance(nutrition.get("fat"), dict) else nutrition.get("fat")
            normalized["carbs_g"] = nutrition.get("carbohydrates", {}).get("value") if isinstance(nutrition.get("carbohydrates"), dict) else nutrition.get("carbohydrates")
            normalized["fiber_g"] = nutrition.get("fiber", {}).get("value") if isinstance(nutrition.get("fiber"), dict) else nutrition.get("fiber")
        elif "nutritional_info" in cal_ai_response:
            # Alternative field name
            nutrition = cal_ai_response["nutritional_info"]
            normalized["calories"] = nutrition.get("calories")
            normalized["protein_g"] = nutrition.get("protein_g")
            normalized["fat_g"] = nutrition.get("fat_g")
            normalized["carbs_g"] = nutrition.get("carbs_g")
            normalized["fiber_g"] = nutrition.get("fiber_g")
        
        # Extract confidence score (may be 0-1 or 0-100)
        confidence = cal_ai_response.get("confidence") or cal_ai_response.get("confidence_score")
        if confidence is not None:
            # Normalize to 0-1 range if needed
            if confidence > 1:
                confidence = confidence / 100.0
            normalized["confidence"] = confidence
        
        # Extract identified food items
        if "food_items" in cal_ai_response:
            normalized["food_items"] = cal_ai_response["food_items"]
        elif "items" in cal_ai_response:
            normalized["food_items"] = cal_ai_response["items"]
        elif "foods" in cal_ai_response:
            normalized["food_items"] = cal_ai_response["foods"]
        
        # Extract serving size if available
        if "serving_size" in cal_ai_response:
            normalized["serving_size"] = cal_ai_response["serving_size"]
        elif "serving" in cal_ai_response:
            normalized["serving_size"] = cal_ai_response["serving"]
        
        return normalized
    
    def calculate_discrepancy(
        self,
        cal_ai_nutrition: Dict[str, Any],
        menu_nutrition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Calculate discrepancy between Cal AI prediction and menu data.
        
        Args:
            cal_ai_nutrition: Normalized Cal AI nutrition data
            menu_nutrition: Nutrition data from menu database
            
        Returns:
            Dictionary with discrepancy metrics and warnings
        """
        discrepancies = {}
        warnings = []
        
        # Compare calories
        cal_ai_cal = cal_ai_nutrition.get("calories")
        menu_cal = menu_nutrition.get("calories")
        
        if cal_ai_cal and menu_cal:
            cal_diff = abs(cal_ai_cal - menu_cal) / menu_cal
            discrepancies["calories"] = {
                "cal_ai": cal_ai_cal,
                "menu": menu_cal,
                "difference": cal_ai_cal - menu_cal,
                "percent_diff": cal_diff * 100
            }
            
            if cal_diff > settings.calorie_discrepancy_threshold:
                warnings.append(
                    f"Calorie discrepancy: {cal_diff*100:.1f}% difference "
                    f"({cal_ai_cal} vs {menu_cal})"
                )
        
        # Compare protein
        cal_ai_protein = cal_ai_nutrition.get("protein_g")
        menu_protein = menu_nutrition.get("protein_g")
        
        if cal_ai_protein and menu_protein:
            protein_diff = abs(cal_ai_protein - menu_protein) / menu_protein
            discrepancies["protein"] = {
                "cal_ai": cal_ai_protein,
                "menu": menu_protein,
                "difference": cal_ai_protein - menu_protein,
                "percent_diff": protein_diff * 100
            }
            
            if protein_diff > settings.protein_discrepancy_threshold:
                warnings.append(
                    f"Protein discrepancy: {protein_diff*100:.1f}% difference "
                    f"({cal_ai_protein}g vs {menu_protein}g)"
                )
        
        # Check confidence threshold
        confidence = cal_ai_nutrition.get("confidence", 0)
        if confidence < settings.confidence_threshold:
            warnings.append(
                f"Low confidence prediction: {confidence*100:.1f}% "
                f"(threshold: {settings.confidence_threshold*100:.1f}%)"
            )
        
        return {
            "discrepancies": discrepancies,
            "warnings": warnings,
            "has_warnings": len(warnings) > 0
        }
