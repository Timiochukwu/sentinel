# WEEK 1: Rule Engine Foundation + First Verticals
**Days 29-35 | Month 2**

## Overview
This week builds the core fraud rule engine and implements the first set of vertical-specific rules:
- FraudRule base class for all rules
- FraudRulesEngine orchestrator with vertical filtering
- Universal rules (4 rules) - apply to all industries
- Identity verification rules (32 rules) - BVN, NIN, synthetic identity
- Device fingerprinting rules (29 rules) - device fraud, emulators

**Total Rules This Week:** 65 rules across 3 verticals

## Files to Build

```
app/services/rules/
├── __init__.py
├── base.py                       # 149 lines - FraudRule class + Engine
├── universal.py                  # 118 lines - 4 universal rules
├── identity.py                   # 621 lines - 32 identity rules
└── device.py                     # 574 lines - 29 device rules
```

**Total for Week 1:** 5 files, ~1,462 lines of code

---

## Dependencies

Create `requirements.txt` (same as Month 1 Week 4 - no new dependencies):

```
# All previous dependencies
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
alembic==1.12.1
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
email-validator==2.1.0
phonenumbers==8.13.26
redis==5.0.1
hiredis==2.2.3
```

---

## File Details

### 1. `app/services/rules/base.py` (149 lines)

**Purpose:** Base class for all fraud rules and the rule engine orchestrator

**Key Classes:**

#### FraudRule Base Class
```python
class FraudRule:
    """Base class for all fraud detection rules"""

    def __init__(self):
        self.rule_id = ""           # Unique rule identifier
        self.name = ""              # Human-readable name
        self.description = ""       # What this rule checks
        self.severity = "medium"    # low/medium/high/critical
        self.score = 0              # Points if triggered
        self.enabled = True         # Can disable rules
        self.industries = []        # Which industries this applies to

    def evaluate(self, context: dict) -> Optional[dict]:
        """
        Evaluate the rule against transaction context

        Returns:
            None if rule doesn't trigger
            dict with flag details if rule triggers
        """
        raise NotImplementedError

    def applies_to_industry(self, industry: str) -> bool:
        """Check if rule applies to given industry"""
        if not self.industries:  # Empty = applies to all
            return True
        return industry in self.industries
```

#### FraudRulesEngine
```python
class FraudRulesEngine:
    """Orchestrates all fraud detection rules"""

    def __init__(self):
        self.all_rules = []
        self._load_rules()

    def _load_rules(self):
        """Load all rules from vertical modules"""
        from .universal import UNIVERSAL_RULES
        from .identity import IDENTITY_RULES
        from .device import DEVICE_RULES

        self.all_rules = (
            UNIVERSAL_RULES +
            IDENTITY_RULES +
            DEVICE_RULES
        )

    def get_rules_for_vertical(self, industry: str) -> List[FraudRule]:
        """Get all rules applicable to an industry"""
        return [
            rule for rule in self.all_rules
            if rule.enabled and rule.applies_to_industry(industry)
        ]

    def evaluate_transaction(self, context: dict) -> List[dict]:
        """
        Run all applicable rules against transaction

        Args:
            context: Transaction data + computed features

        Returns:
            List of triggered fraud flags
        """
        industry = context.get("industry", "fintech")
        applicable_rules = self.get_rules_for_vertical(industry)

        flags = []
        for rule in applicable_rules:
            try:
                result = rule.evaluate(context)
                if result:
                    flags.append(result)
            except Exception as e:
                # Log error but continue with other rules
                print(f"Error in rule {rule.rule_id}: {e}")

        return flags
```

---

### 2. `app/services/rules/universal.py` (118 lines - 4 rules)

**Purpose:** Rules that apply to ALL industries

**Rules Implemented:**

#### Rule 1: Duplicate Transaction Detection
```python
class DuplicateTransactionRule(FraudRule):
    """Detect exact duplicate transactions within 5 minutes"""

    def __init__(self):
        self.rule_id = "UNIV-001"
        self.name = "Duplicate Transaction"
        self.severity = "high"
        self.score = 40
        self.industries = []  # Applies to all

    def evaluate(self, context):
        if context.get("is_duplicate_transaction"):
            return {
                "flag_type": "duplicate_transaction",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.95,
                "message": "Exact duplicate transaction detected within 5 minutes"
            }
        return None
```

