# Data Sources Guide for Sentinel

## Where to Get Data for Testing & Training

---

## 🎯 Quick Answer

You have **4 main options**:

1. **Generate Synthetic Data** (fastest, start today)
2. **Use Public Datasets** (for ML training)
3. **Partner with Early Customers** (real data, best quality)
4. **Create Sample Transactions** (for demo purposes)

Let me explain each option in detail:

---

## 1. Generate Synthetic Data (RECOMMENDED TO START)

### Why Synthetic Data?
- ✅ **Immediate**: Start testing today
- ✅ **Privacy-Safe**: No real customer PII
- ✅ **Controlled**: You control fraud rates, patterns
- ✅ **Scalable**: Generate millions of transactions
- ✅ **Free**: No data licensing costs

### I'll Build a Data Generator for You

Let me create a Python script that generates realistic Nigerian fraud data:

**Script**: `scripts/generate_synthetic_data.py`

**Features**:
- Generates realistic Nigerian transactions
- Mix of fintech, e-commerce, betting, crypto, marketplace
- Realistic fraud patterns (loan stacking, SIM swap, bonus abuse)
- Configurable fraud rate (5-20%)
- Outputs labeled data (fraud = true/false)
- Nigerian-specific details (BVN, phone numbers, IP addresses)

**Usage**:
```bash
# Generate 10,000 transactions with 10% fraud rate
python scripts/generate_synthetic_data.py --count 10000 --fraud-rate 0.10

# Output: synthetic_transactions_10000.csv
```

**What You Get**:
- 10,000 transactions with realistic patterns
- ~1,000 fraudulent transactions (10%)
- ~9,000 legitimate transactions (90%)
- All fields populated (amounts, devices, IPs, etc.)
- Ready to test API and train ML models

---

## 2. Use Public Datasets

### 2a. Credit Card Fraud Detection Dataset
**Source**: Kaggle
**URL**: https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud

**Details**:
- 284,807 transactions
- 492 frauds (0.17% fraud rate)
- European credit card data (2013)
- Anonymous PCA-transformed features

**How to Use**:
```python
# Download from Kaggle, then:
import pandas as pd

df = pd.read_csv('creditcard.csv')

# Map to Sentinel format
transactions = []
for idx, row in df.iterrows():
    transactions.append({
        'transaction_id': f'cc_{idx}',
        'user_id': f'user_{hash(row["V1"]) % 10000}',
        'amount': row['Amount'] * 500,  # Convert to Naira
        'transaction_type': 'purchase',
        'industry': 'ecommerce',
        'is_fraud': row['Class'] == 1  # Label
    })
```

**Pros**:
- Real fraud patterns
- Large dataset
- Well-documented

**Cons**:
- Not Nigerian data
- Credit card only (not loans, betting, crypto)
- Need to adapt to Sentinel schema

---

### 2b. Synthetic Financial Datasets
**Source**: IBM Transactions for Anti Money Laundering (AML)
**URL**: https://www.kaggle.com/datasets/ealtman2019/ibm-transactions-for-anti-money-laundering-aml

**Details**:
- Synthetic banking transactions
- Money laundering patterns
- Multiple account types

**Use for**: Training ML models on money laundering detection (betting without wagering, etc.)

---

### 2c. E-commerce Transaction Dataset
**Source**: IEEE-CIS Fraud Detection
**URL**: https://www.kaggle.com/competitions/ieee-fraud-detection

**Details**:
- Real e-commerce fraud data
- 590,540 transactions
- Card payments, digital wallets
- Rich feature set (device info, transaction amounts, etc.)

**Use for**: Training e-commerce fraud rules

---

## 3. Partner with Early Customers (BEST QUALITY)

### Strategy: Beta Program

**Approach**:
1. Offer **free fraud detection** for 3 months
2. In exchange: Access to **anonymized transaction data**
3. Use data to train ML models
4. Share insights with beta customers

**Target Beta Customers**:

#### Fintech/Lending (Priority 1)
- **Carbon** (digital lending)
- **FairMoney** (loans)
- **Branch** (loans)
- **Renmoney** (loans)
- **PalmPay** (payments + loans)

