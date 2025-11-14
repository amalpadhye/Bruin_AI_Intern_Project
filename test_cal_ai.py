"""Test script for Cal AI integration."""
import asyncio
import sys
from pathlib import Path
from app.services.cal_ai_client import CalAIClient
from app.config import settings

async def test_cal_ai():
    """Test Cal AI client with a sample image."""
    
    # Check if API key is set
    if not settings.cal_ai_api_key or settings.cal_ai_api_key == "your_cal_ai_api_key_here":
        print("ERROR: Cal AI API key not configured in .env file")
        print("Please set CAL_AI_API_KEY in your .env file")
        return
    
    client = CalAIClient()
    
    # Test with image file if provided
    if len(sys.argv) > 1:
        image_path = Path(sys.argv[1])
        if not image_path.exists():
            print(f"ERROR: Image file not found: {image_path}")
            return
        
        print(f"Testing Cal AI with image: {image_path}")
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        try:
            # Call Cal AI
            print("Calling Cal AI API...")
            response = await client.scan_image(image_bytes=image_bytes)
            
            print("\n=== Raw Cal AI Response ===")
            import json
            print(json.dumps(response, indent=2))
            
            # Normalize
            print("\n=== Normalized Response ===")
            normalized = client.normalize_response(response)
            print(json.dumps(normalized, indent=2))
            
            # Test discrepancy calculation
            print("\n=== Testing Discrepancy Logic ===")
            menu_nutrition = {
                "calories": 300,
                "protein_g": 20,
                "fat_g": 10,
                "carbs_g": 40
            }
            discrepancy = client.calculate_discrepancy(normalized, menu_nutrition)
            print(json.dumps(discrepancy, indent=2))
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Usage: python test_cal_ai.py <path_to_image>")
        print("\nExample:")
        print("  python test_cal_ai.py test_images/food.jpg")

if __name__ == "__main__":
    asyncio.run(test_cal_ai())

