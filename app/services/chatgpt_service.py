"""ChatGPT service for food image analysis and menu matching."""
import httpx
import logging
import base64
from typing import Dict, Any, Optional, List
from app.config import settings

logger = logging.getLogger(__name__)


class ChatGPTService:
    """Service for interacting with OpenAI ChatGPT API."""
    
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = "https://api.openai.com/v1"
        if not self.api_key:
            raise ValueError("OpenAI API key not configured. Set OPENAI_API_KEY in .env file.")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def analyze_food_image(
        self,
        image_bytes: bytes,
        menu_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze food image and match to UCLA menu items using ChatGPT Vision.
        
        Args:
            image_bytes: Food image bytes
            menu_items: List of menu items with names and nutrition info
            
        Returns:
            Dictionary with:
            - matched_item: Menu item dict if match found, None otherwise
            - confidence: Confidence level (high/medium/low)
            - serving_size_estimate: Estimated serving size (e.g., "3 oz")
            - estimated_calories: ChatGPT's calorie estimate
            - reasoning: Why it matched or didn't match
        """
        # Convert image to base64
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # Build menu context for ChatGPT
        menu_context = self._build_menu_context(menu_items)
        
        prompt = f"""You are analyzing a food image to match it to UCLA dining hall menu items.

Available menu items:
{menu_context}

CRITICAL: A single plate/image may contain MULTIPLE different foods/meals. Identify ALL foods you see.

IMPORTANT MATCHING RULES:
1. **Break down combined dishes**: If you see something like "Grilled Chicken Thigh with Kale", break it into separate components:
   - "Grilled Chicken Thigh" → match to menu item like "DN CHICKEN THIGH HONEY LIME" (or similar chicken thigh item)
   - "Kale" → match to menu item like "KALE" or "SAUTEED KALE"
   
2. **One visual item = multiple menu items**: A single dish on the plate might be made up of multiple menu items. For example:
   - "Chicken and Rice Bowl" should match: "CHICKEN" + "RICE" (two separate menu items)
   - "Salad with Dressing" should match: "SALAD" + "DRESSING" (two separate menu items)
   
3. **Flexible matching**: Match based on main ingredients, not exact names:
   - "Grilled Chicken" can match "DN CHICKEN THIGH HONEY LIME" (both are chicken)
   - "Roasted Vegetables" can match "ROASTED BROCCOLI" + "ROASTED CARROTS" (if you see multiple vegetables)
   - Look for key words: chicken, beef, rice, kale, broccoli, etc.

Your task:
1. Identify ALL foods/components in the image (break down combined dishes into separate components)
2. For EACH component, find the BEST matching menu item(s) from the list above
   - If a component matches multiple menu items, list each match separately
   - Be flexible: "Chicken Thigh" can match "DN CHICKEN THIGH HONEY LIME" even if the description doesn't exactly match
3. For EACH matched component, estimate the serving size IN OUNCES (oz)
   - For liquids: 1 cup = 8 oz, 1/2 cup = 4 oz, etc.
   - For solids: estimate weight in ounces based on visual size
   - Always use "X oz" format
4. For EACH component, estimate the calories
5. Provide detailed classification for each component including:
   - What you see (description)
   - Why you matched it to that menu item (be flexible with matching)
   - Ingredients you can identify
   - Estimated calories and why

MATCHING EXAMPLES:
- See "Grilled Chicken Thigh with Kale" → Match: "DN CHICKEN THIGH HONEY LIME" (chicken) + "KALE" (vegetable)
- See "Rice Bowl with Chicken and Vegetables" → Match: "RICE" + "CHICKEN" + "BROCCOLI" (or whatever vegetables you see)
- See "Salad with Dressing" → Match: "SALAD" + "DRESSING" (two separate items)

IMPORTANT:
- Break down combined dishes into their component parts
- Match each component to the closest menu item (be flexible with names)
- If you cannot confidently identify a component, mark it as "NO_MATCH"
- List ALL components you see, even if some don't match
- ALWAYS estimate serving size in OUNCES (oz), not cups, pieces, or other units
- One visual food item on the plate can result in MULTIPLE matches (one per component)

Respond in JSON format:
{{
    "foods": [
        {{
            "matched_item_name": "name of menu item or NO_MATCH",
            "confidence": "high/medium/low",
            "serving_size_estimate": "e.g., 4 oz or 6 oz (ALWAYS in ounces)",
            "estimated_calories": 250,
            "classification": {{
                "description": "what you see in the image (the specific component)",
                "visual_features": ["color", "texture", "shape", "etc"],
                "identified_ingredients": ["ingredient1", "ingredient2"],
                "matching_reasoning": "why this component matches the menu item (be flexible)"
            }},
            "reasoning": "brief explanation"
        }}
    ],
    "total_estimated_calories": 500,
    "overall_confidence": "high/medium/low"
}}"""

        try:
            # Increased timeout for image analysis (can take longer with large images)
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": "gpt-4o",  # or "gpt-4-vision-preview" if available
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.3  # Lower temperature for more consistent results
                    },
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()
                
                # Extract JSON from response
                content = result["choices"][0]["message"]["content"]
                import json
                analysis = json.loads(content)
                
                # Handle both old format (single food) and new format (multiple foods)
                if "foods" not in analysis:
                    # Convert old format to new format
                    analysis = {
                        "foods": [{
                            "matched_item_name": analysis.get("matched_item_name", "NO_MATCH"),
                            "confidence": analysis.get("confidence", "low"),
                            "serving_size_estimate": analysis.get("serving_size_estimate", "1 serving"),
                            "estimated_calories": analysis.get("estimated_calories", 0),
                            "classification": {
                                "description": analysis.get("reasoning", ""),
                                "visual_features": [],
                                "identified_ingredients": [],
                                "matching_reasoning": analysis.get("reasoning", "")
                            },
                            "reasoning": analysis.get("reasoning", "")
                        }],
                        "total_estimated_calories": analysis.get("estimated_calories", 0),
                        "overall_confidence": analysis.get("confidence", "low")
                    }
                
                logger.info(f"ChatGPT analysis: {len(analysis.get('foods', []))} food(s) identified")
                return analysis
                
        except httpx.ReadTimeout as e:
            logger.error(f"ChatGPT API timeout: {e}")
            raise ValueError("ChatGPT API request timed out. The image may be too large or the service is slow. Please try again with a smaller image.")
        except httpx.HTTPError as e:
            logger.error(f"ChatGPT API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling ChatGPT: {e}")
            raise
    
    def _build_menu_context(self, menu_items: List[Dict[str, Any]]) -> str:
        """Build a formatted string of menu items for ChatGPT context."""
        context_parts = []
        # Increase limit to 100 items to give ChatGPT more options for matching
        for item in menu_items[:100]:  # Limit to 100 items to avoid token limits
            name = item.get("name", "Unknown")
            calories = item.get("calories", "N/A")
            serving_size = item.get("serving_size", "N/A")
            # Include key ingredients if available to help with matching
            ingredients = item.get("ingredients", [])
            ingredients_str = ""
            if ingredients and isinstance(ingredients, list) and len(ingredients) > 0:
                # Show first 3 ingredients as hints
                ingredients_str = f" [Ingredients: {', '.join(str(ing) for ing in ingredients[:3])}]"
            context_parts.append(f"- {name} ({serving_size}): {calories} calories{ingredients_str}")
        
        return "\n".join(context_parts)
    
    async def estimate_serving_size_multiplier(
        self,
        menu_serving_size: str,
        estimated_serving_size: str
    ) -> float:
        """
        Calculate multiplier for serving size (e.g., menu says 1 oz, user has 3 oz = 3.0x).
        
        Args:
            menu_serving_size: Serving size from menu (e.g., "1 oz", "1 cup")
            estimated_serving_size: Estimated serving size from image (e.g., "3 oz", "1.5 cups")
            
        Returns:
            Multiplier (e.g., 3.0 for 3x the menu serving)
        """
        # Simple parsing - can be improved
        # Extract numbers and units
        try:
            menu_num = self._extract_number(menu_serving_size)
            menu_unit = self._extract_unit(menu_serving_size)
            est_num = self._extract_number(estimated_serving_size)
            est_unit = self._extract_unit(estimated_serving_size)
            
            # If units match, calculate multiplier
            if menu_unit.lower() == est_unit.lower():
                if menu_num > 0:
                    return est_num / menu_num
            # If different units, use ChatGPT for conversion
            return await self._convert_serving_sizes(menu_serving_size, estimated_serving_size)
        except:
            # Fallback: assume 1.0 if parsing fails
            return 1.0
    
    def _extract_number(self, text: str) -> float:
        """Extract first number from text."""
        import re
        match = re.search(r'(\d+\.?\d*)', text)
        return float(match.group(1)) if match else 1.0
    
    def _extract_unit(self, text: str) -> str:
        """Extract unit from text."""
        import re
        units = ['oz', 'ounce', 'cup', 'cups', 'piece', 'pieces', 'g', 'gram', 'lb', 'pound']
        text_lower = text.lower()
        for unit in units:
            if unit in text_lower:
                return unit
        return ""
    
    async def suggest_food_info(
        self,
        image_bytes: bytes,
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Suggest food name and calories for an unmatched food item.
        
        Args:
            image_bytes: Food image bytes
            classification: Classification data from initial analysis
            
        Returns:
            Dictionary with suggested food name and estimated calories
        """
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        description = classification.get("description", "Unknown food")
        visual_features = classification.get("visual_features", [])
        ingredients = classification.get("identified_ingredients", [])
        
        prompt = f"""You are analyzing a food item that could not be matched to a menu.

What you see:
- Description: {description}
- Visual features: {', '.join(visual_features) if visual_features else 'N/A'}
- Ingredients identified: {', '.join(ingredients) if ingredients else 'N/A'}

Your task:
1. Suggest what this food likely is (be specific, e.g., "Grilled Chicken Breast" not just "Chicken")
2. Estimate the calories for this serving
3. Estimate the serving size IN OUNCES (oz) - convert everything to ounces (e.g., "4 oz", "6 oz", "8 oz")
   - For liquids: 1 cup = 8 oz, 1/2 cup = 4 oz, etc.
   - For solids: estimate weight in ounces based on visual size
   - Always use "X oz" format
4. Suggest possible ingredients

IMPORTANT: ALWAYS estimate serving size in OUNCES (oz), not cups, pieces, or other units.

Respond in JSON format:
{{
    "suggested_name": "specific food name",
    "estimated_calories": 250,
    "estimated_serving_size": "4 oz (ALWAYS in ounces)",
    "suggested_ingredients": ["ingredient1", "ingredient2"],
    "confidence": "high/medium/low",
    "reasoning": "why you think this is the food and why this calorie estimate"
}}"""

        try:
            # Increased timeout for food suggestion analysis
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": "gpt-4o",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": prompt
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{image_base64}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "response_format": {"type": "json_object"},
                        "temperature": 0.3
                    },
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                import json
                return json.loads(content)
        except httpx.ReadTimeout as e:
            logger.error(f"ChatGPT suggestion timeout: {e}")
            return {
                "suggested_name": "Unknown Food",
                "estimated_calories": 0,
                "estimated_serving_size": "1 serving",
                "suggested_ingredients": [],
                "confidence": "low",
                "reasoning": "Request timed out. Please try again."
            }
        except Exception as e:
            logger.error(f"Error getting food suggestion: {e}")
            return {
                "suggested_name": "Unknown Food",
                "estimated_calories": 0,
                "estimated_serving_size": "1 serving",
                "suggested_ingredients": [],
                "confidence": "low",
                "reasoning": "Could not analyze food"
            }
    
    async def _convert_serving_sizes(self, menu_size: str, est_size: str) -> float:
        """Use ChatGPT to convert between different serving size units."""
        prompt = f"""Convert serving sizes:
Menu item serving size: {menu_size}
Estimated serving size: {est_size}

Calculate the multiplier (how many times the menu serving size is the estimated size).
Return only a number (e.g., 2.5 or 0.5).
If you cannot convert, return 1.0."""

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": "gpt-4o",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.1
                    },
                    headers=self.headers
                )
                response.raise_for_status()
                result = response.json()
                content = result["choices"][0]["message"]["content"].strip()
                return float(content)
        except:
            return 1.0