**Pitch**: "We'll detect fraud for free. You just share anonymized data."

#### E-commerce (Priority 2)
- **Konga** sellers
- **Jumia** sellers
- **Paystack** merchants
- **Flutterwave** merchants

**Pitch**: "Reduce chargebacks by 30%. Free for first 3 months."

#### Betting (Priority 3)
- **Bet9ja**
- **SportyBet**
- **1xBet Nigeria**
- **NairaBet**

**Pitch**: "Stop bonus abuse and multi-accounting. Free trial."

#### Crypto (Priority 4)
- **Quidax**
- **Luno Nigeria**
- **Busha**
- **Yellow Card**

**Pitch**: "Block P2P scams and suspicious wallets. Free pilot."

---

### Data Sharing Agreement

**What You Need from Beta Customers**:

```
Beta Partner Data Sharing Agreement

1. Customer provides:
   - Historical transaction data (6-12 months)
   - Real-time transaction feed
   - Fraud labels (confirmed fraud cases)
   - Outcome feedback (false positives, etc.)

2. Sentinel provides:
   - Free fraud detection API (3 months)
   - Custom rule tuning
   - Weekly fraud reports
   - Dedicated support

3. Data Privacy:
   - All PII hashed (SHA-256)
   - Data used only for ML training
   - No data shared with competitors
   - NDPR compliant
```

**How to Approach**:

Email template:
```
Subject: Free Fraud Detection for [Company] (3-Month Beta)

Hi [Name],

I'm building Sentinel, a fraud detection platform for Nigerian businesses.

We're offering FREE fraud detection for 3 months to 5 early partners.

What you get:
✅ Real-time fraud API (85%+ accuracy)
✅ Detect loan stacking, SIM swap, bonus abuse
✅ Save ₦X million in fraud losses
✅ No upfront cost

What we need:
- Anonymized transaction data for ML training
- Feedback on false positives

Interested? Let's chat.

[Your Name]
Founder, Sentinel
sentinel-fraud.com
```

---

## 4. Create Sample Transactions (For Demos)

### Manual Sample Data

For demos and documentation, create hand-crafted examples:

**File**: `scripts/sample_transactions.json`

```json
{
  "legitimate_transactions": [
    {
      "transaction_id": "demo_legit_001",
      "user_id": "good_user_123",
      "amount": 25000,
      "transaction_type": "loan_disbursement",
      "industry": "lending",
      "device_id": "samsung_xyz",
      "ip_address": "197.210.52.34",
      "account_age_days": 180,
      "transaction_count": 15,
      "phone_changed_recently": false,
      "email_changed_recently": false,
      "is_fraud": false
    }
  ],

  "fraudulent_transactions": [
    {
      "transaction_id": "demo_fraud_001",
      "user_id": "fraudster_456",
      "amount": 500000,
      "transaction_type": "loan_disbursement",
      "industry": "lending",
      "device_id": "new_device_001",
      "ip_address": "41.58.123.45",  # VPN IP
      "account_age_days": 2,  # New account
      "transaction_count": 0,  # First transaction
      "phone_changed_recently": true,  # SIM swap!
      "email_changed_recently": false,
      "is_fraud": true,

      "fraud_flags": [
        "new_account_large_amount",
        "sim_swap_pattern",
        "vpn_proxy",
        "maximum_first_transaction"
      ]
    },

    {
      "transaction_id": "demo_fraud_002",
      "user_id": "loan_stacker_789",
      "amount": 200000,
      "transaction_type": "loan_disbursement",
      "industry": "lending",
      "device_id": "shared_device_003",
      "ip_address": "102.89.45.67",
      "account_age_days": 5,
      "transaction_count": 1,
      "consortium_data": {
        "client_count": 4,  # Applied to 4 other lenders!
        "lenders": ["Lender A", "Lender B", "Lender C", "Lender D"]
      },
      "is_fraud": true,

      "fraud_flags": [
        "loan_stacking"
      ]
    }
  ]
}
```

---

## 5. Nigerian-Specific Data Sources

