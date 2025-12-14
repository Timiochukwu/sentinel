# WEEK 3: Pydantic Schemas & Core Models
**Days 15-21 | Month 1**

## Overview
This week completes the data models with comprehensive Pydantic schemas:
- TransactionCheckRequest with 249+ fraud detection features
- Industry enum (7 verticals: fintech, lending, crypto, betting, ecommerce, marketplace, gaming)
- Transaction type enums
- Response schemas for fraud check results
- Validation rules for all API inputs

## Files to Build

```
app/models/
└── schemas.py                    # 1,141 lines - Complete schema definitions
```

**Total for Week 3:** 1 file (but it's comprehensive!), ~1,141 lines of code

---

## Dependencies

Create `requirements.txt` in this folder (includes Weeks 1-2):

```
# Week 1 dependencies
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
alembic==1.12.1

# Week 2 dependencies
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# Week 3 dependencies (NEW)
email-validator==2.1.0
phonenumbers==8.13.26
```

### Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Install new dependencies
pip install -r build/month_01/week_03/requirements.txt
```

---

## File Details

### `app/models/schemas.py` (1,141 lines)

**Purpose:** Complete Pydantic schema definitions for all API requests and responses

**Structure:**
1. **Enums** (Lines 1-150)
   - `TransactionType` - 20+ transaction types across all verticals
   - `Industry` - 7 supported industries

2. **TransactionCheckRequest** (Lines 151-900)
   - 249+ fraud detection features organized in categories
   - Validation rules for each field
   - Optional vs required fields

3. **Response Schemas** (Lines 901-1,000)
   - `TransactionCheckResponse` - Fraud check results
   - `FraudFlagResponse` - Individual fraud flags
   - `RiskLevel` enum

4. **Utility Schemas** (Lines 1,001-1,141)
   - `HealthCheck` - System health status
   - `DashboardStats` - Analytics data
   - `FeedbackRequest` - User feedback

---

## Schema Categories

### Category 1: Enums

#### Industry Enum (7 Verticals)
```python
class Industry(str, Enum):
    FINTECH = "fintech"          # Digital payments, transfers, wallets
    LENDING = "lending"           # Loans, credit, BNPL
    CRYPTO = "crypto"             # Cryptocurrency exchanges
    BETTING = "betting"           # Sports betting, gambling
    ECOMMERCE = "ecommerce"       # Online shopping
    MARKETPLACE = "marketplace"   # P2P marketplaces
    GAMING = "gaming"             # In-game purchases
```

#### Transaction Types (22 Types)
```python
class TransactionType(str, Enum):
    # Fintech/Lending
    LOAN_DISBURSEMENT = "loan_disbursement"
    LOAN_REPAYMENT = "loan_repayment"
    TRANSFER = "transfer"
    WITHDRAWAL = "withdrawal"
    DEPOSIT = "deposit"
    BILL_PAYMENT = "bill_payment"

    # E-commerce
    PURCHASE = "purchase"
    REFUND = "refund"
    CHARGEBACK = "chargeback"
    CHECKOUT = "checkout"

    # Betting/Gaming
    BET_PLACEMENT = "bet_placement"
    BET_WITHDRAWAL = "bet_withdrawal"
    BONUS_CLAIM = "bonus_claim"

    # Crypto
    CRYPTO_DEPOSIT = "crypto_deposit"
    CRYPTO_WITHDRAWAL = "crypto_withdrawal"
    P2P_TRADE = "p2p_trade"
    SWAP = "swap"

    # And more...
```

---

### Category 2: TransactionCheckRequest (249+ Features)

The main request schema with all fraud detection features organized by category.

#### Basic Transaction Info (10 fields)
```python
user_id: str = Field(..., description="Unique user identifier")
amount: float = Field(..., gt=0, description="Transaction amount")
currency: str = Field(default="NGN", description="Currency code")
transaction_type: str = Field(..., description="Type of transaction")
industry: Industry = Field(..., description="Business vertical")
transaction_id: Optional[str] = None
timestamp: Optional[datetime] = None
reference_id: Optional[str] = None
merchant_id: Optional[str] = None
merchant_category: Optional[str] = None
```

#### User Identity (15 fields)
```python
email: Optional[str] = Field(None, description="User email address")
phone: Optional[str] = Field(None, description="Phone number")
full_name: Optional[str] = None
date_of_birth: Optional[str] = None
bvn: Optional[str] = Field(None, description="Bank Verification Number")
nin: Optional[str] = Field(None, description="National ID Number")
account_age_days: Optional[int] = Field(None, ge=0)
kyc_verified: Optional[bool] = False
kyc_level: Optional[int] = Field(None, ge=0, le=3)
is_first_transaction: Optional[bool] = None
# ... and more
```

#### Device & Fingerprinting (25 fields)
```python
ip_address: Optional[str] = None
device_id: Optional[str] = None
device_fingerprint: Optional[str] = None
user_agent: Optional[str] = None
browser: Optional[str] = None
os: Optional[str] = None
device_type: Optional[str] = None  # mobile, desktop, tablet
screen_resolution: Optional[str] = None
timezone: Optional[str] = None
language: Optional[str] = None
# Canvas fingerprinting
canvas_fingerprint: Optional[str] = None
webgl_fingerprint: Optional[str] = None
# ... and more
```

#### Network Analysis (20 fields)
```python
is_vpn: Optional[bool] = None
is_proxy: Optional[bool] = None
is_tor: Optional[bool] = None
is_datacenter: Optional[bool] = None
ip_country: Optional[str] = None
ip_city: Optional[str] = None
ip_risk_score: Optional[float] = Field(None, ge=0, le=100)
asn: Optional[str] = None  # Autonomous System Number
isp: Optional[str] = None
connection_type: Optional[str] = None  # cellular, wifi, ethernet
# ... and more
```

#### Velocity & Behavioral (35 fields)
```python
# Transaction velocity
transactions_last_hour: Optional[int] = Field(None, ge=0)
transactions_last_day: Optional[int] = Field(None, ge=0)
transactions_last_week: Optional[int] = Field(None, ge=0)
amount_last_hour: Optional[float] = Field(None, ge=0)
amount_last_day: Optional[float] = Field(None, ge=0)
amount_last_week: Optional[float] = Field(None, ge=0)

# Failed attempts
failed_login_attempts: Optional[int] = Field(None, ge=0)
failed_transactions_last_day: Optional[int] = Field(None, ge=0)

# Behavioral biometrics
typing_speed: Optional[float] = None
mouse_movement_pattern: Optional[str] = None
time_spent_on_page: Optional[int] = None  # seconds

# Session analysis
session_duration: Optional[int] = None
pages_visited: Optional[int] = None
# ... and more
```

#### Location & Shipping (18 fields)
```python
# User location
user_country: Optional[str] = None
user_city: Optional[str] = None
user_state: Optional[str] = None
user_postal_code: Optional[str] = None
latitude: Optional[float] = None
longitude: Optional[float] = None

# Shipping (e-commerce)
shipping_address: Optional[str] = None
shipping_city: Optional[str] = None
shipping_country: Optional[str] = None
billing_address: Optional[str] = None
address_mismatch: Optional[bool] = None
# ... and more
```

#### Payment Method (15 fields)
```python
payment_method: Optional[str] = None  # card, bank_transfer, wallet, crypto
card_bin: Optional[str] = Field(None, min_length=6, max_length=6)
card_last4: Optional[str] = Field(None, min_length=4, max_length=4)
card_type: Optional[str] = None  # debit, credit, prepaid
card_brand: Optional[str] = None  # visa, mastercard, verve
card_country: Optional[str] = None
bank_name: Optional[str] = None
account_number_hash: Optional[str] = None
# ... and more
```

#### Lending-Specific (25 fields)
```python
loan_amount: Optional[float] = Field(None, gt=0)
loan_tenure_months: Optional[int] = Field(None, gt=0)
interest_rate: Optional[float] = Field(None, ge=0)
credit_score: Optional[int] = Field(None, ge=300, le=850)
debt_to_income_ratio: Optional[float] = Field(None, ge=0)
employment_status: Optional[str] = None
monthly_income: Optional[float] = Field(None, ge=0)
existing_loans_count: Optional[int] = Field(None, ge=0)
total_debt: Optional[float] = Field(None, ge=0)
loan_purpose: Optional[str] = None
collateral_type: Optional[str] = None
# ... and more
```

#### Crypto-Specific (20 fields)
```python
wallet_address: Optional[str] = None
wallet_age_days: Optional[int] = Field(None, ge=0)
wallet_balance: Optional[float] = Field(None, ge=0)
crypto_type: Optional[str] = None  # BTC, ETH, USDT
is_mixer: Optional[bool] = None
is_exchange_wallet: Optional[bool] = None
blockchain_confirmations: Optional[int] = Field(None, ge=0)
gas_price: Optional[float] = None
smart_contract_address: Optional[str] = None
# ... and more
```

#### Betting-Specific (18 fields)
```python
bet_type: Optional[str] = None  # single, accumulator, system
odds: Optional[float] = Field(None, gt=1.0)
stake: Optional[float] = Field(None, gt=0)
potential_win: Optional[float] = Field(None, gt=0)
sport_type: Optional[str] = None
event_id: Optional[str] = None
is_live_bet: Optional[bool] = None
account_bonus_balance: Optional[float] = Field(None, ge=0)
# ... and more
```

#### E-commerce Specific (25 fields)
```python
product_id: Optional[str] = None
product_category: Optional[str] = None
product_price: Optional[float] = Field(None, gt=0)
quantity: Optional[int] = Field(None, gt=0)
cart_value: Optional[float] = Field(None, ge=0)
is_digital_goods: Optional[bool] = None
is_high_risk_item: Optional[bool] = None
shipping_method: Optional[str] = None
delivery_time_days: Optional[int] = Field(None, ge=0)
is_gift: Optional[bool] = None
discount_code: Optional[str] = None
discount_amount: Optional[float] = Field(None, ge=0)
# ... and more
```

#### Marketplace-Specific (12 fields)
```python
seller_id: Optional[str] = None
seller_rating: Optional[float] = Field(None, ge=0, le=5)
seller_total_sales: Optional[int] = Field(None, ge=0)
seller_account_age_days: Optional[int] = Field(None, ge=0)
is_verified_seller: Optional[bool] = None
buyer_id: Optional[str] = None
escrow_enabled: Optional[bool] = None
# ... and more
```

#### Risk Indicators (15 fields)
```python
is_duplicate_transaction: Optional[bool] = None
is_refund_request: Optional[bool] = None
is_chargeback_history: Optional[bool] = None
is_blacklisted_email: Optional[bool] = None
is_blacklisted_phone: Optional[bool] = None
is_blacklisted_device: Optional[bool] = None
is_suspicious_email_pattern: Optional[bool] = None
is_disposable_email: Optional[bool] = None
# ... and more
```

---

### Category 3: Response Schemas

#### TransactionCheckResponse
```python
class TransactionCheckResponse(BaseModel):
    transaction_id: str
    fraud_score: int = Field(..., ge=0, le=100)
    risk_level: str  # low, medium, high, critical
    status: str  # approved, declined, review
    flags: List[FraudFlagResponse] = []
    message: str
    timestamp: datetime
    processing_time_ms: Optional[float] = None
```

#### FraudFlagResponse
```python
class FraudFlagResponse(BaseModel):
    flag_type: str
    severity: str  # low, medium, high, critical
    score: int
    confidence: float = Field(..., ge=0, le=1)
    message: str
```

---

## Testing with curl

### Test 1: Basic Transaction (Minimal Fields)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user123",
    "amount": 50000,
    "transaction_type": "transfer",
    "industry": "fintech"
  }'
```

**Expected:** 200 OK (still returns hardcoded score=0)

---

### Test 2: E-commerce Transaction (Many Fields)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user456",
    "amount": 25000,
    "transaction_type": "purchase",
    "industry": "ecommerce",
    "email": "buyer@example.com",
    "phone": "+2348012345678",
    "ip_address": "197.210.70.1",
    "device_type": "mobile",
    "product_id": "PROD-123",
    "product_category": "electronics",
    "quantity": 1,
    "shipping_address": "123 Main St, Lagos",
    "shipping_country": "NG",
    "billing_address": "123 Main St, Lagos",
    "address_mismatch": false,
    "payment_method": "card",
    "card_bin": "539983",
    "card_type": "debit",
    "is_vpn": false,
    "account_age_days": 45
  }'
