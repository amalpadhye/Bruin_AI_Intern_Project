"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI/ChatGPT Configuration
    openai_api_key: Optional[str] = None
    
    # Cal AI Configuration (optional - can be added later)
    cal_ai_api_key: Optional[str] = None
    cal_ai_base_url: str = "https://api.calai.app"
    
    # AWS Configuration
    # Use us-east-2 (Ohio) or us-west-2 (Oregon) - both work fine from CA
    # Important: Use the SAME region for all AWS resources (S3, ECS, etc.)
    aws_region: str = "us-east-2"  # Using us-east-2 (Ohio)
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
        extra = "ignore"  # Ignore extra fields in .env that aren't in this class


settings = Settings()

