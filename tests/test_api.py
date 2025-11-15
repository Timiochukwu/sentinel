"""Test API endpoints"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert data["status"] == "running"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data
    assert "database" in data
    assert "redis" in data


def test_check_transaction_without_api_key():
    """Test fraud detection endpoint without API key"""
    response = client.post(
        "/api/v1/check-transaction",
        json={
            "transaction_id": "test_001",
            "user_id": "user_001",
            "amount": 50000
        }
    )
    assert response.status_code == 401
    assert "API key missing" in response.json()["detail"]


def test_check_transaction_with_invalid_api_key():
    """Test fraud detection endpoint with invalid API key"""
    response = client.post(
        "/api/v1/check-transaction",
        json={
            "transaction_id": "test_001",
            "user_id": "user_001",
            "amount": 50000
        },
        headers={"X-API-Key": "invalid_key"}
    )
    assert response.status_code == 401
    assert "Invalid API key" in response.json()["detail"]


# Note: To test with valid API key, you'd need to:
# 1. Set up test database
# 2. Create test client with known API key
# 3. Run integration tests

# Example integration test (commented out):
"""
@pytest.fixture
def test_api_key(db_session):
    # Create test client
    from app.models.database import Client
    from app.core.security import generate_api_key

    api_key = generate_api_key()
    client = Client(
        client_id="test_client",
        company_name="Test Company",
        api_key=api_key,
        status="active"
    )
    db_session.add(client)
    db_session.commit()

    return api_key


def test_check_transaction_success(test_api_key):
    response = client.post(
        "/api/v1/check-transaction",
        json={
            "transaction_id": "test_001",
            "user_id": "user_001",
            "amount": 50000,
            "transaction_type": "loan_disbursement"
        },
        headers={"X-API-Key": test_api_key}
    )
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert "decision" in data
    assert "flags" in data
"""