```

**Expected:** 200 OK with all fields validated

---

### Test 3: Lending Transaction (Lending-Specific Fields)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user789",
    "amount": 500000,
    "transaction_type": "loan_disbursement",
    "industry": "lending",
    "email": "borrower@example.com",
    "phone": "+2348087654321",
    "bvn": "12345678901",
    "loan_amount": 500000,
    "loan_tenure_months": 12,
    "interest_rate": 18.5,
    "credit_score": 680,
    "debt_to_income_ratio": 0.35,
    "employment_status": "employed",
    "monthly_income": 200000,
    "existing_loans_count": 2,
    "loan_purpose": "business",
    "kyc_verified": true
  }'
```

**Expected:** 200 OK

---

### Test 4: Crypto Transaction

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user999",
    "amount": 100000,
    "transaction_type": "crypto_withdrawal",
    "industry": "crypto",
    "email": "trader@example.com",
    "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "crypto_type": "ETH",
    "wallet_age_days": 120,
    "is_mixer": false,
    "is_exchange_wallet": false,
    "ip_address": "197.210.70.55",
    "is_vpn": true,
    "is_tor": false
  }'
```

**Expected:** 200 OK

---

### Test 5: Validation Error (Negative Amount)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user123",
    "amount": -1000,
    "transaction_type": "transfer",
    "industry": "fintech"
  }'
```

