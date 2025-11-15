# Sentinel API Examples

## Authentication

All API requests require an API key in the `X-API-Key` header:

```bash
X-API-Key: your-api-key-here
```

## Base URL

Development: `http://localhost:8000`
Production: `https://api.sentinel-fraud.com`

---

## 1. Check Transaction for Fraud

**Endpoint**: `POST /api/v1/check-transaction`

### Basic Request

```bash
curl -X POST http://localhost:8000/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo_api_key_12345" \
  -d '{
    "transaction_id": "txn_001",
    "user_id": "user_001",
    "amount": 50000,
    "transaction_type": "loan_disbursement"
  }'
```

### Response (Low Risk)

```json
{
  "transaction_id": "txn_001",
  "risk_score": 15,
  "risk_level": "low",
  "decision": "approve",
  "flags": [],
  "recommendation": "APPROVE - Low fraud risk. Transaction appears legitimate.",
  "processing_time_ms": 45
}
```

### High-Risk Transaction Request

```bash
curl -X POST http://localhost:8000/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo_api_key_12345" \
  -d '{
    "transaction_id": "txn_002",
    "user_id": "user_002",
    "amount": 250000,
    "transaction_type": "loan_disbursement",
    "device_id": "device_abc123",
    "ip_address": "197.210.226.45",
    "account_age_days": 3,
    "transaction_count": 0,
    "phone_changed_recently": true,
    "email_changed_recently": false,
    "bvn": "12345678901",
    "phone": "+2348012345678",
    "email": "user@example.com"
  }'
```

### Response (High Risk)

```json
{
  "transaction_id": "txn_002",
  "risk_score": 85,
  "risk_level": "high",
  "decision": "decline",
  "flags": [
    {
      "type": "new_account_large_amount",
      "severity": "medium",
      "message": "Account only 3 days old requesting ₦250,000",
      "score": 30,
      "confidence": 0.87,
      "metadata": null
    },
    {
      "type": "sim_swap_pattern",
      "severity": "critical",
      "message": "Phone changed + new device + withdrawal - classic SIM swap pattern",
      "score": 45,
      "confidence": 0.88,
      "metadata": null
    }
  ],
  "recommendation": "DECLINE - High risk of SIM swap attack. Request video verification if needed.",
  "processing_time_ms": 87,
  "consortium_alerts": [
    "⚠️ LOAN STACKING: Applied to 3 other lenders this week"
  ]
}
```

### Python Example

```python
import requests

API_KEY = "demo_api_key_12345"
BASE_URL = "http://localhost:8000"

def check_fraud(transaction_data):
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": API_KEY
    }

    response = requests.post(
        f"{BASE_URL}/api/v1/check-transaction",
        json=transaction_data,
        headers=headers
    )

    return response.json()

# Example usage
transaction = {
    "transaction_id": "txn_12345",
    "user_id": "user_789",
    "amount": 150000,
    "transaction_type": "loan_disbursement",
    "device_id": "device_xyz",
    "account_age_days": 45
}

result = check_fraud(transaction)
print(f"Risk Score: {result['risk_score']}")
print(f"Decision: {result['decision']}")
print(f"Processing Time: {result['processing_time_ms']}ms")
```

### JavaScript/Node.js Example

```javascript
const axios = require('axios');

const API_KEY = 'demo_api_key_12345';
const BASE_URL = 'http://localhost:8000';

async function checkFraud(transactionData) {
  try {
    const response = await axios.post(
      `${BASE_URL}/api/v1/check-transaction`,
      transactionData,
      {
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY
        }
      }
    );

    return response.data;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    throw error;
  }
}

// Example usage
const transaction = {
  transaction_id: 'txn_12345',
  user_id: 'user_789',
  amount: 150000,
  transaction_type: 'loan_disbursement',
  device_id: 'device_xyz',
  account_age_days: 45
};

checkFraud(transaction)
  .then(result => {
    console.log('Risk Score:', result.risk_score);
    console.log('Decision:', result.decision);
    console.log('Processing Time:', result.processing_time_ms, 'ms');
  });
```

---

## 2. Submit Feedback

**Endpoint**: `POST /api/v1/feedback`

### Confirm Fraud

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo_api_key_12345" \
  -d '{
    "transaction_id": "txn_002",
    "actual_outcome": "fraud",
    "fraud_type": "sim_swap",
    "notes": "Customer confirmed they did not apply. SIM swap attack confirmed.",
    "amount_saved": 250000
  }'
```

### Response

```json
{
  "status": "received",
  "message": "Feedback processed successfully",
  "accuracy_impact": "Updated 2 rule(s) accuracy",
  "total_feedback_count": 47
}
```

### Report False Positive

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo_api_key_12345" \
  -d '{
    "transaction_id": "txn_003",
    "actual_outcome": "legitimate",
    "notes": "Customer verified. Transaction was legitimate."
  }'
```

---

## 3. Get Dashboard Statistics

**Endpoint**: `GET /api/v1/dashboard/stats`

```bash
curl -X GET http://localhost:8000/api/v1/dashboard/stats \
  -H "X-API-Key: demo_api_key_12345"
```

### Response

