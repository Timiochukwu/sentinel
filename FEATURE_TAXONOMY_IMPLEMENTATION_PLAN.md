# Complete Feature Taxonomy Implementation Plan

## Overview
Implementing 249+ fraud detection features organized into 9 categories using a JSONB-based database schema for efficient storage and querying.

## Architecture Strategy

### Why JSONB Instead of 249+ Columns?
- **Efficiency**: 9 JSONB columns vs 249+ individual columns
- **Flexibility**: Add new features without migrations
- **Queryability**: PostgreSQL JSONB supports complex queries
- **Scalability**: Easier to version features and handle optional fields
- **Performance**: Indexed JSONB paths for commonly queried features

### Implementation Phases

#### Phase 4: IDENTITY FEATURES (40 features)
**Purpose**: Establish who the user claims to be

**Database**: `identity_features` JSONB column
```python
{
  "email": {...email_data...},
  "phone": {...phone_data...},
  "bvn": {...bvn_data...},
  "device": {...device_data...},
  "network": {...network_data...}
}
```

**Features**:
- Email: address, domain, age, reputation, verification
- Phone: number, age, country, verification status
- BVN/ID: BVN, NIN, verification status
- Device: fingerprint, browser, OS, screen, timezone, installed fonts, WebGL
- Network: IP, geolocation, reputation, VPN/proxy detection

**Rules Created**: 40-50 identity-focused rules (e.g., NewEmailDomainRule, SuspiciousIPRule)

---

#### Phase 5: BEHAVIORAL FEATURES (60 features)
**Purpose**: Understand how the user behaves

**Database**: `behavioral_features` JSONB column
```python
{
  "session": {...session_metrics...},
  "login": {...login_patterns...},
  "transaction": {...txn_patterns...},
  "interaction": {...interaction_patterns...}
}
```

**Features**:
- Session: Mouse movement, typing speed, keystroke dynamics, copy/paste, session duration
- Login: Frequency, time patterns, failed attempts, velocity, 2FA usage
- Transaction: Velocity (hourly/daily/weekly), amounts, timing, frequency
- Interaction: Navigation patterns, form completion time, tab switching, scroll patterns

**Rules Created**: 50-70 behavioral rules (e.g., BotDetectionRule, UnusualLoginTimeRule)

---

#### Phase 6: TRANSACTION FEATURES (40 features)
**Purpose**: Analyze what transactions are being made

**Database**: `transaction_features` JSONB column
```python
{
  "card": {...card_data...},
  "banking": {...banking_data...},
  "address": {...address_data...},
  "crypto": {...crypto_data...},
  "merchant": {...merchant_data...}
}
```

**Features**:
- Card: BIN, last 4, expiry, country, age, reputation, testing patterns
- Banking: Account number, age, verification, velocity
- Address: Billing/shipping, distance, match
- Crypto: Wallet address, age, reputation, velocity
- Merchant: Category, fraud rate, refund rate, chargeback rate

**Rules Created**: 40-50 transaction-focused rules (e.g., CardTestingRule, NewFundingSourceRule)

---

#### Phase 7: NETWORK/CONSORTIUM FEATURES (40 features)
**Purpose**: Detect fraud rings and shared identifiers

**Database**: `network_features` JSONB column
```python
{
  "consortium_matching": {...matching_data...},
  "fraud_linkage": {...fraud_links...},
  "network_velocity": {...velocity_across_network...},
  "graph_analysis": {...network_graph_data...}
}
```

**Features**:
- Consortium Matching: Email/phone/device/IP/card/address/BVN seen elsewhere?
- Fraud Linkage: Email/phone/device/IP/card/address/BVN linked to fraud?
- Network Velocity: Velocity across email/phone/device/IP/card/BVN
- Graph Analysis: Connected accounts, fraud rings, money mules, synthetic clusters

**Rules Created**: 40-60 network rules (e.g., FraudRingDetectionRule, MoneyMuleRule)

---

#### Phase 8: ACCOUNT TAKEOVER (ATO) SIGNALS (15 features)
**Purpose**: Detect compromised accounts

**Database**: `ato_signals` JSONB column
```python
{
  "classic_patterns": {...ato_patterns...},
  "behavioral_deviation": {...behavior_changes...}
}
```

**Features**:
- Classic ATO: Password reset + transaction, failed login velocity, new device + change, impossible travel
- Behavioral Deviation: Typing, mouse movement, navigation, transaction, time-of-day changes

