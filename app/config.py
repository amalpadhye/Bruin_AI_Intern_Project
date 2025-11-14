"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Cal AI Configuration
    cal_ai_api_key: str
    cal_ai_base_url: str = "https://api.calai.app"
    
    # AWS Configuration
    aws_region: str = "us-west-2"
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    s3_bucket_raw: str
    s3_bucket_derived: str
    s3_bucket_media: str
    
    # Database Configuration
    database_url: str
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # API Configuration
    api_secret_key: str
    environment: str = "development"
    
    # UCLA API Configuration (optional)
    ucla_api_key: Optional[str] = None
    ucla_api_base_url: str = "https://api.ucla.edu/sis"
    
    # Cal AI Discrepancy Thresholds
    calorie_discrepancy_threshold: float = 0.15  # 15% difference triggers warning
    protein_discrepancy_threshold: float = 0.20  # 20% difference for protein
    confidence_threshold: float = 0.7  # Minimum confidence for Cal AI predictions
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

