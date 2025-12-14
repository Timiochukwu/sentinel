# WEEK 3: Lending & Vertical-Specific Rules
**Days 43-49 | Month 2**

## Overview
This week completes the rule engine with industry-specific rules:
- Lending rules (89 rules) - Loan stacking, debt ratios, income verification
- Crypto rules (8 rules) - Mixer usage, high-risk wallets
- Betting rules (16 rules) - Bonus abuse, multi-accounting
- Marketplace rules (3 rules) - Seller reputation
- Fintech rules (2 rules) - SIM swap, P2P velocity

**Total Rules This Week:** 118 rules across 5 verticals
**Running Total:** 273 rules (all rules complete!)

## Files to Build

```
app/services/rules/
├── lending.py                    # 1,826 lines - 89 lending rules
├── crypto.py                     # 234 lines - 8 crypto rules
├── betting.py                    # 442 lines - 16 betting rules
├── marketplace.py                # 98 lines - 3 marketplace rules
└── fintech.py                    # 82 lines - 2 fintech rules
```

**Total for Week 3:** 5 files, ~2,682 lines of code

---

## Dependencies

No new dependencies:

```
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

### 1. `app/services/rules/lending.py` (1,826 lines - 89 rules)

**Purpose:** Comprehensive lending fraud detection

**Key Rule Categories:**

**Credit & Income Verification (20 rules)**
1. **Low Credit Score** (LEND-001) - Score: 40
2. **High Debt-to-Income** (LEND-002) - Score: 35
3. **Unverified Income** (LEND-003) - Score: 30
4. **Income Mismatch** (LEND-004) - Score: 45
5. **Unemployed Applicant** (LEND-005) - Score: 50

**Loan Stacking Detection (15 rules)**
6. **Multiple Loan Applications** (LEND-006) - Score: 60
7. **Concurrent Loans** (LEND-007) - Score: 55
8. **Recent Loan Rejection** (LEND-008) - Score: 40

**Application Fraud (20 rules)**
9. **Synthetic Identity Indicators** (LEND-009) - Score: 70
10. **Fake Employment** (LEND-010) - Score: 80
11. **Inconsistent Information** (LEND-011) - Score: 45

**Behavioral Patterns (15 rules)**
12. **First Transaction Loan** (LEND-012) - Score: 35
13. **High Loan-to-Income Ratio** (LEND-013) - Score: 40
14. **Rush Application** (LEND-014) - Score: 25

... and 75 more lending rules

**Sample Implementations:**
```python
class LowCreditScoreRule(FraudRule):
    """Flag low credit scores"""

    def __init__(self):
        self.rule_id = "LEND-001"
        self.name = "Low Credit Score"
        self.severity = "medium"
        self.score = 40
        self.industries = ["lending"]

    def evaluate(self, context):
        credit_score = context.get("credit_score")
        if credit_score and credit_score < 550:
            return {
                "flag_type": "low_credit_score",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.85,
                "message": f"Credit score {credit_score} below acceptable threshold"
            }
        return None


class LoanStackingRule(FraudRule):
    """Detect loan stacking (multiple concurrent applications)"""

    def __init__(self):
        self.rule_id = "LEND-006"
        self.name = "Loan Stacking"
        self.severity": "critical"
        self.score = 60
        self.industries = ["lending"]

    def evaluate(self, context):
        existing_loans = context.get("existing_loans_count", 0)
        if existing_loans >= 3:
            return {
                "flag_type": "loan_stacking",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.9,
                "message": f"{existing_loans} active loans detected"
            }
        return None
```

---

### 2. `app/services/rules/crypto.py` (234 lines - 8 rules)

**Purpose:** Cryptocurrency fraud detection

**Key Rules:**

1. **Mixer/Tumbler Usage** (CRYPTO-001) - Score: 80
2. **High-Risk Wallet** (CRYPTO-002) - Score: 60
3. **New Wallet High Value** (CRYPTO-003) - Score: 45
4. **Rapid Conversions** (CRYPTO-004) - Score: 35
5. **Sanctioned Wallet** (CRYPTO-005) - Score: 100
6. **Smart Contract Risk** (CRYPTO-006) - Score: 40
7. **Unusual Gas Price** (CRYPTO-007) - Score: 25
8. **Exchange Hopping** (CRYPTO-008) - Score: 30

**Sample Implementation:**
```python
class MixerUsageRule(FraudRule):
    """Detect cryptocurrency mixer/tumbler usage"""

    def __init__(self):
        self.rule_id = "CRYPTO-001"
        self.name = "Mixer/Tumbler Usage"
        self.severity = "critical"
        self.score = 80
        self.industries = ["crypto"]

    def evaluate(self, context):
        if context.get("is_mixer"):
            return {
                "flag_type": "mixer_usage",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.95,
                "message": "Transaction involves cryptocurrency mixer"
            }
        return None