**Rules Created**: 20-30 ATO-specific rules (e.g., PasswordResetATORule, ImpossibleTravelRule)

---

#### Phase 9: FUNDING SOURCE FRAUD (10 features)
**Purpose**: Detect new funding source abuse

**Database**: `funding_fraud_signals` JSONB column
```python
{
  "new_sources": {...new_funding_data...},
  "card_testing": {...card_testing_data...}
}
```

**Features**:
- New Sources: New card + withdrawal, new bank account, same-day withdrawal
- Card Testing: Multiple $1 auth, small fails → large success, BIN attacks

**Rules Created**: 15-20 funding fraud rules (e.g., CardTestingRule, NewFundingWithdrawalRule)

---

#### Phase 10: MERCHANT-LEVEL ABUSE (10 features)
**Purpose**: Detect merchant-specific fraud patterns

**Database**: `merchant_abuse_signals` JSONB column
```python
{
  "merchant_risk": {...merchant_data...},
  "abuse_patterns": {...abuse_data...}
}
```

**Features**:
- Merchant Risk: Category, fraud cluster, chargeback rate, refund rate
- Abuse Patterns: Refund abuse, cashback abuse, promo abuse, loyalty abuse, referral fraud

**Rules Created**: 15-20 merchant rules (e.g., RefundAbuseRule, PromoAbuseRule)

---

#### Phase 11: ML-DERIVED FEATURES (9 features)
**Purpose**: Aggregate ML model outputs

**Database**: `ml_derived_features` JSONB column
```python
{
  "statistical_outliers": {...outlier_scores...},
  "model_scores": {...ml_scores...},
  "deep_learning": {...dl_scores...}
}
```

**Features**:
- Outliers: Behavioral deviation score, transaction anomaly, z-score
- Models: XGBoost, neural network, random forest, ensemble scores
- Deep Learning: LSTM sequence, GNN graph score, autoencoder anomaly

**Rules Created**: 10-15 ML rules (e.g., AnomalyScoreRule, EnsembleConfidenceRule)

---

#### Phase 12: DERIVED/COMPUTED FEATURES (25 features)
**Purpose**: Create final aggregate fraud signals

**Database**: `derived_features` JSONB column
```python
{
  "similarity": {...similarity_scores...},
  "linkage": {...linkage_data...},
  "clustering": {...cluster_data...},
  "aggregate_risk": {...final_scores...}
}
```

**Features**:
- Similarity: Fraudster profile, usernames, emails, addresses, behaviors
- Linkage: Entity resolution, identity matching, soft/hard linking
- Clustering: Family/business/geographic/temporal connections, community detection
- Aggregate: Final risk score, confidence, explainability, feature importance

**Rules Created**: 20-30 aggregate rules (e.g., FraudsterProfileMatchRule, RiskAggregatorRule)

---

## Database Schema Changes

### New JSONB Columns to Add
```sql
ALTER TABLE transactions ADD COLUMN identity_features JSONB;
ALTER TABLE transactions ADD COLUMN behavioral_features JSONB;
ALTER TABLE transactions ADD COLUMN transaction_features JSONB;
ALTER TABLE transactions ADD COLUMN network_features JSONB;
ALTER TABLE transactions ADD COLUMN ato_signals JSONB;
ALTER TABLE transactions ADD COLUMN funding_fraud_signals JSONB;
ALTER TABLE transactions ADD COLUMN merchant_abuse_signals JSONB;
ALTER TABLE transactions ADD COLUMN ml_derived_features JSONB;
ALTER TABLE transactions ADD COLUMN derived_features JSONB;

-- Add JSONB indexes for performance
CREATE INDEX idx_identity_features ON transactions USING GIN (identity_features);
CREATE INDEX idx_behavioral_features ON transactions USING GIN (behavioral_features);
CREATE INDEX idx_transaction_features ON transactions USING GIN (transaction_features);
CREATE INDEX idx_network_features ON transactions USING GIN (network_features);
CREATE INDEX idx_ato_signals ON transactions USING GIN (ato_signals);
CREATE INDEX idx_funding_fraud_signals ON transactions USING GIN (funding_fraud_signals);
CREATE INDEX idx_merchant_abuse_signals ON transactions USING GIN (merchant_abuse_signals);
CREATE INDEX idx_ml_derived_features ON transactions USING GIN (ml_derived_features);
CREATE INDEX idx_derived_features ON transactions USING GIN (derived_features);
```

