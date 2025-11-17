"""
Create all database tables using SQLAlchemy models

This script creates all the base tables needed for Sentinel:
- transactions
- clients
- consortium_intelligence
- rule_accuracy
- velocity_checks

Run this BEFORE running migrations.
"""

import sys
from sqlalchemy import create_engine
from app.models.database import Base
from app.core.config import settings

def create_tables():
    """Create all tables defined in SQLAlchemy models"""

    print("🔧 Creating Sentinel database tables...")
    print(f"📊 Database URL: {settings.DATABASE_URL}")

    try:
        # Create database engine
        engine = create_engine(settings.DATABASE_URL)

        # Create all tables
        Base.metadata.create_all(bind=engine)

        print("✅ Successfully created all database tables!")
        print("\nTables created:")
        print("  - transactions")
        print("  - clients")
        print("  - consortium_intelligence")
        print("  - rule_accuracy")
        print("  - velocity_checks")
        print("\n✨ Database is ready for use!")

    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_tables()
