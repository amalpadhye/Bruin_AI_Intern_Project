"""Upload endpoints for presigned S3 URLs."""
from fastapi import APIRouter, Query, HTTPException, Depends
from typing import Optional
from app.services.s3_service import S3Service
import uuid

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.get("/presign")
async def get_presigned_url(
    contentType: str = Query(..., description="Content type (e.g., image/jpeg)"),
    s3_service: S3Service = Depends(lambda: S3Service())
):
    """
    Generate a presigned URL for uploading an image to S3.
    
    Args:
        contentType: MIME type of the file to upload
        
    Returns:
        Dictionary with S3 key and presigned PUT URL
    """
    try:
        # Generate a unique key
        # In production, user_id would come from JWT token
        user_id = "temp_user"  # TODO: Extract from auth token
        file_id = str(uuid.uuid4())
        
        # Determine bucket based on content type
        if contentType.startswith("image/"):
            bucket = s3_service.bucket_raw
            key = f"raw/scans/{user_id}/{file_id}.jpg"
        else:
            bucket = s3_service.bucket_media
            key = f"media/uploads/{user_id}/{file_id}"
        
        # Generate presigned URL
        put_url = s3_service.get_presigned_url(
            bucket=bucket,
            key=key,
            expiration=3600,  # 1 hour
            method="put"
        )
        
        if not put_url:
            raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
        
        return {
            "key": key,
            "putUrl": put_url,
            "bucket": bucket
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating presigned URL: {str(e)}")

