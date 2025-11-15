# Sentinel - Nigerian Fraud Detection Platform

## Overview

Sentinel is Africa's leading fraud detection platform for financial institutions, starting with Nigerian lenders. The platform prevents ₦50B+ in annual fraud losses through real-time risk intelligence and consortium-based fraud pattern sharing.

## Key Features

- **Real-Time Fraud Scoring API**: Returns risk scores in <100ms with specific fraud flags
- **Consortium Intelligence**: Detects cross-platform fraud patterns across multiple lenders
- **15+ Detection Rules**: Comprehensive rule-based fraud detection system
- **Privacy-Preserving**: Uses SHA-256 hashing to protect customer PII
- **Dashboard**: Web-based UI for fraud analysts and risk managers
- **Continuous Learning**: Feedback loop improves accuracy over time

## Tech Stack

- **Backend**: Python 3.11 + FastAPI
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Frontend**: React 18 + TypeScript
- **ML**: scikit-learn, XGBoost
- **Deployment**: Docker + Docker Compose

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Node.js 18+ (for frontend)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd sentinel
```

2. Set up Python environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Initialize the database:
```bash
python scripts/init_db.py
```

5. Start the services:
```bash
docker-compose up -d
```

6. Run the application:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## API Usage

### Check Transaction for Fraud

```bash
curl -X POST http://localhost:8000/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "transaction_id": "txn_12345",
    "user_id": "user_789",
    "amount": 250000,
    "transaction_type": "loan_disbursement",
    "device_id": "abc123",
    "ip_address": "197.210.226.45",
    "account_age_days": 3,
    "transaction_count": 0,
    "phone_changed_recently": true,
    "email_changed_recently": false
  }'
```

### Submit Feedback

```bash
curl -X POST http://localhost:8000/api/v1/feedback \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "transaction_id": "txn_12345",
    "actual_outcome": "fraud",
    "fraud_type": "loan_stacking",
    "amount_saved": 250000
  }'
```

## Project Structure

```
sentinel/
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── api/
│   │   ├── v1/
│   │   │   ├── endpoints/
│   │   │   │   ├── fraud_detection.py
│   │   │   │   ├── feedback.py
│   │   │   │   └── dashboard.py
│   │   │   └── api.py
│   │   └── deps.py            # Dependencies and authentication
│   ├── core/
│   │   ├── config.py          # Configuration management
│   │   ├── security.py        # Security utilities
│   │   └── fraud_detector.py  # Core fraud detection engine
│   ├── models/
│   │   ├── database.py        # Database models
│   │   └── schemas.py         # Pydantic schemas
│   ├── services/
│   │   ├── consortium.py      # Consortium intelligence
│   │   ├── rules.py           # Fraud detection rules
│   │   └── learning.py        # ML and learning algorithms
│   └── db/
│       ├── session.py         # Database session management
│       └── init_db.py         # Database initialization
├── frontend/                   # React dashboard (separate directory)
├── tests/
│   ├── test_api.py
│   ├── test_rules.py
│   └── test_consortium.py
├── scripts/
│   ├── init_db.py             # Database initialization script
│   └── seed_data.py           # Sample data for testing
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## Fraud Detection Rules

Sentinel implements 15+ fraud detection rules:

1. **New Account Large Amount**: New accounts (<7 days) with large transactions
2. **Loan Stacking**: Multiple lender applications within 7 days
3. **SIM Swap Pattern**: Phone change + new device + withdrawal
4. **Suspicious Hours**: Transactions during 2am-5am
5. **Velocity Check**: Multiple transactions in short time
6. **Contact Change + Withdrawal**: Recent contact changes with withdrawals
7. **New Device**: First-time device with large amount
8. **Round Amount**: Suspicious round number patterns
9. **Maximum First Transaction**: First transaction at max limit
10. **Impossible Travel**: Geographically impossible locations
11. **VPN/Proxy**: Known VPN/proxy IP addresses
12. **Disposable Email**: Temporary email services
13. **Device Sharing**: Single device for multiple accounts
14. **Dormant Account Activation**: Long-dormant accounts suddenly active
15. **Sequential Applications**: Patterns indicating coordinated fraud

## Performance

- **API Response Time**: <100ms (p95)
- **Throughput**: 1,000+ requests/minute per client
- **Uptime**: 99.9% SLA
- **Fraud Detection Rate**: 70-85%
- **False Positive Rate**: <10-15%

## Security

- All data encrypted at rest (AES-256) and in transit (TLS 1.3)
- Privacy-preserving consortium intelligence using SHA-256 hashing
- No raw BVN/NIN/phone numbers stored
- NDPR (Nigeria Data Protection Regulation) compliant
- Role-Based Access Control (RBAC)
- API key authentication with rate limiting

## License

Copyright © 2024 Sentinel. All rights reserved.

## Support

For support, email support@sentinel-fraud.com or join our Slack community.