```

---

### 3. `app/services/rules/betting.py` (442 lines - 16 rules)

**Purpose:** Sports betting and gambling fraud

**Key Rules:**

1. **Bonus Abuse** (BET-001) - Score: 50
2. **Multi-Accounting** (BET-002) - Score: 70
3. **Arbitrage Betting** (BET-003) - Score: 40
4. **Unusual Betting Pattern** (BET-004) - Score: 35
5. **Late Bet Placement** (BET-005) - Score: 45
6. **Automated Betting** (BET-006) - Score: 60
7. **Gnoming Detection** (BET-007) - Score: 55
8. **Steam Chasing** (BET-008) - Score: 30

... and 8 more betting rules

**Sample Implementation:**
```python
class BonusAbuseRule(FraudRule):
    """Detect bonus abuse patterns"""

    def __init__(self):
        self.rule_id = "BET-001"
        self.name = "Bonus Abuse"
        self.severity = "high"
        self.score = 50
        self.industries = ["betting", "gaming"]

    def evaluate(self, context):
        bonus_claims = context.get("bonus_claims_count", 0)
        if bonus_claims >= 3:
            return {
                "flag_type": "bonus_abuse",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.8,
                "message": f"{bonus_claims} bonus claims in short period"
            }
        return None
```

---

### 4. `app/services/rules/marketplace.py` (98 lines - 3 rules)

**Purpose:** P2P marketplace fraud

**Key Rules:**

1. **Low Seller Reputation** (MARKET-001) - Score: 30
2. **Buyer-Seller Collusion** (MARKET-002) - Score: 60
3. **Price Manipulation** (MARKET-003) - Score: 40

**Sample Implementation:**
```python
class LowSellerReputationRule(FraudRule):
    """Flag transactions with low-reputation sellers"""

    def __init__(self):
        self.rule_id = "MARKET-001"
        self.name = "Low Seller Reputation"
        self.severity = "medium"
        self.score = 30
        self.industries = ["marketplace"]

    def evaluate(self, context):
        seller_rating = context.get("seller_rating")
        if seller_rating and seller_rating < 2.0:
            return {
                "flag_type": "low_seller_reputation",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.7,
                "message": f"Seller rating: {seller_rating}/5.0"
            }
        return None
```

---

### 5. `app/services/rules/fintech.py` (82 lines - 2 rules)

**Purpose:** Fintech-specific patterns not covered elsewhere

**Key Rules:**

1. **SIM Swap Detection** (FINT-001) - Score: 70
2. **P2P High Velocity** (FINT-002) - Score: 45

**Sample Implementation:**
```python
class SIMSwapRule(FraudRule):
    """Detect recent SIM swap fraud"""

    def __init__(self):
        self.rule_id = "FINT-001"
        self.name = "SIM Swap Detection"
        self.severity = "critical"
        self.score = 70
        self.industries = ["fintech", "lending"]

    def evaluate(self, context):
        if context.get("sim_swap_detected"):
            return {
                "flag_type": "sim_swap",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.9,
                "message": "Recent SIM card change detected"
            }
        return None
```

---

## Update Rule Engine (Final Version)

Modify `app/services/rules/base.py` with ALL rule imports:

```python
def _load_rules(self):
    """Load all 273 rules from vertical modules"""
    from .universal import UNIVERSAL_RULES
    from .identity import IDENTITY_RULES
    from .device import DEVICE_RULES
    from .network import NETWORK_RULES
    from .behavioral import BEHAVIORAL_RULES
    from .ato import ATO_RULES
    from .ecommerce import ECOMMERCE_RULES
    # NEW: Final batch
    from .lending import LENDING_RULES
    from .crypto import CRYPTO_RULES
    from .betting import BETTING_RULES
    from .marketplace import MARKETPLACE_RULES
    from .fintech import FINTECH_RULES

    self.all_rules = (
        UNIVERSAL_RULES +
        IDENTITY_RULES +
        DEVICE_RULES +
        NETWORK_RULES +
        BEHAVIORAL_RULES +
        ATO_RULES +
        ECOMMERCE_RULES +
        LENDING_RULES +       # NEW
        CRYPTO_RULES +        # NEW
        BETTING_RULES +       # NEW
        MARKETPLACE_RULES +   # NEW
        FINTECH_RULES         # NEW
    )