#### Rule 2: Refund Abuse Pattern
```python
class RefundAbuseRule(FraudRule):
    """Detect excessive refund requests"""

    def __init__(self):
        self.rule_id = "UNIV-002"
        self.name = "Refund Abuse"
        self.severity = "medium"
        self.score = 25

    def evaluate(self, context):
        refund_count = context.get("refunds_last_30_days", 0)
        if refund_count >= 5:
            return {
                "flag_type": "refund_abuse",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.75,
                "message": f"{refund_count} refunds in 30 days"
            }
        return None
```

#### Rule 3: Chargeback History
```python
class ChargebackHistoryRule(FraudRule):
    """Flag users with chargeback history"""

    def __init__(self):
        self.rule_id = "UNIV-003"
        self.name = "Chargeback History"
        self.severity = "high"
        self.score = 50

    def evaluate(self, context):
        if context.get("is_chargeback_history"):
            return {
                "flag_type": "chargeback_history",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.9,
                "message": "User has previous chargeback history"
            }
        return None
```

#### Rule 4: Blacklisted User
```python
class BlacklistRule(FraudRule):
    """Check if user is on blacklist"""

    def __init__(self):
        self.rule_id = "UNIV-004"
        self.name = "Blacklisted User"
        self.severity = "critical"
        self.score = 100

    def evaluate(self, context):
        blacklist_reasons = []

        if context.get("is_blacklisted_email"):
            blacklist_reasons.append("email")
        if context.get("is_blacklisted_phone"):
            blacklist_reasons.append("phone")
        if context.get("is_blacklisted_device"):
            blacklist_reasons.append("device")

        if blacklist_reasons:
            return {
                "flag_type": "blacklisted_user",
                "severity": self.severity,
                "score": self.score,
                "confidence": 1.0,
                "message": f"Blacklisted: {', '.join(blacklist_reasons)}"
            }
        return None
```

**Export:**
```python
UNIVERSAL_RULES = [
    DuplicateTransactionRule(),
    RefundAbuseRule(),
    ChargebackHistoryRule(),
    BlacklistRule()
]
```

---

### 3. `app/services/rules/identity.py` (621 lines - 32 rules)

**Purpose:** Identity verification and synthetic identity detection

**Key Rules:**

1. **BVN Mismatch** (IDEN-001) - Score: 60
   - BVN name doesn't match provided name
   - Applies to: fintech, lending

2. **Missing BVN** (IDEN-002) - Score: 30
   - High-value transaction without BVN
   - Applies to: fintech, lending

3. **Unverified KYC** (IDEN-003) - Score: 25
   - Transaction above threshold without KYC
   - Applies to: all industries

4. **Disposable Email** (IDEN-004) - Score: 20
   - Using temporary email service
   - Applies to: all industries

5. **Suspicious Email Pattern** (IDEN-005) - Score: 15
   - Random characters, numbers only
   - Example: abc123xyz@gmail.com

6. **Email-Phone Mismatch** (IDEN-006) - Score: 20
   - Email country doesn't match phone country
   - Example: +234 phone with US email

7. **New Account High Value** (IDEN-007) - Score: 35
   - Account < 7 days old, transaction > 100k

8. **Synthetic Identity Indicators** (IDEN-008) - Score: 45
   - Multiple red flags: new account, perfect credit, VoIP phone

... and 24 more identity rules

**Sample Implementation:**
```python
class BVNMismatchRule(FraudRule):
    """Detect BVN name mismatch"""

    def __init__(self):
        self.rule_id = "IDEN-001"
        self.name = "BVN Name Mismatch"
        self.severity = "high"
        self.score = 60
        self.industries = ["fintech", "lending"]

    def evaluate(self, context):
        bvn_verified = context.get("bvn_verified")
        has_bvn = context.get("bvn") is not None

        if has_bvn and bvn_verified == False:
            return {
                "flag_type": "bvn_mismatch",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.9,
                "message": "BVN name does not match provided name"
            }
        return None
```

---

### 4. `app/services/rules/device.py` (574 lines - 29 rules)

**Purpose:** Device fingerprinting and device-based fraud detection

**Key Rules:**

1. **Emulator Detection** (DEV-001) - Score: 50
   - Transaction from Android emulator

2. **Device Fingerprint Mismatch** (DEV-002) - Score: 30
   - Device fingerprint changed mid-session

3. **Multiple Users One Device** (DEV-003) - Score: 40
   - Same device used by >5 users

4. **Incognito Mode** (DEV-004) - Score: 15
   - Browser in private/incognito mode

