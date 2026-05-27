import sys
import os

# Add backend to path so we can import from app
sys.path.append(os.path.abspath("backend"))

from app.schemas.job import JobCreateRequest
from app.config.settings import Settings
from pydantic import ValidationError

print("--- TIGR-TAS MOCK VERIFICATION SCRIPT ---\n")

print("1. Testing Settings Validation...")
try:
    # Set fake env vars for validation
    os.environ["APP_NAME"] = "TIGR-Tas"
    os.environ["APP_VERSION"] = "1.0.0"
    os.environ["APP_ENV"] = "development"
    os.environ["DEBUG"] = "true"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["HOST"] = "0.0.0.0"
    os.environ["PORT"] = "8000"
    os.environ["POSTGRES_HOST"] = "db"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["POSTGRES_DB"] = "tigr_tas"
    os.environ["POSTGRES_USER"] = "user"
    os.environ["POSTGRES_PASSWORD"] = "pass"
    os.environ["REDIS_HOST"] = "redis"
    os.environ["REDIS_PORT"] = "6379"
    os.environ["REDIS_PASSWORD"] = "pass"
    os.environ["UPLOAD_DIR"] = "/tmp/uploads"
    os.environ["JWT_SECRET_KEY"] = "secret"
    
    settings = Settings()
    print("✅ Settings model validated successfully!")
    print(f"Computed Database URL: {settings.database_url}")
except Exception as e:
    print(f"❌ Settings validation failed: {e}")

print("\n2. Testing JobCreateRequest Schema Validation...")
try:
    job = JobCreateRequest(
        job_type="guide_scan",
        input_data={"sequence": "ATCGATCG"},
        priority=3
    )
    print("✅ JobCreateRequest validated successfully!")
    print(f"Parsed Job: {job.model_dump()}")
except ValidationError as e:
    print(f"❌ Schema validation failed: {e}")

print("\n3. Testing JobCreateRequest Rejection (Invalid Priority)...")
try:
    job = JobCreateRequest(
        job_type="guide_scan",
        input_data={"sequence": "ATCGATCG"},
        priority=15  # Should fail, max is 10
    )
    print("❌ Schema failed to reject invalid priority!")
except ValidationError as e:
    print("✅ Schema correctly rejected priority > 10!")

print("\n--- VERIFICATION COMPLETE ---")
