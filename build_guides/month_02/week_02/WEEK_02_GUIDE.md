# WEEK 2: More Rule Verticals
**Days 36-42 | Month 2**

## Overview
This week adds four more vertical-specific rule sets:
- Network analysis rules (41 rules) - VPN, TOR, proxy, IP reputation
- Behavioral biometrics rules (23 rules) - Mouse patterns, typing speed
- Account takeover rules (5 rules) - Credential stuffing, session hijacking
- E-commerce specific rules (21 rules) - Shipping mismatch, high-risk items

**Total Rules This Week:** 90 rules across 4 verticals
**Running Total:** 155 rules (65 from Week 1 + 90 this week)

## Files to Build

```
app/services/rules/
├── network.py                    # 778 lines - 41 network rules
├── behavioral.py                 # 426 lines - 23 behavioral rules
├── ato.py                        # 126 lines - 5 ATO rules
└── ecommerce.py                  # 574 lines - 21 ecommerce rules
```

**Total for Week 2:** 4 files, ~1,904 lines of code

---

## Dependencies

No new dependencies (same as Week 1):

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

### 1. `app/services/rules/network.py` (778 lines - 41 rules)

**Purpose:** Network analysis and IP-based fraud detection

**Key Rules:**

1. **VPN Detection** (NET-001) - Score: 25
2. **TOR Network** (NET-002) - Score: 60
3. **Proxy Detection** (NET-003) - Score: 30
4. **Datacenter IP** (NET-004) - Score: 35
5. **High Risk Country** (NET-005) - Score: 40
6. **IP Country Mismatch** (NET-006) - Score: 20
7. **IP Velocity** (NET-007) - Score: 45
8. **Shared IP Multiple Users** (NET-008) - Score: 25
9. **IP Blacklist** (NET-009) - Score: 80
10. **Unusual IP Location** (NET-010) - Score: 30

... and 31 more network rules

**Sample Implementation:**
```python
class VPNDetectionRule(FraudRule):
    """Detect VPN usage"""

    def __init__(self):
        self.rule_id = "NET-001"
        self.name = "VPN Detection"
        self.severity = "medium"
        self.score = 25
        self.industries = []  # All industries

    def evaluate(self, context):
        if context.get("is_vpn"):
            return {
                "flag_type": "vpn_detected",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.85,
                "message": "Transaction from VPN network"
            }
        return None


class TORNetworkRule(FraudRule):
    """Detect TOR browser usage"""

    def __init__(self):
        self.rule_id = "NET-002"
        self.name = "TOR Network"
        self.severity = "high"
        self.score = 60
        self.industries = []

    def evaluate(self, context):
        if context.get("is_tor"):
            return {
                "flag_type": "tor_network",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.95,
                "message": "Transaction from TOR network"
            }
        return None
```

---

### 2. `app/services/rules/behavioral.py` (426 lines - 23 rules)

**Purpose:** Behavioral biometrics and user interaction patterns

**Key Rules:**

1. **Unusual Typing Speed** (BEH-001) - Score: 20
2. **Bot-Like Mouse Movement** (BEH-002) - Score: 35
3. **Rapid Form Completion** (BEH-003) - Score: 25
4. **Copy-Paste Password** (BEH-004) - Score: 15
5. **No Mouse Movement** (BEH-005) - Score: 30
6. **Unusual Session Duration** (BEH-006) - Score: 20
7. **Time Zone Mismatch** (BEH-007) - Score: 25
8. **Night Transaction Pattern** (BEH-008) - Score: 15

... and 15 more behavioral rules

**Sample Implementation:**
```python
class UnusualTypingSpeedRule(FraudRule):
    """Detect abnormally fast typing (bot indicator)"""

    def __init__(self):
        self.rule_id = "BEH-001"
        self.name = "Unusual Typing Speed"
        self.severity = "medium"
        self.score = 20
        self.industries = []

    def evaluate(self, context):
        typing_speed = context.get("typing_speed")
        if typing_speed and typing_speed > 150:  # >150 WPM
            return {
                "flag_type": "unusual_typing_speed",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.7,
                "message": f"Typing speed {typing_speed} WPM is unusually fast"
            }
        return None


class BotLikeMouseMovementRule(FraudRule):
    """Detect bot-like mouse patterns"""

    def __init__(self):
        self.rule_id = "BEH-002"
        self.name = "Bot-Like Mouse Movement"
        self.severity = "medium"
        self.score = 35
        self.industries = []

    def evaluate(self, context):
        mouse_pattern = context.get("mouse_movement_pattern")
        if mouse_pattern == "linear" or mouse_pattern == "no_movement":
            return {
                "flag_type": "bot_like_mouse",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.75,
                "message": f"Mouse movement pattern: {mouse_pattern}"
            }
        return None
```