**Expected Response (422 Unprocessable Entity):**
```json
{
  "detail": [
    {
      "loc": ["body", "amount"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt",
      "ctx": {"limit_value": 0}
    }
  ]
}
```

---

### Test 6: Validation Error (Invalid Industry)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user123",
    "amount": 50000,
    "transaction_type": "transfer",
    "industry": "invalid_industry"
  }'
```

**Expected Response (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "industry"],
      "msg": "value is not a valid enumeration member; permitted: 'fintech', 'lending', 'crypto', 'betting', 'ecommerce', 'marketplace', 'gaming'",
      "type": "type_error.enum"
    }
  ]
}
```

---

### Test 7: Email Validation

```bash
# Invalid email
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user123",
    "amount": 50000,
    "transaction_type": "transfer",
    "industry": "fintech",
    "email": "invalid-email"
  }'
```

**Expected Response (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

### Test 8: Phone Number Validation

```bash
# Invalid phone number
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user123",
    "amount": 50000,
    "transaction_type": "transfer",
    "industry": "fintech",
    "phone": "123"
  }'
```

**Expected:** May pass (phone validation is lenient) or fail depending on validators

---

### Test 9: All Optional Fields Omitted

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "minimal",
    "amount": 1000,
    "transaction_type": "transfer",
    "industry": "fintech"
  }'
