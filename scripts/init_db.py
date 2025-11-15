#!/usr/bin/env python
"""Database initialization script"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from app.models.database import Base
from app.core.config import settings
from app.core.security import generate_api_key


def init_database():
    """Initialize the database schema"""
    print("🗄️  Initializing database...")

    # Create engine
    engine = create_engine(settings.DATABASE_URL)

    # Create all tables
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("✅ Database initialized successfully!")
    print(f"📊 Tables created: {', '.join(Base.metadata.tables.keys())}")


def create_demo_client():
    """Create a demo client for testing"""
    from sqlalchemy.orm import Session
    from app.models.database import Client

    print("\n👤 Creating demo client...")

    engine = create_engine(settings.DATABASE_URL)
    session = Session(bind=engine)

    # Check if demo client already exists
    existing = session.query(Client).filter(Client.client_id == "demo_client").first()

    if existing:
        print(f"✅ Demo client already exists")
        print(f"   Client ID: {existing.client_id}")
        print(f"   API Key: {existing.api_key}")
        session.close()
        return

    # Generate API key
    api_key = generate_api_key()

    # Create demo client
    demo_client = Client(
        client_id="demo_client",
        company_name="Demo Financial Services",
        plan="starter",
        monthly_fee=100000,  # ₦100k
        status="active",
        api_key=api_key,
        api_rate_limit=10000,
        risk_threshold_high=70,
        risk_threshold_medium=40,
        enabled_rules=None,  # All rules enabled by default
        total_checks=0,
        total_fraud_caught=0,
        total_amount_saved=0,
        contact_name="Demo User",
        contact_email="demo@example.com",
        contact_phone="+234 800 000 0000"
    )

    session.add(demo_client)
    session.commit()

    print(f"✅ Demo client created successfully!")
    print(f"   Client ID: {demo_client.client_id}")
    print(f"   Company: {demo_client.company_name}")
    print(f"   API Key: {api_key}")
    print(f"\n📝 Save this API key - you'll need it to make API requests!")
    print(f"\n🧪 Test the API:")
    print(f'   curl -X POST http://localhost:8000/api/v1/check-transaction \\')
    print(f'     -H "Content-Type: application/json" \\')
    print(f'     -H "X-API-Key: {api_key}" \\')
    print(f'     -d \'{{"transaction_id": "test_001", "user_id": "user_001", "amount": 50000}}\'')

    session.close()


if __name__ == "__main__":
    import sys

    try:
        init_database()
        create_demo_client()
        print("\n🎉 Setup complete! You can now start the application.")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