5. **Screen Resolution Anomaly** (DEV-005) - Score: 20
   - Resolution doesn't match device type

6. **Automation Detection** (DEV-006) - Score: 60
   - Headless browser, Selenium detected

7. **Canvas Fingerprint Spoofing** (DEV-007) - Score: 35
   - Canvas fingerprint manipulation detected

... and 22 more device rules

**Sample Implementation:**
```python
class EmulatorDetectionRule(FraudRule):
    """Detect Android emulators"""

    def __init__(self):
        self.rule_id = "DEV-001"
        self.name = "Emulator Detection"
        self.severity = "high"
        self.score = 50
        self.industries = []  # All industries

    def evaluate(self, context):
        if context.get("is_emulator"):
            return {
                "flag_type": "emulator_detected",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.85,
                "message": "Transaction from Android emulator"
            }
        return None
```

---

## Update Fraud Detector

Modify `app/core/fraud_detector.py` to use the rule engine:

```python
from app.services.rules.base import FraudRulesEngine

class FraudDetector:
    def __init__(self):
        self.redis = RedisService()
        self.rule_engine = FraudRulesEngine()  # ADD THIS

    def check_transaction(self, request: TransactionCheckRequest):
        score = 0
        flags = []

        # 1. Velocity checks (from Month 1 Week 4)
        velocity = self.redis.get_velocity(request.user_id, "1h")
        if velocity["count"] > 5:
            score += 30
            flags.append(...)

        # 2. NEW: Run rule engine
        context = self._build_context(request, velocity)
        rule_flags = self.rule_engine.evaluate_transaction(context)

        for flag in rule_flags:
            score += flag["score"]
            flags.append(flag)

        # 3. Determine risk level and status
        risk_level = self._calculate_risk_level(score)
        status = self._determine_status(score, risk_level)

        # 4. Store and return
        ...

    def _build_context(self, request, velocity):
        """Build context dict from request for rule evaluation"""
        return {
            "industry": request.industry,
            "amount": request.amount,
            "user_id": request.user_id,
            "is_duplicate_transaction": request.is_duplicate_transaction,
            "is_chargeback_history": request.is_chargeback_history,
            "is_blacklisted_email": request.is_blacklisted_email,
            "is_blacklisted_phone": request.is_blacklisted_phone,
            "is_blacklisted_device": request.is_blacklisted_device,
            "bvn": request.bvn,
            "bvn_verified": request.bvn_verified,
            "kyc_verified": request.kyc_verified,
            "account_age_days": request.account_age_days,
            "is_emulator": request.is_emulator,
            "email": request.email,
            "is_disposable_email": request.is_disposable_email,
            # ... all other fields from TransactionCheckRequest
        }
```

---

## Testing with curl

### Test 1: Universal Rule - Duplicate Transaction

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user123",
    "amount": 50000,
    "transaction_type": "transfer",
    "industry": "fintech",
    "is_duplicate_transaction": true
  }'
```

**Expected Response:**
```json
{
  "fraud_score": 40,
  "risk_level": "medium",
  "status": "review",
  "flags": [
    {
      "flag_type": "duplicate_transaction",
      "severity": "high",
      "score": 40,
      "confidence": 0.95,
      "message": "Exact duplicate transaction detected within 5 minutes"
    }
  ]
}
```

---

### Test 2: Identity Rule - BVN Mismatch

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user456",
    "amount": 200000,
    "transaction_type": "loan_disbursement",
    "industry": "lending",
    "bvn": "12345678901",
    "bvn_verified": false
  }'
```

**Expected Response:**
```json
{
  "fraud_score": 60,
  "risk_level": "high",
  "status": "review",
  "flags": [
    {
      "flag_type": "bvn_mismatch",
      "severity": "high",
      "score": 60,
      "confidence": 0.9,
      "message": "BVN name does not match provided name"
    }
  ]
}
```

---

### Test 3: Device Rule - Emulator Detection

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user789",
    "amount": 100000,
    "transaction_type": "purchase",
    "industry": "ecommerce",
    "is_emulator": true
  }'
```

**Expected Response:**
```json
{
  "fraud_score": 50,
  "risk_level": "high",
  "status": "review",
  "flags": [
    {
      "flag_type": "emulator_detected",
      "severity": "high",
      "score": 50,
      "confidence": 0.85,
      "message": "Transaction from Android emulator"
    }
  ]
}
```

---

### Test 4: Multiple Rules Triggered

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "risky_user",
    "amount": 500000,
    "transaction_type": "transfer",
    "industry": "fintech",
    "is_duplicate_transaction": true,
    "is_blacklisted_email": true,
    "is_emulator": true
  }'
```