```

**Expected:** 200 OK (all other fields are optional)

---

### Test 10: Maximum Fields (Kitchen Sink)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user_max",
    "amount": 100000,
    "currency": "NGN",
    "transaction_type": "purchase",
    "industry": "ecommerce",
    "email": "test@example.com",
    "phone": "+2348012345678",
    "full_name": "John Doe",
    "ip_address": "197.210.70.1",
    "device_id": "device123",
    "device_type": "mobile",
    "browser": "Chrome",
    "os": "Android",
    "is_vpn": false,
    "is_proxy": false,
    "is_tor": false,
    "user_country": "NG",
    "user_city": "Lagos",
    "account_age_days": 90,
    "kyc_verified": true,
    "transactions_last_hour": 2,
    "transactions_last_day": 5,
    "amount_last_day": 50000,
    "product_id": "PROD-456",
    "product_category": "electronics",
    "quantity": 1,
    "shipping_country": "NG",
    "payment_method": "card",
    "card_bin": "539983",
    "card_type": "debit"
  }'
```

**Expected:** 200 OK with all fields processed

---

## Verification Tests

### Test 11: Check API Documentation

```bash
# Open in browser
http://localhost:8000/docs

# Or fetch schema
curl http://localhost:8000/openapi.json | jq '.components.schemas.TransactionCheckRequest'
```

