# Client Integration Guide

**Purpose:** Step-by-step guide for integrating Sentinel fraud detection into your application

**Target Audience:** Developers integrating Sentinel API into lending, fintech, ecommerce, betting, gaming, crypto, or marketplace platforms

---

## Quick Start (5 Minutes)

### Step 1: Get API Credentials

```bash
# Create API key for new client
python create_api_key.py

# Example output:
# Client ID: client_abc123
# API Key: sk_live_xyz789...
# Company: Acme Fintech
# Vertical: lending
```

**Save these credentials securely!** You'll need them for all API requests.

---

### Step 2: Test Connection

```bash
# Test if API is reachable
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "redis": "connected"
}
```

---

### Step 3: Your First Fraud Check

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: sk_live_xyz789..." \
  -d '{
    "transaction_id": "txn_001",
    "user_id": "user_123",
    "amount": 500000,
    "industry": "lending",
    "transaction_type": "loan_disbursement",
    "email": "customer@example.com",
    "phone": "+2348012345678",
    "device_id": "device_abc",
    "account_age_days": 5
  }'
```

**Response:**
```json
{
  "transaction_id": "txn_001",
  "risk_score": 45,
  "risk_level": "medium",
  "decision": "review",
  "flags": [
    {
      "type": "NewAccountLargeAmountRule",
      "severity": "medium",
      "message": "New account (5 days old) requesting large amount",
      "score": 30,
      "confidence": 0.85
    }
  ],
  "recommendation": "REVIEW - Manual review recommended",
  "processing_time_ms": 87
}
```

---

## Integration Architecture

### Flow Diagram

```
Your Application
       ↓
   [API Call]
       ↓
Sentinel Fraud Detection
       ↓
   [Response]
       ↓
Your Application → Make Decision
       ↓
[Approve/Review/Decline]
```

---

## Integration Options

### Option 1: Synchronous (Recommended for Real-Time)

**Use when:** You need immediate fraud decision before proceeding

```python
# Python example
import requests

def check_fraud(transaction):
    """Check transaction for fraud before processing"""

    response = requests.post(
        'http://localhost:8000/api/v1/fraud/check',
        headers={
            'Content-Type': 'application/json',
            'X-API-Key': 'sk_live_xyz789...'
        },
        json={
            'transaction_id': transaction['id'],
            'user_id': transaction['user_id'],
            'amount': transaction['amount'],
            'industry': 'lending',
            'transaction_type': 'loan_disbursement',
            'email': transaction['email'],
            'phone': transaction['phone'],
            'device_id': transaction['device_id'],
            'account_age_days': transaction['account_age_days']
        }
    )

    result = response.json()

    # Make decision based on risk level
    if result['decision'] == 'approve':
        # Process transaction immediately
        return process_loan_disbursement(transaction)

    elif result['decision'] == 'review':
        # Send to manual review queue
        return send_to_manual_review(transaction, result)

    else:  # decline
        # Reject transaction
        return reject_transaction(transaction, result['recommendation'])
```

**Pros:** Immediate decision, simple logic
**Cons:** Adds latency to transaction flow (usually ~100ms)

---

### Option 2: Asynchronous (Recommended for Background Checks)

**Use when:** You can process transaction first, check fraud later

```python
# Python with Celery/background jobs
from celery import shared_task

@shared_task
def check_fraud_async(transaction_id):
    """Check fraud in background, flag suspicious transactions"""

    transaction = get_transaction(transaction_id)

    response = requests.post(
        'http://localhost:8000/api/v1/fraud/check',
        headers={'X-API-Key': 'sk_live_xyz789...'},
        json={
            'transaction_id': transaction_id,
            'user_id': transaction['user_id'],
            'amount': transaction['amount'],
            'industry': 'lending',
            # ... other fields
        }
    )

    result = response.json()

    # If high risk, freeze account and alert ops team
    if result['decision'] == 'decline':
        freeze_account(transaction['user_id'])
        alert_ops_team(transaction_id, result)