**Expected Response:**
```json
{
  "fraud_score": 190,
  "risk_level": "critical",
  "status": "declined",
  "flags": [
    {
      "flag_type": "duplicate_transaction",
      "score": 40
    },
    {
      "flag_type": "blacklisted_user",
      "score": 100
    },
    {
      "flag_type": "emulator_detected",
      "score": 50
    }
  ]
}
```

---

### Test 5: Rule Filtering by Industry

```bash
# BVN mismatch applies to lending, not ecommerce
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user999",
    "amount": 50000,
    "transaction_type": "purchase",
    "industry": "ecommerce",
    "bvn": "12345678901",
    "bvn_verified": false
  }'
```

**Expected:** BVN mismatch rule should NOT trigger (only applies to fintech/lending)

---

## Verification Tests

### Test 6: Count Loaded Rules

```bash
python3 << 'EOF'
from app.services.rules.base import FraudRulesEngine

engine = FraudRulesEngine()
print(f"✓ Total rules loaded: {len(engine.all_rules)}")

# Count by module
from app.services.rules.universal import UNIVERSAL_RULES
from app.services.rules.identity import IDENTITY_RULES
from app.services.rules.device import DEVICE_RULES

print(f"  Universal rules: {len(UNIVERSAL_RULES)}")
print(f"  Identity rules: {len(IDENTITY_RULES)}")
print(f"  Device rules: {len(DEVICE_RULES)}")
EOF
```

**Expected Output:**
```
✓ Total rules loaded: 65
  Universal rules: 4
  Identity rules: 32
  Device rules: 29
```

---

### Test 7: Test Rule Filtering

```bash
python3 << 'EOF'
from app.services.rules.base import FraudRulesEngine

engine = FraudRulesEngine()

# Get rules for different industries
lending_rules = engine.get_rules_for_vertical("lending")
ecommerce_rules = engine.get_rules_for_vertical("ecommerce")
crypto_rules = engine.get_rules_for_vertical("crypto")

print(f"✓ Lending rules: {len(lending_rules)}")
print(f"✓ E-commerce rules: {len(ecommerce_rules)}")
print(f"✓ Crypto rules: {len(crypto_rules)}")
EOF
```

---

## Troubleshooting

### Issue: `ImportError: cannot import name 'FraudRulesEngine'`

**Solution:** Ensure `app/services/rules/__init__.py` exists (can be empty)

---

### Issue: Rules not triggering

**Solution:** Check context building in fraud_detector.py - ensure all fields from request are passed to context dict

---

### Issue: Duplicate rule IDs

**Solution:** Each rule must have unique rule_id. Check for conflicts.

---

## Success Criteria

By the end of Week 1 (Month 2), you should have:

- ✅ FraudRule base class working
- ✅ FraudRulesEngine loading 65 rules
- ✅ 4 universal rules triggering
- ✅ 32 identity rules triggering
- ✅ 29 device rules triggering
- ✅ Rules filtered by industry
- ✅ Multiple rules can trigger on same transaction
- ✅ Fraud scores accumulating correctly

---

## Next Week Preview

**Week 2:** More Rule Verticals
- Network analysis rules (41 rules) - VPN, TOR, proxy
- Behavioral biometrics rules (23 rules) - typing, mouse patterns
- Account takeover rules (5 rules) - credential stuffing
- E-commerce rules (21 rules) - shipping mismatch

**Total Week 2:** 90 rules
**Running Total:** 155 rules

---

## Notes

- Week 1 focuses on foundational rules that apply broadly
- Rule engine is extensible - easy to add new rules
- Each rule is self-contained and testable
- Scores are additive - multiple rules compound risk
- Industry filtering prevents false positives (lending rules don't trigger on crypto)

---

## File Checklist

Week 1 files to create:
- [ ] app/services/rules/__init__.py
- [ ] app/services/rules/base.py
- [ ] app/services/rules/universal.py
- [ ] app/services/rules/identity.py
- [ ] app/services/rules/device.py
- [ ] Update app/core/fraud_detector.py (add rule engine)
- [ ] requirements.txt (in build_guides/month_02/week_01/)

---

**End of Week 1 Guide - Month 2**
