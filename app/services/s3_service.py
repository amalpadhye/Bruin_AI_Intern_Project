"""S3 service for storing raw and derived data."""
import boto3
import json
import logging
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from app.config import settings

logger = logging.getLogger(__name__)


class S3Service:
    """Service for interacting with AWS S3 buckets."""
    
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key
        )
        self.bucket_raw = settings.s3_bucket_raw
        self.bucket_derived = settings.s3_bucket_derived
        self.bucket_media = settings.s3_bucket_media
    
    def upload_json(
        self,
        bucket: str,
        key: str,
        data: Dict[str, Any],
        content_type: str = "application/json"
    ) -> bool:
        """
        Upload JSON data to S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (path)
            data: Dictionary to upload as JSON
            content_type: Content type for the object
            
        Returns:
            True if successful, False otherwise
        """
        try:
            json_data = json.dumps(data, indent=2, default=str)
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json_data.encode('utf-8'),
                ContentType=content_type
            )
            logger.info(f"Uploaded JSON to s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading to S3: {e}")
            return False
    
    def upload_bytes(
        self,
        bucket: str,
        key: str,
        data: bytes,
        content_type: str
    ) -> bool:
        """
        Upload raw bytes to S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (path)
            data: Bytes to upload
            content_type: Content type (e.g., 'image/jpeg')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=data,
                ContentType=content_type
            )
            logger.info(f"Uploaded bytes to s3://{bucket}/{key}")
            return True
        except ClientError as e:
            logger.error(f"Error uploading to S3: {e}")
            return False
    
    def get_presigned_url(
        self,
        bucket: str,
        key: str,
        expiration: int = 3600,
        method: str = "put"
    ) -> Optional[str]:
        """
        Generate a presigned URL for S3 operations.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (path)
            expiration: URL expiration time in seconds (default 1 hour)
            method: HTTP method ('put' or 'get')
            
        Returns:
            Presigned URL or None if error
        """
        try:
            if method.lower() == "put":
                operation = 'put_object'
            else:
                operation = 'get_object'
            
            url = self.s3_client.generate_presigned_url(
                operation,
                Params={'Bucket': bucket, 'Key': key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
    
    def download_json(self, bucket: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Download and parse JSON from S3.
        
        Args:
            bucket: S3 bucket name
            key: S3 object key (path)
            
        Returns:
            Parsed JSON dictionary or None if error
        """
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response['Body'].read().decode('utf-8')
            return json.loads(content)
        except ClientError as e:
            logger.error(f"Error downloading from S3: {e}")
            return None
    
    def upload_raw_menu(self, date_str: str, menu_data: Dict[str, Any]) -> str:
        """
        Upload raw menu data to S3.
        
        Args:
            date_str: Date in YYYY-MM-DD format
            menu_data: Menu data dictionary
            
        Returns:
            S3 key of uploaded file
        """
        key = f"raw/menus/{date_str}/menu.json"
        self.upload_json(self.bucket_raw, key, menu_data)
        return key
    
    def upload_scan_image(
        self,
        user_id: str,
        image_bytes: bytes,
        image_id: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload scan image to S3.
        
        Args:
            user_id: User UUID
            image_bytes: Image file bytes
            image_id: Unique image identifier (UUID)
            content_type: Image MIME type
            
        Returns:
            S3 key of uploaded file
        """
        key = f"raw/scans/{user_id}/{image_id}.jpg"
        self.upload_bytes(self.bucket_raw, key, image_bytes, content_type)
        return key
    
    def upload_cal_ai_result(
        self,
        user_id: str,
        scan_id: str,
        cal_ai_response: Dict[str, Any]
    ) -> str:
        """
        Upload Cal AI analysis result to S3.
        
        Args:
            user_id: User UUID
            scan_id: Scan identifier (UUID)
            cal_ai_response: Cal AI API response
            
        Returns:
            S3 key of uploaded file
        """
        key = f"derived/cal_ai/{user_id}/{scan_id}.json"
        self.upload_json(self.bucket_derived, key, cal_ai_response)
        return key

