#!/usr/bin/env python
"""Seed database with sample data for testing"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import random

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.models.database import Transaction
from app.core.config import settings


def seed_transactions():
    """Create sample transactions for testing"""
    print("🌱 Seeding sample transactions...")

    engine = create_engine(settings.DATABASE_URL)
    session = Session(bind=engine)

    # Sample transaction data
    sample_transactions = [
        # Legitimate transactions
        {
            "transaction_id": "txn_001",
            "user_id": "user_001",
            "amount": 50000,
            "risk_score": 15,
            "risk_level": "low",
            "decision": "approve",
            "is_fraud": False
        },
        {
            "transaction_id": "txn_002",
            "user_id": "user_002",
            "amount": 75000,
            "risk_score": 20,
            "risk_level": "low",
            "decision": "approve",
            "is_fraud": False
        },
        # Medium risk
        {
            "transaction_id": "txn_003",
            "user_id": "user_003",
            "amount": 150000,
            "risk_score": 55,
            "risk_level": "medium",
            "decision": "review",
            "is_fraud": False
        },
        # High risk / fraud
        {
            "transaction_id": "txn_004",
            "user_id": "user_004",
            "amount": 250000,
            "risk_score": 85,
            "risk_level": "high",
            "decision": "decline",
            "is_fraud": True,
            "fraud_type": "loan_stacking"
        },
        {
            "transaction_id": "txn_005",
            "user_id": "user_005",
            "amount": 300000,
            "risk_score": 92,
            "risk_level": "high",
            "decision": "decline",
            "is_fraud": True,
            "fraud_type": "sim_swap"
        },
    ]

    created_count = 0

    for txn_data in sample_transactions:
        # Check if transaction already exists
        existing = session.query(Transaction).filter(
            Transaction.transaction_id == txn_data["transaction_id"]
        ).first()

        if existing:
            continue

        # Create transaction
        transaction = Transaction(
            client_id="demo_client",
            transaction_type="loan_disbursement",
            ip_address="197.210.226.45",
            account_age_days=random.randint(1, 365),
            transaction_count=random.randint(0, 10),
            flags=[],
            processing_time_ms=random.randint(50, 150),
            created_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            **txn_data
        )

        session.add(transaction)
        created_count += 1

    session.commit()
    session.close()

    print(f"✅ Created {created_count} sample transactions")


if __name__ == "__main__":
    try:
        seed_transactions()
        print("🎉 Seeding complete!")
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
