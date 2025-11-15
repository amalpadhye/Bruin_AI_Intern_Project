"""Scan endpoint for food image analysis with ChatGPT menu matching."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from typing import Optional, List, Dict, Any
import uuid
import logging
from app.services.chatgpt_service import ChatGPTService
from app.services.s3_service import S3Service
from app.config import settings
from app.db.crud import get_menu_items_dict
from app.db.database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("")
async def scan_food_image(
    image: UploadFile = File(...),
    dining_halls: Optional[str] = Query(None, description="Comma-separated dining hall names (e.g., 'Bruin Plate,Epicuria')"),
    s3_service: S3Service = Depends(lambda: S3Service()),
    db: Session = Depends(get_db)
):
    """
    Analyze food image using ChatGPT to match to UCLA menu items.
    
    Flow:
    1. Store image in S3
    2. Get menu items from database (filtered by dining halls if provided)
    3. Use ChatGPT to match food(s) to menu item(s) - handles multiple foods per image
    4. Estimate serving size for each food
    5. Compare ChatGPT calorie estimate vs menu calories for each
    6. Return match results with warnings if needed
    
    Args:
        image: Food image file
        dining_halls: Optional comma-separated list of dining hall names to filter menu items
    """
    # Upload image to S3
    scan_id = str(uuid.uuid4())
    user_id = "temp_user"  # TODO: Extract from auth token
    image_bytes = await image.read()
    image_key = s3_service.upload_scan_image(user_id, image_bytes, scan_id, image.content_type)
    
    # Check if ChatGPT is configured
    if not settings.openai_api_key:
        return {
            "scan_id": scan_id,
            "image_key": image_key,
            "error": "OpenAI API key not configured",
            "message": "Please configure OPENAI_API_KEY in .env file"
        }
    
    try:
        chatgpt_service = ChatGPTService()
        
        # Parse dining halls filter
        dining_hall_list = None
        if dining_halls:
            dining_hall_list = [h.strip() for h in dining_halls.split(",")]
        
        # Get menu items from database (filtered by dining halls)
        menu_items = get_menu_items_dict(db, dining_hall_list)
        
        if not menu_items:
            return {
                "scan_id": scan_id,
                "image_key": image_key,
                "error": "No menu items found",
                "message": "No menu items available in database. Please scrape menus first."
            }
        
        # Analyze image with ChatGPT (handles multiple foods)
        analysis = await chatgpt_service.analyze_food_image(image_bytes, menu_items)
        
        foods_identified = analysis.get("foods", [])
        
        if not foods_identified:
            return {
                "scan_id": scan_id,
                "image_key": image_key,
                "all_matched": False,
                "total_foods": 0,
                "matched_count": 0,
                "unmatched_count": 0,
                "foods": [],
                "error": "No foods identified",
                "message": "Could not identify any foods in the image. Please try a different image."
            }
        
        # Process each identified food
        results = []
        all_matched = True
        has_warning = False
        
        for food_analysis in foods_identified:
            matched_item_name = food_analysis.get("matched_item_name")
            confidence = food_analysis.get("confidence", "low")
            
            # Check if match found
            if matched_item_name == "NO_MATCH" or confidence == "low":
                # Get ChatGPT suggestion for unmatched food
                try:
                    suggestion = await chatgpt_service.suggest_food_info(
                        image_bytes,
                        food_analysis.get("classification", {})
                    )
                except Exception as e:
                    logger.error(f"Error getting food suggestion: {e}")
                    suggestion = {
                        "suggested_name": "Unknown Food",
                        "estimated_calories": food_analysis.get("estimated_calories", 0),
                        "estimated_serving_size": food_analysis.get("serving_size_estimate", "1 serving"),
                        "suggested_ingredients": [],
                        "confidence": "low",
                        "reasoning": "Could not analyze"
                    }
                
                results.append({
                    "matched": False,
                    "classification": food_analysis.get("classification", {}),
                    "reasoning": food_analysis.get("reasoning", ""),
                    "suggestion": {
                        "suggested_name": suggestion.get("suggested_name", "Unknown Food"),
                        "estimated_calories": suggestion.get("estimated_calories", 0),
                        "estimated_serving_size": suggestion.get("estimated_serving_size", "1 serving"),
                        "suggested_ingredients": suggestion.get("suggested_ingredients", []),
                        "confidence": suggestion.get("confidence", "low"),
                        "reasoning": suggestion.get("reasoning", "")
                    },
                    "chatgpt_original_estimate": food_analysis.get("estimated_calories", 0)
                })
                all_matched = False
                continue
            
            # Find the matched menu item
            matched_item = next(
                (item for item in menu_items if item.get("name") == matched_item_name),
                None
            )
            
            if not matched_item:
                results.append({
                    "matched": False,
                    "error": "Matched item not found in database",
                    "message": "Please enter this food information manually",
                    "matched_item_name": matched_item_name,
                    "classification": food_analysis.get("classification", {})
                })
                all_matched = False
                continue
            
            # Calculate serving size multiplier
            menu_serving_size = matched_item.get("serving_size", "1 serving")
            estimated_serving_size = food_analysis.get("serving_size_estimate", "1 serving")
            multiplier = await chatgpt_service.estimate_serving_size_multiplier(
                menu_serving_size,
                estimated_serving_size
            )
            
            # Get menu calories (already stored in database)
            # Handle None values - if calories is None, use 0
            menu_calories_per_serving = matched_item.get("calories") or 0
            if menu_calories_per_serving is None:
                menu_calories_per_serving = 0
            
            menu_calories_total = menu_calories_per_serving * multiplier
            
            # Get ChatGPT calorie estimate
            chatgpt_calories = food_analysis.get("estimated_calories", 0) or 0
            if chatgpt_calories is None:
                chatgpt_calories = 0
            
            # Calculate difference percentage
            if menu_calories_total > 0:
                calorie_diff_percent = abs(chatgpt_calories - menu_calories_total) / menu_calories_total
            else:
                # If menu has no calories, use ChatGPT estimate only
                calorie_diff_percent = 0.0  # No comparison possible
            
            # Check if difference is > 50% (only if we have menu calories to compare)
            food_warning = False
            if menu_calories_total > 0 and calorie_diff_percent > 0.5:
                food_warning = True
                has_warning = True
            
            food_result = {
                "matched": True,
                "matched_item": {
                    "name": matched_item.get("name"),
                    "id": matched_item.get("id"),
                    "menu_calories_per_serving": menu_calories_per_serving,
                    "menu_serving_size": menu_serving_size,
                    "ingredients": matched_item.get("ingredients", []) or [],
                    "dining_hall": matched_item.get("dining_hall"),
                    "service": matched_item.get("service")
                },
                "serving_size": {
                    "menu_serving_size": menu_serving_size,
                    "estimated_serving_size": estimated_serving_size,
                    "multiplier": multiplier
                },
                "calories": {
                    "menu_calories": round(menu_calories_total, 0) if menu_calories_total else 0,
                    "chatgpt_estimate": chatgpt_calories,
                    "difference_percent": round(calorie_diff_percent * 100, 1) if menu_calories_total > 0 else None
                },
                "classification": food_analysis.get("classification", {}),
                "confidence": confidence,
                "reasoning": food_analysis.get("reasoning", ""),
                "warn": food_warning
            }
            
            if food_warning:
                food_result["warning"] = {
                    "message": f"Large calorie difference detected ({food_result['calories']['difference_percent']}%)",
                    "details": f"Menu: {food_result['calories']['menu_calories']} cal, ChatGPT estimate: {food_result['calories']['chatgpt_estimate']} cal",
                    "action_required": "Please verify and choose which calorie count to use, or enter a custom amount"
                }
            
            results.append(food_result)
        
        # Calculate totals (include unmatched foods with their estimates)
        total_menu_calories = sum(r.get("calories", {}).get("menu_calories", 0) for r in results if r.get("matched"))
        total_chatgpt_calories = sum(
            r.get("calories", {}).get("chatgpt_estimate", 0) if r.get("matched") 
            else r.get("suggestion", {}).get("estimated_calories", 0) or r.get("chatgpt_original_estimate", 0)
            for r in results
        )
        
        # Count matched vs unmatched
        matched_count = sum(1 for r in results if r.get("matched"))
        unmatched_count = len(results) - matched_count
        
        return {
            "scan_id": scan_id,
            "image_key": image_key,
            "all_matched": all_matched,
            "total_foods": len(foods_identified),
            "matched_count": matched_count,
            "unmatched_count": unmatched_count,
            "foods": results,
            "totals": {
                "menu_calories": total_menu_calories,
                "chatgpt_estimate": total_chatgpt_calories
            },
            "overall_confidence": analysis.get("overall_confidence", "low"),
            "warn": has_warning,
            "dining_halls_filtered": dining_hall_list
        }
        
    except ValueError as e:
        # API key not configured
        return {
            "scan_id": scan_id,
            "image_key": image_key,
            "error": str(e),
            "message": "Please configure OPENAI_API_KEY in .env file",
            "all_matched": False,
            "total_foods": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "foods": []
        }
    except ValueError as e:
        # Handle specific errors like timeout
        error_message = str(e)
        return {
            "scan_id": scan_id,
            "image_key": image_key,
            "error": "Food analysis failed",
            "message": error_message,
            "all_matched": False,
            "total_foods": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "foods": []
        }
    except Exception as e:
        logger.error(f"Error in scan endpoint: {e}", exc_info=True)
        # Return error in expected format instead of raising HTTPException
        error_message = str(e)
        if "429" in error_message or "Too Many Requests" in error_message:
            error_message = "OpenAI API rate limit exceeded. Please try again in a moment."
        elif "401" in error_message or "Unauthorized" in error_message:
            error_message = "OpenAI API key is invalid. Please check your OPENAI_API_KEY."
        elif "timeout" in error_message.lower() or "ReadTimeout" in error_message:
            error_message = "Request timed out. The image may be too large or the service is slow. Please try again with a smaller image or wait a moment."
        
        return {
            "scan_id": scan_id,
            "image_key": image_key,
            "error": "Food analysis failed",
            "message": error_message,
            "all_matched": False,
            "total_foods": 0,
            "matched_count": 0,
            "unmatched_count": 0,
            "foods": []
        }


