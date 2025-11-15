"""Test S3 connection and upload."""
import sys
from app.services.s3_service import S3Service
from app.config import settings

def test_s3():
    """Test S3 connection and basic operations."""
    print("Testing S3 connection...")
    print(f"Region: {settings.aws_region}")
    print(f"Buckets: {settings.s3_bucket_raw}, {settings.s3_bucket_derived}, {settings.s3_bucket_media}")
    
    try:
        s3 = S3Service()
        
        # Test 1: Upload a test JSON file
        print("\n1. Testing JSON upload...")
        test_data = {"test": "data", "timestamp": "2025-01-01"}
        test_key = "test/connection_test.json"
        
        success = s3.upload_json(s3.bucket_raw, test_key, test_data)
        if success:
            print(f"✓ Upload successful: s3://{s3.bucket_raw}/{test_key}")
        else:
            print("✗ Upload failed")
            return False
        
        # Test 2: Download the file back
        print("\n2. Testing JSON download...")
        downloaded = s3.download_json(s3.bucket_raw, test_key)
        if downloaded and downloaded.get("test") == "data":
            print("✓ Download successful")
        else:
            print("✗ Download failed or data mismatch")
            return False
        
        # Test 3: Generate presigned URL
        print("\n3. Testing presigned URL generation...")
        presigned_url = s3.get_presigned_url(s3.bucket_raw, test_key, method="get")
        if presigned_url:
            print(f"✓ Presigned URL generated: {presigned_url[:50]}...")
        else:
            print("✗ Presigned URL generation failed")
            return False
        
        print("\n✓ All S3 tests passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ S3 test failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check AWS credentials in .env file")
        print("2. Verify bucket names exist in AWS")
        print("3. Check IAM user has S3 permissions")
        print("4. Verify AWS region is correct")
        return False

if __name__ == "__main__":
    success = test_s3()
    sys.exit(0 if success else 1)