### Pydantic Schema Updates
Create nested Pydantic models for each category:
```python
class IdentityFeatures(BaseModel):
    email: Dict[str, Any] = {}
    phone: Dict[str, Any] = {}
    bvn: Dict[str, Any] = {}
    device: Dict[str, Any] = {}
    network: Dict[str, Any] = {}

class BehavioralFeatures(BaseModel):
    session: Dict[str, Any] = {}
    login: Dict[str, Any] = {}
    transaction: Dict[str, Any] = {}
    interaction: Dict[str, Any] = {}

# ... etc for other categories

class TransactionCheckRequest(BaseModel):
    transaction_id: str
    user_id: str
    amount: float
    # ... existing fields ...

    # New: Feature category fields
    identity_features: Optional[IdentityFeatures] = None
    behavioral_features: Optional[BehavioralFeatures] = None
    transaction_features: Optional[TransactionFeatures] = None
    network_features: Optional[NetworkFeatures] = None
    ato_signals: Optional[ATOSignals] = None
    funding_fraud_signals: Optional[FundingFraudSignals] = None
    merchant_abuse_signals: Optional[MerchantAbuseSignals] = None
    ml_derived_features: Optional[MLDerivedFeatures] = None
    derived_features: Optional[DerivedFeatures] = None
```

---

## Rule Creation Strategy

### Total Rules by Phase
- Phase 4 (Identity): 40-50 rules → Total: 149-159 rules
- Phase 5 (Behavioral): 50-70 rules → Total: 199-229 rules
- Phase 6 (Transaction): 40-50 rules → Total: 239-279 rules
- Phase 7 (Network): 40-60 rules → Total: 279-339 rules
- Phase 8 (ATO): 20-30 rules → Total: 299-369 rules
- Phase 9 (Funding): 15-20 rules → Total: 314-389 rules
- Phase 10 (Merchant): 15-20 rules → Total: 329-409 rules
- Phase 11 (ML): 10-15 rules → Total: 339-424 rules
- Phase 12 (Derived): 20-30 rules → Total: 359-454 rules

**Final System**: 350-450+ fraud detection rules

### Rule Composition Patterns
1. **Simple Rules**: Single feature threshold (e.g., NewEmailDomainRule)
2. **Composite Rules**: Multiple features combined (e.g., CardTestingPatternRule)
3. **Temporal Rules**: Feature changes over time (e.g., DeviceHoppingRule)
4. **Network Rules**: Multi-entity analysis (e.g., FraudRingDetectionRule)
5. **ML Rules**: Model score-based (e.g., AnomalyScoreRule)

---

## Implementation Timeline

| Phase | Category | Features | Rules | Est. Lines | Status |
|-------|----------|----------|-------|-----------|---------|
| 4 | Identity | 40 | 45 | 2,000 | Pending |
| 5 | Behavioral | 60 | 60 | 2,500 | Pending |
| 6 | Transaction | 40 | 45 | 2,000 | Pending |
| 7 | Network | 40 | 50 | 2,500 | Pending |
| 8 | ATO | 15 | 25 | 1,500 | Pending |
| 9 | Funding | 10 | 18 | 1,000 | Pending |
| 10 | Merchant | 10 | 18 | 1,000 | Pending |
| 11 | ML | 9 | 12 | 800 | Pending |
| 12 | Derived | 25 | 25 | 1,500 | Pending |
| **TOTAL** | **9 categories** | **249 features** | **398 rules** | **14,800 lines** | **Pending** |

---

## Benefits of Complete Taxonomy

✅ **Coverage**: 350-450+ fraud detection rules
✅ **Granularity**: 249+ distinct fraud signals
✅ **Flexibility**: JSONB allows easy feature additions
✅ **Performance**: GIN indexes on JSONB columns
✅ **Scalability**: Modular category-based design
✅ **Explainability**: Clear feature categories and rule purposes
✅ **Multi-Vertical**: Works across all 8 industry verticals
✅ **85-95% Detection**: Comprehensive fraud coverage

---

## Success Criteria

- [ ] All 249 features defined in schemas
- [ ] All 9 feature category JSONB columns in database
- [ ] 350+ fraud detection rules implemented
- [ ] Comprehensive test coverage for all rules
- [ ] Feature extraction from requests working
- [ ] Database migrations ready for deployment
- [ ] Documentation of all features and rules
- [ ] Performance benchmarks for JSONB queries