---

### 3. `app/services/rules/ato.py` (126 lines - 5 rules)

**Purpose:** Account takeover detection

**Key Rules:**

1. **Credential Stuffing** (ATO-001) - Score: 70
2. **Session Hijacking** (ATO-002) - Score: 80
3. **Impossible Travel** (ATO-003) - Score: 60
4. **Device Change High Value** (ATO-004) - Score: 45
5. **Password Reset Then Transaction** (ATO-005) - Score: 40

**Sample Implementation:**
```python
class CredentialStuffingRule(FraudRule):
    """Detect credential stuffing attacks"""

    def __init__(self):
        self.rule_id = "ATO-001"
        self.name = "Credential Stuffing"
        self.severity = "critical"
        self.score = 70
        self.industries = []

    def evaluate(self, context):
        failed_logins = context.get("failed_login_attempts", 0)
        if failed_logins >= 3:
            return {
                "flag_type": "credential_stuffing",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.8,
                "message": f"{failed_logins} failed login attempts"
            }
        return None


class ImpossibleTravelRule(FraudRule):
    """Detect impossible travel (login from 2 distant locations)"""

    def __init__(self):
        self.rule_id = "ATO-003"
        self.name = "Impossible Travel"
        self.severity = "critical"
        self.score = 60
        self.industries = []

    def evaluate(self, context):
        if context.get("impossible_travel_detected"):
            return {
                "flag_type": "impossible_travel",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.9,
                "message": "Login from geographically impossible location"
            }
        return None
```

---

### 4. `app/services/rules/ecommerce.py` (574 lines - 21 rules)

**Purpose:** E-commerce specific fraud patterns

**Key Rules:**

1. **Shipping Address Mismatch** (ECOM-001) - Score: 35
2. **High Risk Item** (ECOM-002) - Score: 30
3. **Digital Goods High Value** (ECOM-003) - Score: 40
4. **Multiple Shipping Addresses** (ECOM-004) - Score: 25
5. **Freight Forwarding Address** (ECOM-005) - Score: 45
6. **Quantity Anomaly** (ECOM-006) - Score: 20
7. **Rush Shipping High Value** (ECOM-007) - Score: 30
8. **Gift Card Purchase Pattern** (ECOM-008) - Score: 50

... and 13 more ecommerce rules

**Sample Implementation:**
```python
class ShippingAddressMismatchRule(FraudRule):
    """Detect shipping/billing address mismatch"""

    def __init__(self):
        self.rule_id = "ECOM-001"
        self.name = "Shipping Address Mismatch"
        self.severity = "medium"
        self.score = 35
        self.industries = ["ecommerce", "marketplace"]

    def evaluate(self, context):
        if context.get("address_mismatch"):
            return {
                "flag_type": "address_mismatch",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.7,
                "message": "Shipping and billing addresses do not match"
            }
        return None


class HighRiskItemRule(FraudRule):
    """Flag high-risk product categories"""

    def __init__(self):
        self.rule_id = "ECOM-002"
        self.name = "High Risk Item"
        self.severity = "medium"
        self.score = 30
        self.industries = ["ecommerce"]

    def evaluate(self, context):
        if context.get("is_high_risk_item"):
            product_category = context.get("product_category", "unknown")
            return {
                "flag_type": "high_risk_item",
                "severity": self.severity,
                "score": self.score,
                "confidence": 0.65,
                "message": f"High-risk category: {product_category}"
            }
        return None
```

---

## Update Rule Engine

Modify `app/services/rules/base.py` to load new rules:

```python
def _load_rules(self):
    """Load all rules from vertical modules"""
    from .universal import UNIVERSAL_RULES
    from .identity import IDENTITY_RULES
    from .device import DEVICE_RULES
    # NEW: Add these imports
    from .network import NETWORK_RULES
    from .behavioral import BEHAVIORAL_RULES
    from .ato import ATO_RULES
    from .ecommerce import ECOMMERCE_RULES

    self.all_rules = (
        UNIVERSAL_RULES +
        IDENTITY_RULES +
        DEVICE_RULES +
        NETWORK_RULES +      # NEW
        BEHAVIORAL_RULES +   # NEW
        ATO_RULES +          # NEW
        ECOMMERCE_RULES      # NEW
    )
```

---

## Testing with curl

### Test 1: VPN Detection

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user123",
    "amount": 50000,
    "transaction_type": "transfer",
    "industry": "fintech",
    "is_vpn": true,
    "ip_address": "1.2.3.4"
  }'
