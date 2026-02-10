"""
S3 Storage Configuration Verification Script
Checks if S3 is properly configured and accessible
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings
from app.utils.s3_storage import get_s3_storage


def verify_s3_configuration():
    """Verify S3 configuration and connectivity"""
    print("=" * 60)
    print("S3 Storage Configuration Verification")
    print("=" * 60)
    print()
    
    # Check configuration settings
    print("📋 Configuration Settings:")
    print(f"   USE_S3_STORAGE: {settings.USE_S3_STORAGE}")
    print(f"   USE_SUPABASE_STORAGE: {settings.USE_SUPABASE_STORAGE}")
    print(f"   S3_BUCKET_NAME: {settings.S3_BUCKET_NAME}")
    print(f"   AWS_REGION: {settings.AWS_REGION}")
    print()
    
    # Check if S3 is enabled
    if not settings.USE_S3_STORAGE:
        print("❌ S3 Storage is DISABLED")
        print("   Set USE_S3_STORAGE=True in .env file")
        return False
    
    print("✅ S3 Storage is ENABLED")
    print()
    
    # Check bucket name
    if not settings.S3_BUCKET_NAME:
        print("❌ S3_BUCKET_NAME is not configured")
        print("   Set S3_BUCKET_NAME in .env file")
        return False
    
    print(f"✅ S3 Bucket configured: {settings.S3_BUCKET_NAME}")
    print()
    
    # Initialize S3 client
    print("🔧 Initializing S3 client...")
    s3_storage = get_s3_storage()
    
    if not s3_storage.is_enabled():
        print("❌ S3 client initialization FAILED")
        print("   Check:")
        print("   1. S3 bucket exists in AWS")
        print("   2. IAM role is attached to EC2 instance")
        print("   3. IAM role has S3 permissions")
        print("   4. Bucket is in the correct region")
        return False
    
    print("✅ S3 client initialized successfully")
    print()
    
    # Test bucket access
    print("🧪 Testing bucket access...")
    try:
        # Try to list files (this verifies permissions)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success, message, files = loop.run_until_complete(
            s3_storage.list_files(prefix="")
        )
        
        if success:
            print(f"✅ Bucket access successful")
            print(f"   Found {len(files)} file(s) in bucket")
        else:
            print(f"❌ Bucket access failed: {message}")
            return False
    except Exception as e:
        print(f"❌ Error accessing bucket: {e}")
        return False
    
    print()
    print("=" * 60)
    print("✅ S3 CONFIGURATION IS VALID AND WORKING!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Restart your FastAPI server")
    print("2. Restart Celery workers")
    print("3. Test file conversion with: POST /api/convert")
    print()
    
    return True


if __name__ == "__main__":
    try:
        success = verify_s3_configuration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