### Nigerian Phone Numbers
**Pattern**: +234 followed by 10 digits
**Operators**:
- MTN: +234 803, 806, 810, 813, 814, 816, 903, 906
- Airtel: +234 802, 808, 812, 902, 907, 912
- Glo: +234 805, 807, 811, 815, 905
- 9mobile: +234 809, 817, 818, 909

### Nigerian IP Address Ranges
**Common ISPs**:
- MTN Nigeria: 41.58.0.0/16, 105.112.0.0/16
- Airtel Nigeria: 197.210.0.0/16
- Glo: 105.113.0.0/16
- Spectranet: 105.117.0.0/16

### BVN Format
- 11 digits
- Example: 22234567890
- **Note**: Hash before storing!

### Nigerian Banks
- GTBank, Access Bank, Zenith Bank, First Bank, UBA, etc.
- Bank codes: 058 (GTBank), 044 (Access), 057 (Zenith)

---

## 🛠️ Tools I'll Build For You

### Tool 1: Synthetic Data Generator
**File**: `scripts/generate_synthetic_data.py`

**Features**:
- Generate N transactions with configurable fraud rate
- Realistic Nigerian data (phone numbers, IPs, BVNs)
- All 5 industries (fintech, ecommerce, betting, crypto, marketplace)
- Realistic fraud patterns
- Output formats: CSV, JSON, SQL

**Command**:
```bash
python scripts/generate_synthetic_data.py \
  --count 50000 \
  --fraud-rate 0.08 \
  --industries fintech,ecommerce,betting \
  --output synthetic_data.csv
```

---

### Tool 2: Public Dataset Converter
**File**: `scripts/convert_public_datasets.py`

**Features**:
- Download Kaggle datasets
- Convert to Sentinel schema
- Map features to fraud rules
- Add Nigerian context

**Command**:
```bash
python scripts/convert_public_datasets.py \
  --source kaggle:creditcardfraud \
  --output converted_fraud_data.csv
```

---

### Tool 3: Data Quality Validator
**File**: `scripts/validate_data.py`

**Features**:
- Check data completeness
- Validate field formats (phone, BVN, IP)
- Detect data quality issues
- Generate data quality report

**Command**:
```bash
python scripts/validate_data.py \
  --input my_transaction_data.csv \
  --report data_quality_report.html
```

---

## 📈 Data Collection Strategy (Timeline)

### Week 1-2: Synthetic Data
- Generate 50,000 synthetic transactions
- Test all fraud rules
- Train initial ML model
- Achieve 70-75% accuracy (baseline)

### Week 3-4: Public Datasets
- Import Kaggle credit card fraud data
- Import IEEE e-commerce fraud data
- Retrain ML model
- Achieve 80-82% accuracy

### Month 2-3: Beta Customers
- Sign 3-5 beta partners
- Collect 100k+ real transactions
- Get fraud labels
- Retrain ML model
- Achieve 85%+ accuracy

### Month 4+: Production
- 10+ paying customers
- Millions of transactions
- Continuous learning
- 90%+ accuracy

---

## 🎓 ML Training Strategy

### Training Data Requirements

**Minimum (to start)**:
- 10,000 transactions (synthetic)
- 10% fraud rate (1,000 frauds)
- All 64 ML features populated

**Good (for production)**:
- 100,000 transactions (real + synthetic)
- 5-10% fraud rate
- Fraud labels from customers

**Excellent (for enterprise)**:
- 1,000,000+ transactions (real)
- Actual fraud outcomes
- Multiple industries
- Continuous retraining

---

### Training Script

**File**: `scripts/ml/train_model.py` (already exists!)

**Usage**:
```bash
# Train on synthetic data
python scripts/ml/train_model.py \
  --data synthetic_data.csv \
  --output models/fraud_model.json

# Train on real data
python scripts/ml/train_model.py \
  --data production_data.csv \
  --test-size 0.2 \
  --output models/fraud_model_v2.json
```

---

## 🤝 Getting Your First Beta Customer

### Step-by-Step Process

**1. Build Credibility**:
- Show working demo (use synthetic data)
- Share accuracy metrics (70-75% with synthetic, 85%+ with real data)
- Share fraud detection examples

