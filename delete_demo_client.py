#!/usr/bin/env python3
"""Delete the demo client to allow recreation with proper defaults"""

import sys
sys.path.insert(0, '/home/user/sentinel')

from sqlalchemy import create_engine, text
from app.core.config import settings

def delete_demo_client():
    """Delete the demo client"""
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        result = conn.execute(text("DELETE FROM clients WHERE client_id = 'demo-client'"))
        conn.commit()
        print(f"\n✓ Deleted demo client (rows affected: {result.rowcount})")

if __name__ == "__main__":
    try:
        delete_demo_client()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