# Call asynchronously
process_loan_disbursement(transaction)
check_fraud_async.delay(transaction['id'])  # Runs in background
```

**Pros:** No latency impact on user experience
**Cons:** Fraud detected after transaction processed (may need reversal)

---

## Code Examples by Language

### Python (Recommended)

```python
import requests
from typing import Dict, Any

class SentinelClient:
    """Sentinel fraud detection client"""

    def __init__(self, api_key: str, base_url: str = 'http://localhost:8000'):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Content-Type': 'application/json',
            'X-API-Key': api_key
        }

    def check_fraud(
        self,
        transaction_id: str,
        user_id: str,
        amount: float,
        industry: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Check transaction for fraud

        Args:
            transaction_id: Your transaction ID
            user_id: Your user ID
            amount: Transaction amount
            industry: One of: lending, fintech, ecommerce, betting, gaming, crypto, marketplace
            **kwargs: Additional fields (email, phone, device_id, etc.)

        Returns:
            Fraud detection result with risk_score, decision, flags
        """
        payload = {
            'transaction_id': transaction_id,
            'user_id': user_id,
            'amount': amount,
            'industry': industry,
            **kwargs
        }

        response = requests.post(
            f'{self.base_url}/api/v1/fraud/check',
            headers=self.headers,
            json=payload,
            timeout=5  # 5 second timeout
        )
        response.raise_for_status()
        return response.json()

    def submit_feedback(
        self,
        transaction_id: str,
        actual_outcome: str,
        fraud_type: str = None
    ):
        """
        Submit feedback on fraud detection accuracy

        Args:
            transaction_id: Transaction ID previously checked
            actual_outcome: 'fraud' or 'legitimate'
            fraud_type: Optional fraud type if outcome was fraud
        """
        payload = {
            'transaction_id': transaction_id,
            'actual_outcome': actual_outcome
        }
        if fraud_type:
            payload['fraud_type'] = fraud_type

        response = requests.post(
            f'{self.base_url}/api/v1/feedback/submit',
            headers=self.headers,
            json=payload
        )
        return response.json()


# Usage
client = SentinelClient(api_key='sk_live_xyz789...')

result = client.check_fraud(
    transaction_id='txn_001',
    user_id='user_123',
    amount=500000,
    industry='lending',
    email='customer@example.com',
    phone='+2348012345678',
    device_id='device_abc',
    account_age_days=5
)

if result['decision'] == 'approve':
    print("✓ Transaction approved")
elif result['decision'] == 'review':
    print("⚠ Manual review needed")
else:
    print("✗ Transaction declined")
```

---

### Node.js

```javascript
// sentinel-client.js
const axios = require('axios');

class SentinelClient {
  constructor(apiKey, baseUrl = 'http://localhost:8000') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.headers = {
      'Content-Type': 'application/json',
      'X-API-Key': apiKey
    };
  }

  async checkFraud({
    transactionId,
    userId,
    amount,
    industry,
    ...additionalFields
  }) {
    try {
      const response = await axios.post(
        `${this.baseUrl}/api/v1/fraud/check`,
        {
          transaction_id: transactionId,
          user_id: userId,
          amount,
          industry,
          ...additionalFields
        },
        {
          headers: this.headers,
          timeout: 5000 // 5 second timeout
        }
      );

      return response.data;
    } catch (error) {
      console.error('Sentinel API error:', error.message);
      throw error;
    }
  }

  async submitFeedback(transactionId, actualOutcome, fraudType = null) {
    const payload = {
      transaction_id: transactionId,
      actual_outcome: actualOutcome
    };

    if (fraudType) {
      payload.fraud_type = fraudType;
    }

    const response = await axios.post(
      `${this.baseUrl}/api/v1/feedback/submit`,
      payload,
      { headers: this.headers }
    );

    return response.data;
  }
}

// Usage
const client = new SentinelClient('sk_live_xyz789...');

async function processLoan(loan) {
  const result = await client.checkFraud({
    transactionId: loan.id,
    userId: loan.userId,
    amount: loan.amount,
    industry: 'lending',
    email: loan.email,
    phone: loan.phone,
    deviceId: loan.deviceId,
    accountAgeDays: loan.accountAgeDays
  });

  if (result.decision === 'approve') {
    return approveLoan(loan);
  } else if (result.decision === 'review') {
    return sendToManualReview(loan, result);
  } else {
    return declineLoan(loan, result.recommendation);
  }
}
```

---

### PHP

```php
<?php
// SentinelClient.php

class SentinelClient {
    private $apiKey;
    private $baseUrl;

    public function __construct($apiKey, $baseUrl = 'http://localhost:8000') {
        $this->apiKey = $apiKey;
        $this->baseUrl = $baseUrl;
    }

    public function checkFraud($data) {
        $url = $this->baseUrl . '/api/v1/fraud/check';

        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, [
            'Content-Type: application/json',
            'X-API-Key: ' . $this->apiKey
        ]);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);

        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($httpCode !== 200) {
            throw new Exception("Sentinel API error: HTTP $httpCode");
        }

        return json_decode($response, true);
    }
}

// Usage
$client = new SentinelClient('sk_live_xyz789...');

$result = $client->checkFraud([
    'transaction_id' => 'txn_001',
    'user_id' => 'user_123',
    'amount' => 500000,
    'industry' => 'lending',
    'email' => 'customer@example.com',
    'phone' => '+2348012345678',
    'device_id' => 'device_abc',
    'account_age_days' => 5
]);

if ($result['decision'] === 'approve') {
    approveLoan($loan);
} elseif ($result['decision'] === 'review') {
    sendToManualReview($loan, $result);
} else {
    declineLoan($loan);
}
?>
```

---

## Required vs. Optional Fields

### Minimum Required Fields (Will work but limited accuracy)

```json
{
  "transaction_id": "txn_001",    // REQUIRED: Your unique transaction ID
  "user_id": "user_123",          // REQUIRED: Your user ID
  "amount": 500000,               // REQUIRED: Transaction amount
  "industry": "lending"           // REQUIRED: Your industry vertical
}
```

### Recommended Fields (80% accuracy)

```json
{
  "transaction_id": "txn_001",
  "user_id": "user_123",
  "amount": 500000,
  "industry": "lending",

  // Add these for better accuracy:
  "email": "customer@example.com",
  "phone": "+2348012345678",
  "device_id": "device_abc123",
  "ip_address": "197.210.85.45",
  "account_age_days": 5,
  "transaction_count": 2
}
```

### Full Fields (95%+ accuracy)

See `API_EXAMPLES.md` for complete list of 249+ available fields.

---

## Industry-Specific Integration

### Lending Integration

```python
def check_loan_application(application):
    """Check loan application for fraud"""

    result = sentinel.check_fraud(
        transaction_id=application['id'],
        user_id=application['user_id'],
        amount=application['loan_amount'],
        industry='lending',
        transaction_type='loan_disbursement',

        # Lending-specific fields
        email=application['email'],
        phone=application['phone'],
        bvn=application['bvn'],  # Nigerian BVN
        device_fingerprint=get_device_fingerprint(),
        account_age_days=application['account_age_days'],
        phone_changed_recently=application['phone_changed_in_48h'],

        # Behavioral signals
        is_first_transaction=application['is_first_loan'],
        previous_fraud_count=application['previous_fraud_count']
    )

    # Lending has higher threshold (65%)
    # Less likely to decline good customers
    return result
```

---

### Crypto Integration

```python
def check_crypto_withdrawal(withdrawal):
    """Check crypto withdrawal for fraud"""

    result = sentinel.check_fraud(
        transaction_id=withdrawal['id'],
        user_id=withdrawal['user_id'],
        amount=withdrawal['amount_usd'],
        industry='crypto',
        transaction_type='crypto_withdrawal',

        # Crypto-specific fields
        wallet_address=withdrawal['destination_wallet'],
        wallet_age_days=withdrawal['wallet_age_days'],
        blockchain=withdrawal['blockchain'],  # bitcoin, ethereum, etc.
        is_new_wallet=withdrawal['is_first_time_wallet'],

        # KYC status (critical for crypto)
        email=withdrawal['email'],
        phone=withdrawal['phone'],
        kyc_verified=withdrawal['kyc_verified']
    )

    # Crypto has stricter threshold (50%)
    # More likely to flag suspicious activity
    return result
```

---

### E-commerce Integration

```python
def check_purchase(order):
    """Check e-commerce purchase for fraud"""

    result = sentinel.check_fraud(
        transaction_id=order['id'],
        user_id=order['customer_id'],
        amount=order['total'],
        industry='ecommerce',
        transaction_type='purchase',

        # E-commerce specific
        card_bin=order['card_first_6'],
        card_last4=order['card_last_4'],
        shipping_address_matches_billing=order['address_match'],
        is_digital_goods=order['is_digital'],

        # Behavioral
        device_id=order['device_id'],
        ip_address=order['ip_address'],
        session_duration_seconds=order['session_duration']
    )

    return result
```

---

## Handling Different Decisions

### Decision: "approve"

```python
if result['decision'] == 'approve':
    # Low risk (score < threshold * 0.7)
    # Safe to process immediately
    process_transaction_immediately()
    log_fraud_check(result)
```

### Decision: "review"

```python
elif result['decision'] == 'review':
    # Medium risk (score between threshold * 0.7 and threshold)
    # Send to manual review

    # Option 1: Hold transaction pending review
    hold_transaction()
    create_review_ticket(transaction_id, result)
    notify_ops_team()

    # Option 2: Process with additional verification
    request_additional_verification()  # ID, selfie, etc.
    if verification_passed():
        process_transaction()
```

### Decision: "decline"

```python
else:  # decline
    # High risk (score >= threshold)
    # Reject transaction

    decline_transaction()
    log_fraud_attempt(result)

    # Optionally notify customer
    send_email(
        to=customer_email,
        subject="Transaction Declined",
        body=f"Your transaction was declined for security reasons. "
             f"Contact support if you believe this is an error."
    )

    # Block repeat offenders
    if result['risk_score'] >= 90:
        flag_account_for_investigation()
```

---

## Best Practices

### 1. **Always Submit Feedback**

Help improve accuracy by reporting actual outcomes:

```python
# When you discover a transaction was fraud
sentinel.submit_feedback(
    transaction_id='txn_001',
    actual_outcome='fraud',
    fraud_type='loan_stacking'
)

# When a declined transaction was actually legitimate
sentinel.submit_feedback(
    transaction_id='txn_002',
    actual_outcome='legitimate'
)
```

### 2. **Cache Device Fingerprints**

```javascript
// On your frontend, capture device fingerprint
import FingerprintJS from '@fingerprintjs/fingerprintjs';

const fp = await FingerprintJS.load();
const result = await fp.get();
const deviceFingerprint = result.visitorId;

// Send to backend with transaction
fetch('/api/transactions', {
  method: 'POST',
  body: JSON.stringify({
    ...transactionData,
    device_fingerprint: deviceFingerprint
  })
});
```

### 3. **Handle Errors Gracefully**

```python
try:
    result = sentinel.check_fraud(...)
except requests.Timeout:
    # Sentinel took too long (> 5s)
    # Fail open: approve transaction, check fraud async
    logger.warning("Sentinel timeout, approving transaction")
    process_transaction()
    check_fraud_async(transaction_id)

except requests.HTTPError as e:
    if e.response.status_code == 429:
        # Rate limit exceeded
        # Queue for later or use cached rules
        logger.error("Rate limit exceeded")
    else:
        # Other API error
        # Fail open or use local rules
        logger.error(f"Sentinel API error: {e}")
        use_local_fraud_rules()
```

### 4. **Monitor Performance**

```python
import time

start = time.time()
result = sentinel.check_fraud(...)
latency = (time.time() - start) * 1000

# Log metrics
metrics.histogram('sentinel.latency_ms', latency)
metrics.counter(f'sentinel.decision.{result["decision"]}')

if latency > 200:
    logger.warning(f"Slow Sentinel response: {latency}ms")
```

---

## Testing Integration

### Step 1: Test with Sample Data

```python
# Use test API key
client = SentinelClient(api_key='sk_test_xyz...')

# Test low-risk transaction
result = client.check_fraud(
    transaction_id='test_low_risk',
    user_id='test_user_001',
    amount=10000,
    industry='lending',
    account_age_days=365,
    transaction_count=50
)
assert result['decision'] == 'approve'

# Test high-risk transaction
result = client.check_fraud(
    transaction_id='test_high_risk',
    user_id='test_user_002',
    amount=5000000,
    industry='crypto',
    account_age_days=1,
    is_new_wallet=True,
    phone_changed_recently=True
)
assert result['decision'] in ['review', 'decline']
```

### Step 2: Staging Environment

```bash
# Point to staging Sentinel instance
export SENTINEL_URL=https://sentinel-staging.yourdomain.com
export SENTINEL_API_KEY=sk_staging_...

# Run integration tests
pytest tests/test_sentinel_integration.py
```

### Step 3: Production Gradual Rollout

```python
# Phase 1: Shadow mode (don't act on decisions)
result = sentinel.check_fraud(...)
log_decision(result)  # Log but don't act
process_transaction()  # Always approve

# Phase 2: Review only
if result['decision'] == 'decline':
    send_to_manual_review()  # Don't auto-decline yet
else:
    process_transaction()

# Phase 3: Full enforcement
if result['decision'] == 'approve':
    process_transaction()
else:
    handle_fraud(result)
```

---

## Troubleshooting

### "Transaction not found" error

**Cause:** Idempotency - you're checking the same transaction_id twice

**Solution:** Each transaction_id should be unique. Use UUIDs or timestamps.

```python
import uuid
transaction_id = f"txn_{uuid.uuid4()}"
```

### High false positive rate

**Cause:** Industry threshold too strict for your use case

**Solution:** Adjust vertical threshold

```bash
curl -X PATCH http://localhost:8000/api/v1/verticals/lending/config \
  -H "Content-Type: application/json" \
  -d '{"fraud_score_threshold": 70.0}'  # Increase from 65 to 70
```

### Missing fields warnings

**Cause:** Not sending enough context fields

**Solution:** Add more fields for better accuracy (see Recommended Fields above)

---

## Support & Monitoring

### Dashboard

```bash
# View fraud statistics
curl http://localhost:8000/api/v1/dashboard/stats

# View recent transactions
curl http://localhost:8000/api/v1/dashboard/transactions?limit=100
```

### Logs

```bash
# Check Sentinel logs
tail -f logs/sentinel.log

# Check for your transactions
grep "client_abc123" logs/sentinel.log
```

---

## Summary Checklist

Before going live, ensure:

- [ ] API key created and stored securely
- [ ] Integration code tested with sample data
- [ ] Error handling implemented (timeouts, rate limits)
- [ ] Feedback loop set up (report actual fraud)
- [ ] Device fingerprinting implemented (if applicable)
- [ ] Staging environment tested
- [ ] Production gradual rollout plan
- [ ] Monitoring/alerting configured
- [ ] Team trained on manual review process
- [ ] Vertical threshold tuned for your risk tolerance

---

## Need Help?

- **API Documentation:** See `API_EXAMPLES.md`
- **Testing Guide:** See `TESTING_GUIDE_VERTICAL_AND_ML.md`
- **Feature Guide:** See `RULES_AND_FEATURES.md`
- **Support:** Contact your account manager

---

**Integration Complete!** 🎉

Your application is now protected by Sentinel's 29 fraud detection rules, vertical-specific thresholds, and ML-powered behavioral analysis.