```json
{
  "today_transactions": 1247,
  "today_high_risk": 34,
  "today_medium_risk": 89,
  "today_low_risk": 1124,
  "today_fraud_prevented_amount": 8400000,
  "month_transactions": 38942,
  "month_fraud_caught": 247,
  "month_fraud_prevented_amount": 87300000,
  "month_false_positive_rate": 0.083,
  "month_accuracy": 0.821,
  "risk_distribution": {
    "low": 35124,
    "medium": 2895,
    "high": 923
  },
  "fraud_types": {
    "loan_stacking": 87,
    "sim_swap": 65,
    "new_account": 42,
    "device_sharing": 31,
    "dormant_account": 22
  }
}
```

---

## 4. Get Transaction History

**Endpoint**: `GET /api/v1/dashboard/transactions`

```bash
# Get all transactions
curl -X GET "http://localhost:8000/api/v1/dashboard/transactions?limit=50" \
  -H "X-API-Key: demo_api_key_12345"

# Filter by risk level
curl -X GET "http://localhost:8000/api/v1/dashboard/transactions?risk_level=high&limit=20" \
  -H "X-API-Key: demo_api_key_12345"

# Filter by outcome
curl -X GET "http://localhost:8000/api/v1/dashboard/transactions?outcome=fraud&limit=10" \
  -H "X-API-Key: demo_api_key_12345"
```

### Response

```json
[
  {
    "transaction_id": "txn_12345",
    "amount": 250000,
    "risk_score": 92,
    "risk_level": "high",
    "decision": "decline",
    "outcome": "fraud",
    "created_at": "2024-11-15T03:42:00"
  },
  {
    "transaction_id": "txn_12346",
    "amount": 50000,
    "risk_score": 15,
    "risk_level": "low",
    "decision": "approve",
    "outcome": "legitimate",
    "created_at": "2024-11-15T14:15:00"
  }
]
```

---

## 5. Get Client Information

**Endpoint**: `GET /api/v1/dashboard/client-info`

```bash
curl -X GET http://localhost:8000/api/v1/dashboard/client-info \
  -H "X-API-Key: demo_api_key_12345"
```

### Response

```json
{
  "client_id": "demo_client",
  "company_name": "Demo Financial Services",
  "plan": "starter",
  "status": "active",
  "total_checks": 38942,
  "total_fraud_caught": 247,
  "total_amount_saved": 87300000,
  "created_at": "2024-01-15T10:00:00"
}
```

---

## 6. Get Rule Accuracy

**Endpoint**: `GET /api/v1/dashboard/rule-accuracy`

```bash
curl -X GET http://localhost:8000/api/v1/dashboard/rule-accuracy \
  -H "X-API-Key: demo_api_key_12345"
```

### Response

```json
[
  {
    "rule_name": "loan_stacking",
    "triggered_count": 234,
    "accuracy": 0.846,
    "precision": 0.892,
    "recall": 0.0,
    "current_weight": 1.2
  },
  {
    "rule_name": "sim_swap_pattern",
    "triggered_count": 156,
    "accuracy": 0.878,
    "precision": 0.913,
    "recall": 0.0,
    "current_weight": 1.3
  },
  {
    "rule_name": "new_account_large_amount",
    "triggered_count": 892,
    "accuracy": 0.753,
    "precision": 0.698,
    "recall": 0.0,
    "current_weight": 0.9
  }
]
```

---

## 7. Get Specific Transaction

**Endpoint**: `GET /api/v1/transaction/{transaction_id}`

```bash
curl -X GET http://localhost:8000/api/v1/transaction/txn_002 \
  -H "X-API-Key: demo_api_key_12345"
```

### Response

```json
{
  "transaction_id": "txn_002",
  "risk_score": 85,
  "risk_level": "high",
  "decision": "decline",
  "flags": [
    {
      "type": "new_account_large_amount",
      "severity": "medium",
      "message": "Account only 3 days old requesting ₦250,000",
      "score": 30,
      "confidence": 0.87,
      "metadata": null
    }
  ],
  "recommendation": null,
  "processing_time_ms": 87
}
```

---

## 8. Health Check

**Endpoint**: `GET /health`

```bash
curl -X GET http://localhost:8000/health
```

### Response

```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "ok",
  "redis": "ok",
  "timestamp": "2024-11-15T10:30:00"
}
```

---

## Error Responses

### 401 Unauthorized (Missing API Key)

```json
{
  "detail": "API key missing. Please provide X-API-Key header."
}
```

### 401 Unauthorized (Invalid API Key)

```json
{
  "detail": "Invalid API key"
}
```

### 403 Forbidden (Suspended Account)

```json
{
  "detail": "Account is suspended. Please contact support."
}
```

### 404 Not Found

```json
{
  "detail": "Transaction txn_999 not found"
}
```

### 500 Internal Server Error

```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred",
  "timestamp": "2024-11-15T10:30:00"
}
```

---

## Rate Limiting

Requests include rate limit headers:

```
X-RateLimit-Limit: 10000
X-RateLimit-Remaining: 9847
X-RateLimit-Reset: 1699999999
```

When rate limit is exceeded:

```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 3600
}
```

---

## Best Practices

1. **Store API keys securely** - Never commit API keys to version control
2. **Handle errors gracefully** - Always check response status codes
3. **Use HTTPS in production** - Never send API keys over unencrypted connections
4. **Implement retry logic** - With exponential backoff for failed requests
5. **Monitor response times** - Alert if `processing_time_ms` exceeds 100ms
6. **Submit feedback** - Helps improve accuracy over time
7. **Cache consortium data** - Reduce redundant API calls for the same user

---

## Support

For API support:
- Email: api-support@sentinel-fraud.com
- Documentation: https://docs.sentinel-fraud.com
- Status Page: https://status.sentinel-fraud.com
