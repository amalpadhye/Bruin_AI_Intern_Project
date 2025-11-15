"""Test database connection."""
import sys
from app.config import settings

try:
    from sqlalchemy import create_engine, text
    from app.db.database import engine
    print("Testing database connection...")
    print(f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    
    conn = engine.connect()
    print("✓ Database connection successful!")
    
    # Test query
    result = conn.execute(text("SELECT version();"))
    version = result.fetchone()
    print(f"PostgreSQL version: {version[0]}")
    
    conn.close()
    print("✓ Connection closed successfully")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    print("Make sure virtual environment is activated and dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Postgres is running: brew services list")
    print("2. Check DATABASE_URL in .env file")
    print("3. Verify database exists: psql -l | grep forku")
    sys.exit(1)

