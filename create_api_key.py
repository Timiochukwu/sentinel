#!/usr/bin/env python3
"""Simple script to create an API key for testing"""

import secrets
import sys
from datetime import datetime
sys.path.insert(0, '/home/user/sentinel')

from sqlalchemy import create_engine, text
from app.core.config import settings

def generate_api_key():
    """Generate a secure random API key"""
    return secrets.token_urlsafe(32)

def create_test_client():
    """Create a test client with an API key"""
    engine = create_engine(settings.DATABASE_URL)

    api_key = generate_api_key()

    with engine.connect() as conn:
        # Check if a demo client already exists
        result = conn.execute(text("SELECT api_key FROM clients WHERE client_id = 'demo-client' LIMIT 1"))
        existing = result.fetchone()

        if existing:
            print(f"\n✓ Demo client already exists!")
            print(f"\nAPI Key: {existing[0]}")
            print(f"\nUse this API key in your requests:")
            print(f'  curl -X POST http://localhost:8000/api/v1/check-transaction \\')
            print(f'    -H "Content-Type: application/json" \\')
            print(f'    -H "X-API-Key: {existing[0]}" \\')
            print(f'    -d \'{{"transaction_id": "txn_001", "user_id": "user_001", "amount": 50000, "transaction_type": "loan_disbursement"}}\'')
            return

        # Create a new demo client
        insert_query = text("""
            INSERT INTO clients (
                client_id, company_name, contact_email, contact_phone,
                plan, status, api_key, api_rate_limit, webhook_url,
                risk_threshold_high, risk_threshold_medium,
                total_checks, total_fraud_caught, total_amount_saved,
                ml_enabled, ml_weight,
                created_at, updated_at
            ) VALUES (
                :client_id, :company_name, :contact_email, :contact_phone,
                :plan, :status, :api_key, :api_rate_limit, :webhook_url,
                :risk_threshold_high, :risk_threshold_medium,
                :total_checks, :total_fraud_caught, :total_amount_saved,
                :ml_enabled, :ml_weight,
                :created_at, :updated_at
            )
            RETURNING id, api_key
        """)

        now = datetime.utcnow()
        result = conn.execute(insert_query, {
            'client_id': 'demo-client',
            'company_name': 'Demo Company',
            'contact_email': 'demo@example.com',
            'contact_phone': '+234-800-000-0000',
            'plan': 'starter',
            'status': 'active',
            'api_key': api_key,
            'api_rate_limit': 10000,
            'webhook_url': 'https://example.com/webhook',
            'risk_threshold_high': 70,
            'risk_threshold_medium': 40,
            'total_checks': 0,
            'total_fraud_caught': 0,
            'total_amount_saved': 0,
            'ml_enabled': True,
            'ml_weight': 0.7,
            'created_at': now,
            'updated_at': now
        })

        row = result.fetchone()
        conn.commit()

        print(f"\n✓ Successfully created demo client (ID: {row[0]})")
        print(f"\nAPI Key: {row[1]}")
        print(f"\n⚠️  IMPORTANT: Save this API key! You'll need it for all API requests.")
        print(f"\nExample usage:")
        print(f'  curl -X POST http://localhost:8000/api/v1/check-transaction \\')
        print(f'    -H "Content-Type: application/json" \\')
        print(f'    -H "X-API-Key: {row[1]}" \\')
        print(f'    -d \'{{"transaction_id": "txn_001", "user_id": "user_001", "amount": 50000, "transaction_type": "loan_disbursement"}}\'')

if __name__ == "__main__":
    try:
        create_test_client()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
