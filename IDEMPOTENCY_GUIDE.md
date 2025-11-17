# API Idempotency Guide

## Overview

The Sentinel fraud detection API is **idempotent** - submitting the same transaction ID multiple times will return the same result. This is a **feature, not a bug**!

## How It Works

When you submit a transaction for fraud checking, the API:

1. **Checks if the transaction_id was already processed** (database lookup)
2. **If YES**: Returns the cached result from the database immediately
   - Response includes `"cached": true`
   - Processing time is very fast (~5-10ms)
   - Uses the values from the **first** submission
3. **If NO**: Processes the transaction normally
   - Runs all fraud detection rules
   - Stores result in database
   - Returns fresh analysis

## Example: Duplicate Transaction Detection

### First Request
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/check-transaction' \
  -H 'X-API-Key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
  "transaction_id": "txn_12345",
  "account_age_days": 3,
  "amount": 250000,
  "user_id": "user_789",
  ...
}'
```

**Response:** Processed normally, stored in database
- `"cached": false`
- Uses values: account_age_days=3, amount=250000

### Second Request (Same transaction_id, different values)
```bash
curl -X 'POST' \
  'http://localhost:8000/api/v1/check-transaction' \
  -H 'X-API-Key: YOUR_API_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
  "transaction_id": "txn_12345",
  "account_age_days": 300,
  "amount": 25000,
  "user_id": "user_789",
  ...
}'
```

**Response:** Returns cached result from first request
- `"cached": true`
- **Still shows values from first request:** account_age_days=3, amount=250000
- **Ignores new values** (account_age_days=300, amount=25000)

## Why This Is Useful

### ✅ Benefits

1. **Network Retry Safety**
   - If a client times out and retries, they won't get duplicate charges/processing
   - Same transaction_id = same response

2. **Duplicate Prevention**
   - Prevents accidental double-processing (e.g., double-click on submit button)
   - Database constraint violations avoided

3. **Fast Responses**
   - Cached responses return in ~5-10ms
   - Original processing takes ~50-100ms

4. **Consistent Results**
   - Same transaction always gets same fraud score
   - Useful for auditing and compliance

## Solutions for Testing

### Option 1: Use Unique Transaction IDs (Recommended)
Generate a new transaction ID for each test:

```bash
# Good - Unique IDs
txn_12345  # First test
txn_12346  # Second test
txn_12347  # Third test

# Or use timestamps
txn_$(date +%s)
```

### Option 2: Delete Test Transactions

If you need to reuse a transaction ID for testing:

```python
from app.db.session import SessionLocal
from app.models.database import Transaction

db = SessionLocal()

# Delete specific transaction
db.query(Transaction).filter(
    Transaction.transaction_id == "txn_12345"
).delete()

db.commit()
db.close()
```

### Option 3: Use Testing Endpoint (Future Feature)

We could add a `DELETE /api/v1/transaction/{transaction_id}` endpoint for testing:

```bash
# Clear a test transaction
curl -X 'DELETE' \
  'http://localhost:8000/api/v1/transaction/txn_12345' \
  -H 'X-API-Key: YOUR_API_KEY'
```

## Best Practices

### ✅ Production Usage

```bash
# Use your application's unique transaction IDs
{
  "transaction_id": "loan_app_1234567890",  # From your system
  "amount": 50000,
  ...
}
```

### ✅ Testing

```bash
# Generate unique test IDs
{
  "transaction_id": "test_001",  # First test
  ...
}

{
  "transaction_id": "test_002",  # Second test
  ...
}
```

### ❌ Don't Do This

```bash
# Don't reuse transaction IDs expecting different results
{
  "transaction_id": "txn_12345",  # First submission: amount=100000
  ...
}

{
  "transaction_id": "txn_12345",  # Second submission: amount=50000
  ...
  # Will still return result for amount=100000 (cached)
}
```

## Identifying Cached Responses

Check the `cached` field in the response:

```json
{
  "transaction_id": "txn_12345",
  "risk_score": 85,
  "risk_level": "high",
  "decision": "decline",
  "cached": true,  // ← This transaction was already processed
  "processing_time_ms": 5  // ← Very fast (cached lookup)
}
```

If `cached: true`, the response is from a previous submission with the same transaction_id.

## FAQ

**Q: Why do cached responses show wrong values?**
A: They're not "wrong" - they're the values from the **first** time that transaction_id was submitted. The API is showing you the original fraud check result.

**Q: Can I force a re-check?**
A: Yes, use a different transaction_id. In production, this shouldn't happen since each real transaction has a unique ID.

**Q: What if I made a mistake on the first submission?**
A: For testing, delete the transaction from the database. For production, contact support to void/delete the incorrect transaction.

**Q: How long are results cached?**
A: Forever (they're stored in the database). This is intentional for audit trails and compliance.

## Technical Implementation

The idempotency check happens in `app/core/fraud_detector.py:136-181`:

```python
# Check if this transaction was already processed
existing_transaction = self.db.query(Transaction).filter(
    Transaction.transaction_id == transaction.transaction_id,
    Transaction.client_id == self.client_id
).first()

if existing_transaction:
    # Return cached result
    return TransactionCheckResponse(
        ...
        cached=True
    )
```

This ensures that:
- Each transaction_id is only processed once
- Subsequent requests return the original result
- The API is idempotent and safe for retries
