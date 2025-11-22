# 📚 SENTINEL API ENDPOINTS - COMPLETE REFERENCE

**Last Updated:** 2025-01-22
**Total Endpoints:** 13
**API Version:** v1
**Base URL:** `http://localhost:8000`

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [Health & Status Endpoints](#health--status-endpoints)
4. [Fraud Detection Endpoints](#fraud-detection-endpoints)
5. [Dashboard Endpoints](#dashboard-endpoints)
6. [Consortium Intelligence Endpoints](#consortium-intelligence-endpoints)
7. [Feedback Endpoints](#feedback-endpoints)
8. [Error Handling](#error-handling)
9. [Response Codes](#response-codes)
10. [Rate Limiting](#rate-limiting)

---

## Quick Start

### Installation
```bash
# Clone repository
git clone <repository-url>
cd sentinel

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env

# Start services
docker-compose up -d

# Run application
uvicorn app.main:app --reload --port 8000
```

### First API Call
```bash
# Get API status
curl -X GET http://localhost:8000/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "redis": "connected",
#   "timestamp": "2024-01-22T10:30:00Z"
# }
```

---

## Authentication

### API Key Authentication

All endpoints (except `/` and `/health`) require API key authentication.

**Header:** `X-API-Key: your_api_key_here`

**Example:**
```bash
curl -X GET http://localhost:8000/api/v1/dashboard/stats \
  -H "X-API-Key: your-sentinel-api-key"
```

### Getting an API Key

1. Sign up at `/admin/signup`
2. Navigate to Settings → API Keys
3. Click "Generate New Key"
4. Copy and store securely (shown only once)

### API Key Formats

```
Live Key:    your-sentinel-live-api-key-here
Test Key:    your-sentinel-test-api-key-here
```

---

## Health & Status Endpoints

### 1. Health Check

Verify API and dependency health status.

**Endpoint:** `GET /health`

**Authentication:** None (public endpoint)

**Query Parameters:** None

**Response Schema:**
```json
{
  "status": "healthy|unhealthy",
  "database": "connected|disconnected",
  "redis": "connected|disconnected|degraded",
  "timestamp": "2024-01-22T10:30:00Z",
  "uptime_seconds": 3600,
  "version": "1.0.0"
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/health

# Response (200 OK):
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2024-01-22T10:30:00Z",
  "uptime_seconds": 3600,
  "version": "1.0.0"
}
```

**Status Codes:**
- `200 OK` - All systems healthy
- `503 Service Unavailable` - One or more dependencies down

---

### 2. API Information

Get API metadata and documentation links.

**Endpoint:** `GET /`

**Authentication:** None (public endpoint)

**Query Parameters:** None

**Response Schema:**
```json
{
  "name": "SENTINEL Fraud Detection API",
  "version": "1.0.0",
  "status": "operational",
  "environment": "production|development",
  "documentation": "http://localhost:8000/docs",
  "description": "Advanced multi-vertical fraud detection system",
  "endpoints": {
    "fraud_detection": "/api/v1",
    "dashboard": "/api/v1/dashboard",
    "consortium": "/api/v1/consortium",
    "feedback": "/api/v1/feedback"
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/

# Response (200 OK):
{
  "name": "SENTINEL Fraud Detection API",
  "version": "1.0.0",
  "status": "operational",
  "environment": "production",
  "documentation": "http://localhost:8000/docs",
  "description": "Advanced multi-vertical fraud detection system",
  "endpoints": {
    "fraud_detection": "/api/v1",
    "dashboard": "/api/v1/dashboard",
    "consortium": "/api/v1/consortium",
    "feedback": "/api/v1/feedback"
  }
}
```

---

## Fraud Detection Endpoints

Core fraud detection endpoints for transaction analysis.

### 3. Check Transaction for Fraud

Main fraud detection endpoint. Analyzes a transaction and returns fraud risk assessment.

**Endpoint:** `POST /api/v1/check-transaction`

**Authentication:** Required (`X-API-Key` header)

**Request Body Schema:**
```json
{
  "transaction_id": "TXN20240122001",
  "user_id": "USR12345",
  "amount": 50000.00,
  "currency": "NGN",
  "transaction_type": "transfer",
  "merchant_id": "MER98765",
  "device_id": "device_abc123",
  "ip_address": "192.168.1.100",
  "account_age_days": 30,
  "transaction_count": 5,
  "phone_changed_recently": false,
  "shipping_address": "Lagos, Nigeria",
  "user_country": "NG",
  "vertical": "payments"
}
```

**Field Descriptions:**
- `transaction_id` (string, required): Unique transaction identifier
- `user_id` (string, required): User/customer identifier
- `amount` (float, required): Transaction amount
- `currency` (string, required): Currency code (NGN, USD, EUR, etc.)
- `transaction_type` (string, required): Type of transaction (transfer, purchase, withdrawal, etc.)
- `merchant_id` (string, optional): Merchant/destination identifier
- `device_id` (string, optional): Device identifier for fingerprinting
- `ip_address` (string, optional): Client IP address
- `account_age_days` (int, optional): Days since account creation
- `transaction_count` (int, optional): Number of transactions by user
- `phone_changed_recently` (boolean, optional): Whether phone changed in last 48 hours
- `shipping_address` (string, optional): Shipping address for ecommerce
- `user_country` (string, optional): User's country code
- `vertical` (string, optional): Industry vertical (payments, crypto, lending, ecommerce, etc.)

**Response Schema:**
```json
{
  "transaction_id": "TXN20240122001",
  "fraud_score": 65.5,
  "fraud_level": "medium",
  "decision": "review",
  "is_fraudulent": false,
  "confidence": 0.87,
  "rules_triggered": [
    {
      "rule_id": 45,
      "rule_name": "VelocityCheckRule",
      "severity": "medium",
      "fraud_score_contribution": 15.5,
      "description": "High transaction velocity detected"
    },
    {
      "rule_id": 12,
      "rule_name": "DisposableEmailRule",
      "severity": "low",
      "fraud_score_contribution": 10.0,
      "description": "Disposable email address detected"
    }
  ],
  "recommendations": [
    "Require additional authentication",
    "Check shipping address",
    "Monitor account activity"
  ],
  "processing_time_ms": 87,
  "timestamp": "2024-01-22T10:30:00Z"
}
```

**Field Descriptions:**
- `transaction_id`: Echo of input transaction ID
- `fraud_score`: Numerical score (0-100) indicating fraud probability
- `fraud_level`: Category (low: 0-33, medium: 34-66, high: 67-100)
- `decision`: Recommended action (approve, review, decline)
- `is_fraudulent`: Boolean fraud determination
- `confidence`: Confidence level (0-1) of the assessment
- `rules_triggered`: List of fraud rules that detected issues
- `recommendations`: Suggested actions for the transaction
- `processing_time_ms`: API response time in milliseconds
- `timestamp`: Server timestamp of response

**Fraud Level Mapping:**
```
Score 0-33:   LOW      - Approve with minimal checks
Score 34-66:  MEDIUM   - Review or require additional auth
Score 67-100: HIGH     - Decline or escalate to manual review
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-sentinel-api-key" \
  -d '{
    "transaction_id": "TXN20240122001",
    "user_id": "USR12345",
    "amount": 50000.00,
    "currency": "NGN",
    "transaction_type": "transfer",
    "merchant_id": "MER98765",
    "device_id": "device_abc123",
    "ip_address": "192.168.1.100",
    "account_age_days": 30,
    "transaction_count": 5,
    "user_country": "NG",
    "vertical": "payments"
  }'
```

**Example Response:**
```json
{
  "transaction_id": "TXN20240122001",
  "fraud_score": 45.2,
  "fraud_level": "low",
  "decision": "approve",
  "is_fraudulent": false,
  "confidence": 0.92,
  "rules_triggered": [],
  "recommendations": [],
  "processing_time_ms": 87,
  "timestamp": "2024-01-22T10:30:00Z"
}
```

**Performance:**
- Average response time: 80-100ms
- With caching (5-minute TTL): 5-10ms
- Concurrent requests: Up to 1,000 req/s

**Status Codes:**
- `200 OK` - Successfully processed
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Invalid or missing API key
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

### 4. Get Transaction Details

Retrieve previously processed transaction fraud assessment.

**Endpoint:** `GET /api/v1/transaction/{transaction_id}`

**Authentication:** Required (`X-API-Key` header)

**Path Parameters:**
- `transaction_id` (string, required): The transaction ID to retrieve

**Query Parameters:** None

**Response Schema:** Same as Check Transaction endpoint

**Example:**
```bash
curl -X GET http://localhost:8000/api/v1/transaction/TXN20240122001 \
  -H "X-API-Key: your-sentinel-api-key"
```

**Status Codes:**
- `200 OK` - Transaction found
- `404 Not Found` - Transaction not found
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Server error

---

### 5. Batch Transaction Check

Bulk fraud checking for multiple transactions.

**Endpoint:** `POST /api/v1/check-transactions-batch`

**Authentication:** Required (`X-API-Key` header)

**Request Body Schema:**
```json
{
  "transactions": [
    {
      "transaction_id": "TXN20240122001",
      "user_id": "USR12345",
      "amount": 50000.00,
      "currency": "NGN",
      "transaction_type": "transfer",
      "device_id": "device_abc123",
      "ip_address": "192.168.1.100",
      "user_country": "NG",
      "vertical": "payments"
    },
    {
      "transaction_id": "TXN20240122002",
      "user_id": "USR12346",
      "amount": 25000.00,
      "currency": "NGN",
      "transaction_type": "purchase",
      "device_id": "device_def456",
      "ip_address": "192.168.1.101",
      "user_country": "NG",
      "vertical": "ecommerce"
    }
  ]
}
```

**Constraints:**
- Minimum: 1 transaction
- Maximum: 100 transactions per request
- Exceeding limits returns `400 Bad Request`

**Response Schema:**
```json
{
  "results": [
    {
      "transaction_id": "TXN20240122001",
      "fraud_score": 45.2,
      "fraud_level": "low",
      "decision": "approve",
      "is_fraudulent": false,
      "confidence": 0.92,
      "rules_triggered": [],
      "timestamp": "2024-01-22T10:30:00Z"
    },
    {
      "transaction_id": "TXN20240122002",
      "fraud_score": 72.5,
      "fraud_level": "high",
      "decision": "decline",
      "is_fraudulent": true,
      "confidence": 0.88,
      "rules_triggered": [
        {
          "rule_id": 10,
          "rule_name": "ImpossibleTravelRule",
          "severity": "critical",
          "fraud_score_contribution": 50.0
        }
      ],
      "timestamp": "2024-01-22T10:30:05Z"
    }
  ],
  "summary": {
    "total": 2,
    "processed": 2,
    "errors": 0,
    "high_risk": 1,
    "medium_risk": 0,
    "low_risk": 1,
    "total_processing_time_ms": 150,
    "average_time_per_transaction_ms": 75.0
  }
}
```

**Example Request:**
```bash
curl -X POST http://localhost:8000/api/v1/check-transactions-batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-sentinel-api-key" \
  -d '{
    "transactions": [
      {
        "transaction_id": "TXN20240122001",
        "user_id": "USR12345",
        "amount": 50000.00,
        "currency": "NGN",
        "transaction_type": "transfer",
        "user_country": "NG",
        "vertical": "payments"
      },
      {
        "transaction_id": "TXN20240122002",
        "user_id": "USR12346",
        "amount": 25000.00,
        "currency": "NGN",
        "transaction_type": "purchase",
        "user_country": "NG",
        "vertical": "ecommerce"
      }
    ]
  }'
```

**Performance:**
- 100 transactions: ~3 seconds (vs ~150 seconds sequentially)
- 50x faster than sequential API calls
- Ideal for batch processing and reconciliation

**Status Codes:**
- `200 OK` - Successfully processed
- `400 Bad Request` - Invalid input or too many transactions
- `401 Unauthorized` - Invalid API key
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Dashboard Endpoints

Analytics and monitoring endpoints for fraud statistics and transaction history.

### 6. Get Dashboard Statistics

Comprehensive fraud statistics for dashboard display.

**Endpoint:** `GET /api/v1/dashboard/stats`

**Authentication:** Required (`X-API-Key` header)

**Query Parameters:** None

**Response Schema:**
```json
{
  "today": {
    "total_transactions": 150,
    "high_risk_count": 5,
    "medium_risk_count": 12,
    "low_risk_count": 133,
    "fraud_prevented_amount": 2500000.00,
    "false_positive_rate": 0.03
  },
  "month": {
    "total_transactions": 4500,
    "fraud_caught_count": 120,
    "fraud_prevented_amount": 85000000.00,
    "accuracy": 0.94,
    "false_positive_rate": 0.025,
    "precision": 0.91,
    "recall": 0.87
  },
  "risk_distribution": {
    "low": 85,
    "medium": 12,
    "high": 3
  },
  "fraud_types": {
    "loan_stacking": 15,
    "sim_swap": 3,
    "identity_fraud": 28,
    "device_sharing": 12,
    "card_fraud": 35,
    "account_takeover": 8,
    "bot_activity": 19
  },
  "top_fraud_rules": [
    {
      "rule_name": "ImpossibleTravelRule",
      "triggers_count": 35,
      "accuracy": 0.92
    },
    {
      "rule_name": "VelocityCheckRule",
      "triggers_count": 28,
      "accuracy": 0.88
    }
  ]
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/api/v1/dashboard/stats \
  -H "X-API-Key: your-sentinel-api-key"
```

**Status Codes:**
- `200 OK` - Statistics retrieved
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Server error

---

### 7. Get Transaction History

Advanced transaction search and filtering.

**Endpoint:** `GET /api/v1/dashboard/transactions`

**Authentication:** Required (`X-API-Key` header)

**Query Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `risk_level` | string | - | low, medium, high | Filter by single risk level |
| `risk_levels` | string | - | comma-separated | Filter by multiple risk levels (e.g., `low,high`) |
| `decision` | string | - | approve, review, decline | Filter by single decision |
| `decisions` | string | - | comma-separated | Filter by multiple decisions |
| `outcome` | string | - | fraud, legitimate, pending | Filter by outcome |
| `start_date` | string | - | ISO 8601 | Start date (e.g., 2024-01-01) |
| `end_date` | string | - | ISO 8601 | End date (e.g., 2024-12-31) |
| `min_amount` | float | 0 | ≥ 0 | Minimum transaction amount |
| `max_amount` | float | ∞ | ≥ 0 | Maximum transaction amount |
| `search` | string | - | - | Search by transaction_id or user_id |
| `limit` | int | 50 | 1-100 | Results per page |
| `offset` | int | 0 | ≥ 0 | Pagination offset |

**Response Schema:**
```json
{
  "transactions": [
    {
      "transaction_id": "TXN20240122001",
      "user_id": "USR12345",
      "amount": 50000.00,
      "currency": "NGN",
      "fraud_score": 45.2,
      "risk_level": "low",
      "decision": "approve",
      "outcome": "legitimate",
      "created_at": "2024-01-22T10:30:00Z",
      "rules_triggered_count": 0
    }
  ],
  "total": 1500,
  "offset": 0,
  "limit": 50,
  "pages": 30
}
```

**Examples:**

Filter by high-risk transactions:
```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/transactions?risk_level=high" \
  -H "X-API-Key: your-sentinel-api-key"
```

Search with date range and amount filter:
```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/transactions?start_date=2024-01-01&end_date=2024-01-22&min_amount=100000&max_amount=5000000" \
  -H "X-API-Key: your-sentinel-api-key"
```

Pagination example:
```bash
curl -X GET "http://localhost:8000/api/v1/dashboard/transactions?limit=25&offset=50" \
  -H "X-API-Key: your-sentinel-api-key"
```

**Status Codes:**
- `200 OK` - Transactions retrieved
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Server error

---

### 8. Get Client Information

Retrieve authenticated client account details.

**Endpoint:** `GET /api/v1/dashboard/client-info`

**Authentication:** Required (`X-API-Key` header)

**Query Parameters:** None

**Response Schema:**
```json
{
  "client_id": "CLI_abc123xyz",
  "company_name": "Acme Financial",
  "email": "contact@acmefinancial.com",
  "plan": "enterprise",
  "status": "active",
  "subscription_start": "2023-06-01",
  "subscription_end": "2025-06-01",
  "api_keys_count": 3,
  "total_checks_lifetime": 5000000,
  "total_fraud_caught": 12500,
  "total_amount_saved": 250000000.00,
  "monthly_quota": null,
  "monthly_usage": 85000,
  "usage_percentage": 42.5
}
```

**Plans:**
- `starter`: 50K transactions/month
- `growth`: 200K transactions/month
- `enterprise`: Unlimited transactions

**Example:**
```bash
curl -X GET http://localhost:8000/api/v1/dashboard/client-info \
  -H "X-API-Key: your-sentinel-api-key"
```

**Status Codes:**
- `200 OK` - Client info retrieved
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Server error

---

### 9. Get Rule Accuracy Metrics

View accuracy statistics for each fraud detection rule.

**Endpoint:** `GET /api/v1/dashboard/rule-accuracy`

**Authentication:** Required (`X-API-Key` header)

**Query Parameters:** None

**Response Schema:**
```json
{
  "rules": [
    {
      "rule_id": 10,
      "rule_name": "ImpossibleTravelRule",
      "category": "behavioral",
      "severity": "critical",
      "triggered_count": 450,
      "true_positives": 412,
      "false_positives": 38,
      "accuracy": 0.92,
      "precision": 0.92,
      "recall": 0.87,
      "f1_score": 0.89,
      "current_weight": 1.0,
      "fraud_score_contribution": 95
    },
    {
      "rule_id": 45,
      "rule_name": "VelocityCheckRule",
      "category": "behavioral",
      "severity": "medium",
      "triggered_count": 380,
      "true_positives": 335,
      "false_positives": 45,
      "accuracy": 0.88,
      "precision": 0.88,
      "recall": 0.85,
      "f1_score": 0.86,
      "current_weight": 0.95,
      "fraud_score_contribution": 60
    }
  ],
  "total_rules": 269,
  "average_accuracy": 0.86,
  "time_period": "30_days"
}
```

**Metric Definitions:**
- `accuracy`: (TP + TN) / (TP + TN + FP + FN)
- `precision`: TP / (TP + FP)
- `recall`: TP / (TP + FN)
- `f1_score`: 2 * (precision * recall) / (precision + recall)

**Example:**
```bash
curl -X GET http://localhost:8000/api/v1/dashboard/rule-accuracy \
  -H "X-API-Key: your-sentinel-api-key"
```

**Status Codes:**
- `200 OK` - Metrics retrieved
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Server error

---

## Consortium Intelligence Endpoints

Cross-lender fraud detection through consortium network.

### 10. Get Consortium Statistics

Overview of consortium fraud detection coverage.

**Endpoint:** `GET /api/v1/consortium/stats`

**Authentication:** Required (`X-API-Key` header)

**Query Parameters:** None

**Response Schema:**
```json
{
  "total_member_institutions": 145,
  "total_fraud_cases_shared": 12500,
  "loan_stacking_detected": 3200,
  "account_takeover_detected": 1850,
  "identity_fraud_detected": 4300,
  "total_amount_protected": 5000000000.00,
  "this_week": {
    "new_alerts": 250,
    "institutions_involved": 42,
    "total_applications": 15000,
    "fraud_cases_detected": 42,
    "amount_protected": 125000000.00
  },
  "this_month": {
    "new_alerts": 1200,
    "institutions_involved": 98,
    "total_applications": 65000,
    "fraud_cases_detected": 185,
    "amount_protected": 580000000.00
  }
}
```

**Example:**
```bash
curl -X GET http://localhost:8000/api/v1/consortium/stats \
  -H "X-API-Key: your-sentinel-api-key"
```

**Status Codes:**
- `200 OK` - Statistics retrieved
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Server error

---

### 11. Get Consortium Alerts

Recent cross-lender fraud alerts.

**Endpoint:** `GET /api/v1/consortium/alerts`

**Authentication:** Required (`X-API-Key` header)

**Query Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `limit` | int | 10 | 1-50 | Number of alerts to return |
| `severity` | string | - | critical, high, medium | Filter by severity |
| `days` | int | 7 | 1-90 | Number of days to retrieve |

**Response Schema:**
```json
{
  "alerts": [
    {
      "alert_id": "ALR_001",
      "transaction_id": "TXN20240122001",
      "type": "loan_stacking",
      "message": "User applied to 3 lenders within 48 hours",
      "institutions_involved": 3,
      "severity": "high",
      "created_at": "2024-01-22T08:15:00Z",
      "risk_score": 85,
      "fraud_amount": 500000.00,
      "identifiers": {
        "user_id": "USR12345",
        "phone": "+234XXXXXXXXXX",
        "email": "user@example.com",
        "bvn": "XXXXXXXXXXXX"
      }
    },
    {
      "alert_id": "ALR_002",
      "transaction_id": "TXN20240122002",
      "type": "sim_swap",
      "message": "Phone changed across lenders within 24 hours",
      "institutions_involved": 2,
      "severity": "critical",
      "created_at": "2024-01-22T10:30:00Z",
      "risk_score": 95,
      "fraud_amount": 250000.00,
      "identifiers": {
        "user_id": "USR12346",
        "phone": "+234XXXXXXXXXX",
        "email": "user2@example.com",
        "bvn": "XXXXXXXXXXXX"
      }
    }
  ],
  "total": 25,
  "new_today": 3
}
```

**Alert Types:**
- `loan_stacking`: Multiple loan applications to different lenders
- `sim_swap`: Phone number changed across lenders
- `multiple_applications`: Same identity across multiple applications
- `fraud_network`: Account linked to known fraud network
- `account_takeover`: Account compromised at multiple institutions
- `payment_fraud`: Suspicious payment patterns

**Severity Levels:**
- `critical`: 5+ lenders or known fraud network (Risk Score: 90-100)
- `high`: 3-4 lenders (Risk Score: 70-89)
- `medium`: 2 lenders (Risk Score: 50-69)
- `low`: Single institution or suspicious pattern (Risk Score: 0-49)

**Examples:**

Get recent alerts:
```bash
curl -X GET "http://localhost:8000/api/v1/consortium/alerts?limit=20" \
  -H "X-API-Key: your-sentinel-api-key"
```

Filter by critical severity:
```bash
curl -X GET "http://localhost:8000/api/v1/consortium/alerts?severity=critical&limit=10" \
  -H "X-API-Key: your-sentinel-api-key"
```

Get alerts from last 30 days:
```bash
curl -X GET "http://localhost:8000/api/v1/consortium/alerts?days=30&limit=50" \
  -H "X-API-Key: your-sentinel-api-key"
```

**Status Codes:**
- `200 OK` - Alerts retrieved
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Server error

---

### 12. Get Fraud Patterns

Analyze fraud patterns across consortium.

**Endpoint:** `GET /api/v1/consortium/patterns`

**Authentication:** Required (`X-API-Key` header)

**Query Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `days` | int | 30 | 1-90 | Number of days to analyze |

**Response Schema:**
```json
{
  "patterns": [
    {
      "type": "loan_stacking",
      "count": 450,
      "percentage": 35.2,
      "trend": "increasing",
      "previous_period_count": 380,
      "trend_percentage": 18.4,
      "average_amount": 450000.00,
      "severity": "high"
    },
    {
      "type": "sim_swap",
      "count": 120,
      "percentage": 9.4,
      "trend": "stable",
      "previous_period_count": 118,
      "trend_percentage": 1.7,
      "average_amount": 250000.00,
      "severity": "critical"
    },
    {
      "type": "identity_fraud",
      "count": 280,
      "percentage": 21.9,
      "trend": "decreasing",
      "previous_period_count": 320,
      "trend_percentage": -12.5,
      "average_amount": 300000.00,
      "severity": "high"
    },
    {
      "type": "account_takeover",
      "count": 185,
      "percentage": 14.5,
      "trend": "increasing",
      "previous_period_count": 150,
      "trend_percentage": 23.3,
      "average_amount": 200000.00,
      "severity": "high"
    },
    {
      "type": "card_fraud",
      "count": 225,
      "percentage": 17.6,
      "trend": "stable",
      "previous_period_count": 220,
      "trend_percentage": 2.3,
      "average_amount": 100000.00,
      "severity": "medium"
    }
  ],
  "total_incidents": 1280,
  "period_days": 30,
  "total_amount_protected": 850000000.00,
  "top_pattern": "loan_stacking",
  "trending_up": ["loan_stacking", "account_takeover"],
  "trending_down": ["identity_fraud"]
}
```

**Trend Values:**
- `increasing`: Pattern frequency increased compared to previous period
- `stable`: Pattern frequency remained similar
- `decreasing`: Pattern frequency decreased

**Examples:**

Get patterns for last 30 days:
```bash
curl -X GET "http://localhost:8000/api/v1/consortium/patterns?days=30" \
  -H "X-API-Key: your-sentinel-api-key"
```

Analyze 90-day trends:
```bash
curl -X GET "http://localhost:8000/api/v1/consortium/patterns?days=90" \
  -H "X-API-Key: your-sentinel-api-key"
```

**Status Codes:**
- `200 OK` - Patterns retrieved
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Invalid API key
- `500 Internal Server Error` - Server error

---

## Feedback Endpoints

Report transaction outcomes to improve fraud detection accuracy.

### 13. Submit Feedback

Report actual transaction outcome (fraud/legitimate) for model improvement.

**Endpoint:** `POST /api/v1/feedback`

**Authentication:** Required (`X-API-Key` header)

**Request Body Schema:**
```json
{
  "transaction_id": "TXN20240122001",
  "actual_outcome": "fraud",
  "fraud_type": "loan_stacking",
  "fraud_subtype": "multiple_lenders",
  "notes": "Customer applied to 3 lenders within 48 hours",
  "amount_saved": 500000.00,
  "correction_needed": false
}
```

**Field Descriptions:**
- `transaction_id` (string, required): Transaction to report on
- `actual_outcome` (string, required): "fraud" or "legitimate"
- `fraud_type` (string, optional): Type of fraud detected
- `fraud_subtype` (string, optional): Specific fraud subtype
- `notes` (string, optional): Additional context (max 500 chars)
- `amount_saved` (float, optional): Amount saved by catching fraud
- `correction_needed` (boolean, optional): Whether rule adjustment needed

**Fraud Types:**
- `loan_stacking`: Multiple loan applications
- `sim_swap`: SIM card swap fraud
- `identity_fraud`: Fraudulent identity
- `device_sharing`: Multiple users on same device
- `card_fraud`: Fraudulent card usage
- `account_takeover`: Account compromise
- `bot_activity`: Automated fraud
- `bonus_abuse`: Bonus/promotion abuse
- `chargeback_fraud`: Fraudulent chargebacks
- `other`: Other fraud type

**Response Schema:**
```json
{
  "status": "received",
  "message": "Feedback processed successfully",
  "transaction_id": "TXN20240122001",
  "feedback_id": "FB_abc123xyz",
  "impact": {
    "rule_adjustments": 2,
    "accuracy_improvement": 0.5,
    "model_retraining_scheduled": true,
    "estimated_retraining_time": "24 hours"
  },
  "contribution_score": 150,
  "total_feedback_count": 12500,
  "timestamp": "2024-01-22T10:35:00Z"
}
```

**Example - Report Fraud:**
```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-sentinel-api-key" \
  -d '{
    "transaction_id": "TXN20240122001",
    "actual_outcome": "fraud",
    "fraud_type": "loan_stacking",
    "fraud_subtype": "multiple_lenders",
    "notes": "Customer applied to 3 lenders within 48 hours",
    "amount_saved": 500000.00
  }'
```

**Example - Correct False Positive:**
```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-sentinel-api-key" \
  -d '{
    "transaction_id": "TXN20240122002",
    "actual_outcome": "legitimate",
    "notes": "Legitimate transaction incorrectly flagged",
    "correction_needed": true
  }'
```

**Impact on System:**
1. **Immediate:** Rule weights adjusted based on feedback
2. **Hourly:** Accuracy metrics recalculated
3. **Daily:** Model retraining scheduled if threshold met
4. **Weekly:** Cross-institution intelligence shared via consortium

**Status Codes:**
- `200 OK` - Feedback received and processed
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Invalid API key
- `404 Not Found` - Transaction not found
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

---

## Error Handling

### Standard Error Response

All error responses follow this format:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Description of the error",
    "details": {
      "field": "field_name",
      "issue": "Specific issue with field"
    }
  },
  "timestamp": "2024-01-22T10:30:00Z",
  "request_id": "REQ_abc123xyz"
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request or invalid parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `FORBIDDEN` | 403 | API key lacks required permissions |
| `NOT_FOUND` | 404 | Requested resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Example Error Response

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Invalid transaction amount",
    "details": {
      "field": "amount",
      "issue": "Amount must be greater than 0"
    }
  },
  "timestamp": "2024-01-22T10:30:00Z",
  "request_id": "REQ_abc123xyz"
}
```

---

## Response Codes

### Success Codes (2xx)

| Code | Description |
|------|-------------|
| `200 OK` | Request successful |
| `201 Created` | Resource created successfully |

### Client Error Codes (4xx)

| Code | Description | Example |
|------|-------------|---------|
| `400 Bad Request` | Invalid request format | Missing required field |
| `401 Unauthorized` | Authentication failed | Invalid API key |
| `403 Forbidden` | Insufficient permissions | API key lacks scope |
| `404 Not Found` | Resource not found | Transaction ID doesn't exist |
| `429 Too Many Requests` | Rate limit exceeded | Too many API calls |

### Server Error Codes (5xx)

| Code | Description |
|------|-------------|
| `500 Internal Server Error` | Unexpected server error |
| `503 Service Unavailable` | Service temporarily down |

---

## Rate Limiting

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705928400
```

### Limits by Plan

| Plan | Transactions/Month | Req/Hour | Batch Size |
|------|------------------|----------|------------|
| Starter | 50,000 | 2,083 | 50 |
| Growth | 200,000 | 8,333 | 100 |
| Enterprise | Unlimited | Unlimited | 1,000 |

### Rate Limit Reset

When rate limit is exceeded:
1. API returns `429 Too Many Requests`
2. Use `X-RateLimit-Reset` header to determine reset time
3. Wait and retry after reset time

**Example:**
```bash
# Check remaining requests
curl -i -X GET http://localhost:8000/api/v1/dashboard/stats \
  -H "X-API-Key: your-sentinel-api-key"

# Response headers:
# X-RateLimit-Limit: 1000
# X-RateLimit-Remaining: 42
# X-RateLimit-Reset: 1705928400
```

---

## Best Practices

### 1. Batch Processing
```bash
# Instead of 100 individual requests:
curl -X POST http://localhost:8000/api/v1/check-transactions-batch \
  -H "X-API-Key: your-sentinel-api-key" \
  -d '{"transactions": [...]}'  # 50x faster
```

### 2. Caching
```bash
# Cache results for 5 minutes to avoid redundant API calls
if (cache.has(transaction_id)):
    return cache.get(transaction_id)
else:
    result = api.check_transaction(transaction_id)
    cache.set(transaction_id, result, ttl=300)
    return result
```

### 3. Error Handling
```python
import requests

try:
    response = requests.post(
        'http://localhost:8000/api/v1/check-transaction',
        headers={'X-API-Key': 'sk_live_abc123xyz...'},
        json=transaction_data
    )
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 429:
        # Handle rate limit
        reset_time = int(e.response.headers.get('X-RateLimit-Reset', 0))
        # Retry after reset_time
    elif e.response.status_code == 401:
        # Handle authentication error
        print("Invalid API key")
except requests.exceptions.RequestException as e:
    # Handle connection error
    print(f"Connection error: {e}")
```

### 4. Monitoring
```bash
# Monitor API health
curl http://localhost:8000/health | jq .

# Monitor rate limit usage
curl -i http://localhost:8000/api/v1/dashboard/stats \
  -H "X-API-Key: your-sentinel-api-key" | grep X-RateLimit
```

---

## Testing

### Using curl

```bash
# Health check
curl http://localhost:8000/health

# Check transaction (with auth)
curl -X POST http://localhost:8000/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-sentinel-api-key" \
  -d '{...}'

# Get dashboard stats
curl http://localhost:8000/api/v1/dashboard/stats \
  -H "X-API-Key: your-sentinel-api-key"
```

### Using Python requests

```python
import requests

api_key = "sk_live_abc123xyz..."
base_url = "http://localhost:8000"

# Check single transaction
response = requests.post(
    f"{base_url}/api/v1/check-transaction",
    headers={"X-API-Key": api_key},
    json={
        "transaction_id": "TXN001",
        "user_id": "USR001",
        "amount": 50000,
        "currency": "NGN",
        "user_country": "NG"
    }
)
print(response.json())

# Get dashboard stats
response = requests.get(
    f"{base_url}/api/v1/dashboard/stats",
    headers={"X-API-Key": api_key}
)
print(response.json())
```

### Using JavaScript/Node.js

```javascript
const API_KEY = "sk_live_abc123xyz...";
const BASE_URL = "http://localhost:8000";

// Check transaction
const checkTransaction = async (transaction) => {
  const response = await fetch(`${BASE_URL}/api/v1/check-transaction`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY
    },
    body: JSON.stringify(transaction)
  });
  return response.json();
};

// Example usage
checkTransaction({
  transaction_id: "TXN001",
  user_id: "USR001",
  amount: 50000,
  currency: "NGN",
  user_country: "NG"
}).then(result => console.log(result));
```

---

## Documentation

- **Interactive API Docs:** Visit `http://localhost:8000/docs` (Swagger UI)
- **Alternative Docs:** Visit `http://localhost:8000/redoc` (ReDoc)
- **API Status:** Visit `http://localhost:8000/health`

---

**Last Updated:** 2025-01-22
**Total Endpoints:** 13
**API Version:** v1.0.0