```

---

## Testing with curl

### Test 1: Lending - Low Credit Score

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "borrower001",
    "amount": 500000,
    "transaction_type": "loan_disbursement",
    "industry": "lending",
    "credit_score": 480,
    "debt_to_income_ratio": 0.65
  }'
```

**Expected:**
```json
{
  "fraud_score": 75,
  "risk_level": "critical",
  "status": "declined",
  "flags": [
    {
      "flag_type": "low_credit_score",
      "score": 40
    },
    {
      "flag_type": "high_debt_to_income",
      "score": 35
    }
  ]
}
```

---

### Test 2: Crypto - Mixer Usage

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "crypto_user",
    "amount": 1000000,
    "transaction_type": "crypto_withdrawal",
    "industry": "crypto",
    "is_mixer": true,
    "wallet_address": "0x123..."
  }'
```

**Expected:**
```json
{
  "fraud_score": 80,
  "risk_level": "critical",
  "status": "declined",
  "flags": [
    {
      "flag_type": "mixer_usage",
      "score": 80,
      "severity": "critical"
    }
  ]
}
```

---

### Test 3: Betting - Bonus Abuse

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "bettor001",
    "amount": 50000,
    "transaction_type": "bonus_claim",
    "industry": "betting",
    "bonus_claims_count": 5
  }'
```

**Expected:**
```json
{
  "fraud_score": 50,
  "risk_level": "high",
  "flags": [
    {
      "flag_type": "bonus_abuse",
      "score": 50
    }
  ]
}
```

---

## Verification Tests

### Test 4: Verify All 273 Rules Loaded

```bash
python3 << 'EOF'
from app.services.rules.base import FraudRulesEngine

engine = FraudRulesEngine()
total_rules = len(engine.all_rules)

print(f"✓ Total rules loaded: {total_rules}")
assert total_rules == 273, f"Expected 273 rules, got {total_rules}"

# Count by vertical
from app.services.rules.lending import LENDING_RULES
from app.services.rules.crypto import CRYPTO_RULES
from app.services.rules.betting import BETTING_RULES

print(f"  Lending rules: {len(LENDING_RULES)}")
print(f"  Crypto rules: {len(CRYPTO_RULES)}")
print(f"  Betting rules: {len(BETTING_RULES)}")

print("\n✓ All 273 rules loaded successfully!")
EOF
```

---

### Test 5: Verify Industry Filtering

```bash
python3 << 'EOF'
from app.services.rules.base import FraudRulesEngine

engine = FraudRulesEngine()

industries = ["lending", "crypto", "betting", "ecommerce", "fintech", "marketplace", "gaming"]

for industry in industries:
    rules = engine.get_rules_for_vertical(industry)
    print(f"{industry:12} - {len(rules):3} applicable rules")
EOF
```

**Expected Output:**
```
lending      - 150 applicable rules
crypto       -  75 applicable rules
betting      -  85 applicable rules
ecommerce    - 120 applicable rules
fintech      - 140 applicable rules
marketplace  -  95 applicable rules
gaming       -  80 applicable rules
```

---

## Success Criteria

By the end of Week 3 (Month 2), you should have:

- ✅ All 273 fraud detection rules loaded
- ✅ 89 lending rules working
- ✅ 8 crypto rules working
- ✅ 16 betting rules working
- ✅ 3 marketplace rules working
- ✅ 2 fintech rules working
- ✅ Industry-specific rules only trigger for correct industries
- ✅ Rule engine complete and production-ready

---

## Next Week Preview

**Week 4:** Feature Storage & Aggregation
- Feature storage service (JSONB in PostgreSQL)
- Feature aggregation and retrieval
- Historical feature tracking
- Integration with fraud detector

**Files:**
- app/services/feature_storage.py (285 lines)
- app/services/feature_aggregation.py (420 lines)

---

## Notes

- Week 3 completes the rule engine - all 273 rules are now implemented
- Lending rules are the most numerous (89 rules) due to complexity of loan fraud
- Each industry has specialized rules that only apply to that vertical
- Rules can be enabled/disabled individually for A/B testing
- Rule scores and thresholds are configurable

---

## File Checklist

Week 3 files to create:
- [ ] app/services/rules/lending.py
- [ ] app/services/rules/crypto.py
- [ ] app/services/rules/betting.py
- [ ] app/services/rules/marketplace.py
- [ ] app/services/rules/fintech.py
- [ ] Update app/services/rules/base.py (add final imports)
- [ ] requirements.txt (in build_guides/month_02/week_03/)

---

**End of Week 3 Guide - Month 2 | 273 Rules Complete! 🎉**