**2. Target Right Customers**:
- Start with **small digital lenders** (more agile)
- Or **Paystack/Flutterwave merchants** (they have fraud problems)
- Avoid big banks initially (slow decision-making)

**3. Offer No-Risk Trial**:
- 3 months free
- No integration required (you can call their API)
- Just need data export

**4. Show Quick Wins**:
- Week 1: Detect 10 fraud cases they missed
- Week 2: Prevent ₦1M in fraud losses
- Week 3: They're convinced

**5. Convert to Paid**:
- After 3 months, convert to paid ($500-$2,000/month)
- If they say no, find out why and improve

---

## 💾 Data Storage & Privacy

### Where to Store Data

**Development**:
- Local PostgreSQL database
- CSV files for backups

**Production**:
- Cloud database (AWS RDS, Google Cloud SQL)
- Encrypted at rest (AES-256)
- Encrypted in transit (TLS 1.3)

### Privacy Best Practices

**1. Hash All PII**:
```python
import hashlib

def hash_pii(value: str) -> str:
    """Hash sensitive data (BVN, phone, email)"""
    return hashlib.sha256(value.encode()).hexdigest()

# Store hashed version only
bvn_hash = hash_pii("22234567890")
```

**2. Anonymize User IDs**:
```python
# Don't store: "john.doe@gmail.com"
# Store: "user_7f8a9b2c"
```

**3. Data Retention Policy**:
- Keep transaction data for 7 years (fraud investigation)
- Auto-delete after 7 years
- Allow users to request deletion (GDPR/NDPR)

**4. Access Controls**:
- Only authorized personnel access production data
- Audit logs for all data access
- No data export without approval

---

## 🎯 Quick Start Guide

### Option 1: Start Today with Synthetic Data

```bash
# 1. Generate synthetic data
python scripts/generate_synthetic_data.py --count 10000

# 2. Import to database
python scripts/import_data.py synthetic_data.csv

# 3. Train ML model
python scripts/ml/train_model.py --data synthetic_data.csv

# 4. Test API
curl -X POST http://localhost:8080/api/v1/check-transaction \
  -d @test_transaction.json

# 5. Start monitoring
# Check dashboard for fraud detection results
```

---

### Option 2: Use Public Datasets

```bash
# 1. Download Kaggle dataset
kaggle datasets download -d mlg-ulb/creditcardfraud

# 2. Convert to Sentinel format
python scripts/convert_public_datasets.py \
  --source creditcard.csv \
  --output converted_data.csv

# 3. Train ML model
python scripts/ml/train_model.py --data converted_data.csv

# 4. Test with real fraud patterns
```

---

### Option 3: Find a Beta Customer

```bash
# 1. Build demo
# 2. Reach out to potential customers (email template above)
# 3. Offer 3-month free trial
# 4. Get data sharing agreement signed
# 5. Import their data
# 6. Start detecting fraud!
```

---

## 📞 Need Help?

**What I can build for you**:
1. ✅ Synthetic data generator
2. ✅ Public dataset converter
3. ✅ Data quality validator
4. ✅ Data import scripts
5. ✅ ML training automation

**What you should do**:
1. Start with synthetic data (easiest)
2. Reach out to potential beta customers
3. Offer free trial for data access
4. Use data to train production ML models

---

## 📊 Expected Results

### With Synthetic Data (Week 1)
- 70-75% fraud detection accuracy
- All rules working
- API functional
- Ready for demos

### With Public Datasets (Week 2-3)
- 80-82% fraud detection accuracy
- ML model trained
- Ready for beta customers

### With Real Data from Beta Customers (Month 2-3)
- 85%+ fraud detection accuracy
- Industry-specific tuning
- Ready for production launch

---

## 🎉 Bottom Line

**Start with synthetic data** - You can begin testing TODAY

**Want me to build the synthetic data generator?** I can create a comprehensive script that generates:
- 10,000+ realistic Nigerian transactions
- All 5 industries (fintech, ecommerce, betting, crypto, marketplace)
- 10% fraud rate with realistic patterns
- All fields populated
- Ready to import and test

Just say the word and I'll build it! 🚀
