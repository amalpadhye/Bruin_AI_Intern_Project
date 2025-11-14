"""Scan endpoint for food image analysis."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from typing import Optional
import uuid
from app.services.cal_ai_client import CalAIClient
from app.services.s3_service import S3Service
from app.config import settings

router = APIRouter(prefix="/scan", tags=["scan"])


@router.post("")
async def scan_food_image(
    image: UploadFile = File(...),
    cal_ai_client: CalAIClient = Depends(lambda: CalAIClient()),
    s3_service: S3Service = Depends(lambda: S3Service())
):
    """
    Analyze a food image using Cal AI.
    
    Expected flow:
    1. Client uploads image to S3 via presigned URL
    2. Client calls this endpoint with image_key
    3. We fetch image from S3, call Cal AI, store result
    4. Return normalized prediction with discrepancy warnings
    """
    # For now, accept direct upload (alternative: accept image_key and fetch from S3)
    image_bytes = await image.read()
    
    # Upload to S3
    scan_id = str(uuid.uuid4())
    # In production, user_id would come from JWT token
    user_id = "temp_user"  # TODO: Extract from auth token
    image_key = s3_service.upload_scan_image(user_id, image_bytes, scan_id, image.content_type)
    
    # Call Cal AI
    try:
        cal_ai_response = await cal_ai_client.scan_image(image_bytes=image_bytes)
        normalized = cal_ai_client.normalize_response(cal_ai_response)
        
        # Store Cal AI result in S3
        cal_ai_key = s3_service.upload_cal_ai_result(user_id, scan_id, cal_ai_response)
        
        # TODO: Compare with menu data if item_id is provided
        # For now, return prediction without comparison
        return {
            "scan_id": scan_id,
            "image_key": image_key,
            "cal_ai_key": cal_ai_key,
            "predicted": normalized,
            "delta_vs_menu": None,  # TODO: Implement menu comparison
            "warn": normalized.get("confidence", 0) < settings.confidence_threshold
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cal AI analysis failed: {str(e)}")


@router.post("/compare")
async def scan_and_compare(
    image_key: str,
    item_id: Optional[str] = None,
    cal_ai_client: CalAIClient = Depends(lambda: CalAIClient()),
    s3_service: S3Service = Depends(lambda: S3Service())
):
    """
    Scan image and compare with menu item if item_id provided.
    
    Args:
        image_key: S3 key of uploaded image
        item_id: Optional menu item ID to compare against
    """
    # Fetch image from S3
    # TODO: Implement S3 image download
    # For now, this is a placeholder
    
    # Call Cal AI
    # Compare with menu data if item_id provided
    # Return discrepancy analysis
    
    return {"message": "Comparison endpoint - TODO: implement menu item lookup"}