**Expected:** Should see all 249+ fields documented in Swagger UI

---

### Test 12: Verify Field Count

```bash
python3 << 'EOF'
from app.models.schemas import TransactionCheckRequest

# Get all field names
fields = TransactionCheckRequest.model_fields
print(f"✓ Total fields in TransactionCheckRequest: {len(fields)}")

# Count required vs optional
required = [name for name, field in fields.items() if field.is_required()]
optional = [name for name, field in fields.items() if not field.is_required()]

print(f"  Required fields: {len(required)}")
print(f"  Optional fields: {len(optional)}")
print(f"\nRequired fields: {', '.join(required)}")
EOF
```

**Expected Output:**
```
✓ Total fields in TransactionCheckRequest: 249
  Required fields: 4
  Optional fields: 245

Required fields: user_id, amount, transaction_type, industry
```

---

### Test 13: Verify Enums

```bash
python3 << 'EOF'
from app.models.schemas import Industry, TransactionType

print("✓ Industries:")
for industry in Industry:
    print(f"  - {industry.value}")

print("\n✓ Transaction Types:")
for txn_type in TransactionType:
    print(f"  - {txn_type.value}")
EOF
```

---

## Troubleshooting

### Issue: `ImportError: cannot import name 'EmailStr'`

**Solution:** Install email-validator
```bash
pip install email-validator==2.1.0
```

---

### Issue: `ValueError: invalid phone number`

**Solution:** Install phonenumbers
```bash
pip install phonenumbers==8.13.26
```

---

### Issue: Schemas not updating in /docs

**Solution:** Restart uvicorn server
```bash
# Kill existing server
pkill -f uvicorn

# Restart
uvicorn app.main:app --reload
```

---

## Success Criteria

By the end of Week 3, you should have:

- ✅ Complete schemas.py with 1,141 lines
- ✅ 249+ fields in TransactionCheckRequest
- ✅ All 7 industries supported (fintech, lending, crypto, etc.)
- ✅ 22 transaction types defined
- ✅ Email and phone validation working
- ✅ All fields documented in /docs
- ✅ Validation errors working correctly
- ✅ Can send requests with minimal or maximum fields

---

## Next Week Preview

**Week 4:** Redis Service & Velocity Tracking
- Redis connection and pooling
- Velocity calculations (transactions per hour/day)
- Cache service for features
- Rate limiting support
- Basic fraud detector integration

**Dependencies to add:**
- redis
- hiredis

---

## Notes

- Week 3 completes the API contract - all possible inputs are now defined
- 249+ features organized in logical categories (identity, device, network, velocity, etc.)
- Most fields are optional - only 4 required (user_id, amount, transaction_type, industry)
- Pydantic automatically validates types, ranges, formats (email, phone, etc.)
- FastAPI uses these schemas to generate OpenAPI/Swagger documentation
- Each industry has vertical-specific fields (lending has credit_score, crypto has wallet_address, etc.)

---

## File Checklist

Week 3 files to create:
- [ ] app/models/schemas.py (complete version with 249+ fields)
- [ ] requirements.txt (in build/month_01/week_03/)

---

**End of Week 3 Guide**
