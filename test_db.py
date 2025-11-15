"""Test database connection."""
import sys
from app.config import settings

try:
    import psycopg2
    print("Testing database connection...")
    print(f"Database URL: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")
    
    conn = psycopg2.connect(settings.database_url)
    print("✓ Database connection successful!")
    
    # Test query
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"PostgreSQL version: {version[0]}")
    
    cursor.close()
    conn.close()
    print("✓ Connection closed successfully")
    
except ImportError:
    print("✗ psycopg2 not installed. Run: pip install psycopg2-binary")
    sys.exit(1)
except Exception as e:
    print(f"✗ Database connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Postgres is running: brew services list")
    print("2. Check DATABASE_URL in .env file")
    print("3. Verify database exists: psql -l | grep forku")
    sys.exit(1)