```

**Expected:**
```json
{
  "fraud_score": 25,
  "flags": [
    {
      "flag_type": "vpn_detected",
      "score": 25,
      "message": "Transaction from VPN network"
    }
  ]
}
```

---

### Test 2: TOR Network (High Risk)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user456",
    "amount": 100000,
    "transaction_type": "withdrawal",
    "industry": "crypto",
    "is_tor": true
  }'
```

**Expected:**
```json
{
  "fraud_score": 60,
  "risk_level": "high",
  "status": "review",
  "flags": [
    {
      "flag_type": "tor_network",
      "score": 60,
      "severity": "high"
    }
  ]
}
```

---

### Test 3: Credential Stuffing

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "user789",
    "amount": 75000,
    "transaction_type": "transfer",
    "industry": "fintech",
    "failed_login_attempts": 5
  }'
```

**Expected:**
```json
{
  "fraud_score": 70,
  "risk_level": "critical",
  "status": "declined",
  "flags": [
    {
      "flag_type": "credential_stuffing",
      "score": 70,
      "message": "5 failed login attempts"
    }
  ]
}
```

---

### Test 4: E-commerce Address Mismatch

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "buyer001",
    "amount": 150000,
    "transaction_type": "purchase",
    "industry": "ecommerce",
    "address_mismatch": true,
    "is_high_risk_item": true
  }'
```

**Expected:**
```json
{
  "fraud_score": 65,
  "risk_level": "high",
  "status": "review",
  "flags": [
    {
      "flag_type": "address_mismatch",
      "score": 35
    },
    {
      "flag_type": "high_risk_item",
      "score": 30
    }
  ]
}
```

---

### Test 5: Behavioral - Bot Detection

```bash
curl -X POST http://localhost:8000/api/v1/fraud/check \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "user_id": "bot_user",
    "amount": 25000,
    "transaction_type": "purchase",
    "industry": "ecommerce",
    "typing_speed": 200,
    "mouse_movement_pattern": "linear"
  }'
```

**Expected:**
```json
{
  "fraud_score": 55,
  "risk_level": "high",
  "flags": [
    {
      "flag_type": "unusual_typing_speed",
      "score": 20
    },
    {
      "flag_type": "bot_like_mouse",
      "score": 35
    }
  ]
}
```

---

## Verification Tests

### Test 6: Count All Rules

```bash
python3 << 'EOF'
from app.services.rules.base import FraudRulesEngine

engine = FraudRulesEngine()
print(f"✓ Total rules loaded: {len(engine.all_rules)}")

# Should be 155 rules (65 from Week 1 + 90 from Week 2)
assert len(engine.all_rules) == 155, f"Expected 155 rules, got {len(engine.all_rules)}"
print("✓ Rule count verified!")
EOF
```

---

### Test 7: Verify E-commerce Rules Only Apply to E-commerce

```bash
python3 << 'EOF'
from app.services.rules.base import FraudRulesEngine

engine = FraudRulesEngine()

# E-commerce rules should apply to ecommerce industry
ecommerce_rules = engine.get_rules_for_vertical("ecommerce")
ecommerce_specific = [r for r in ecommerce_rules if "ecommerce" in r.industries]

print(f"✓ E-commerce specific rules: {len(ecommerce_specific)}")

# Crypto shouldn't get ecommerce-specific rules
crypto_rules = engine.get_rules_for_vertical("crypto")
crypto_ecommerce = [r for r in crypto_rules if r.industries == ["ecommerce"]]

print(f"✓ E-commerce rules in crypto: {len(crypto_ecommerce)} (should be 0)")
assert len(crypto_ecommerce) == 0
EOF
```

---

## Success Criteria

By the end of Week 2 (Month 2), you should have:

- ✅ 155 total rules loaded (65 + 90)
- ✅ Network rules detecting VPN/TOR/Proxy
- ✅ Behavioral rules detecting bots
- ✅ ATO rules detecting credential stuffing
- ✅ E-commerce rules detecting shipping fraud
- ✅ Rules properly filtered by industry
- ✅ Multiple rules triggering correctly

---

## Next Week Preview

**Week 3:** Lending & Vertical-Specific Rules
- Lending rules (89 rules) - Loan stacking, income verification
- Crypto rules (8 rules) - Mixer usage, high-risk wallets
- Betting rules (16 rules) - Bonus abuse, arbitrage
- Marketplace rules (3 rules)
- Fintech rules (2 rules)

**Total Week 3:** 118 rules
**Running Total:** 273 rules

---

## File Checklist

Week 2 files to create:
- [ ] app/services/rules/network.py
- [ ] app/services/rules/behavioral.py
- [ ] app/services/rules/ato.py
- [ ] app/services/rules/ecommerce.py
- [ ] Update app/services/rules/base.py (add new imports)
- [ ] requirements.txt (in build_guides/month_02/week_02/)

---

**End of Week 2 Guide - Month 2**
