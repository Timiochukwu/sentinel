# WEEK 1: Consortium Network & BVN Verification
**Days 57-63 | Month 3**

## Overview
This week adds shared fraud intelligence and identity verification:
- Consortium network for sharing fraud data across clients
- BVN (Bank Verification Number) validation service
- Consortium API endpoints
- Cross-client fraud pattern detection

## Files to Build

```
app/services/
├── consortium.py                 # 380 lines - Consortium network service
└── bvn_verification.py           # 215 lines - BVN validation

app/api/v1/endpoints/
└── consortium.py                 # 180 lines - Consortium API endpoints
```

**Total for Week 1:** 3 files, ~775 lines of code

---

## Dependencies

Add new dependencies:

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

# NEW for Month 3 Week 1
httpx==0.25.2
cryptography==41.0.7
```

---

## File Details

### 1. `app/services/consortium.py` (380 lines)

**Purpose:** Share and query fraud data across multiple clients

**Key Features:**
- Query user fraud history from other clients
- Share fraud flags with consortium
- Privacy-preserving hashing
- Fraud score aggregation

**Key Functions:**

```python
class ConsortiumService:
    def __init__(self):
        self.db = SessionLocal()
        self.redis = RedisService()

    def query_user(self, identifiers: dict) -> dict:
        """
        Query consortium for user fraud history

        Args:
            identifiers: {
                "email": "user@example.com",
                "phone": "+2348012345678",
                "device_id": "device123"
            }

        Returns:
            {
                "total_fraud_flags": 15,
                "critical_flags": 3,
                "last_fraud_date": "2024-01-10",
                "participating_clients": 3
            }
        """
        # Hash identifiers for privacy
        email_hash = self._hash_identifier(identifiers.get("email"))
        phone_hash = self._hash_identifier(identifiers.get("phone"))

        # Query consortium database
        flags = self.db.query(FraudFlag).filter(
            or_(
                FraudFlag.email_hash == email_hash,
                FraudFlag.phone_hash == phone_hash
            )
        ).all()

        return {
            "total_fraud_flags": len(flags),
            "critical_flags": sum(1 for f in flags if f.severity == "critical"),
            "last_fraud_date": max(f.created_at for f in flags) if flags else None,
            "participating_clients": len(set(f.client_id for f in flags))
        }

    def share_fraud_flag(self, user_id: str, flag: dict, client_id: str):
        """Share fraud flag with consortium"""
        # Implementation
        pass

    def _hash_identifier(self, value: str) -> str:
        """Privacy-preserving hash"""
        import hashlib
        return hashlib.sha256(value.encode()).hexdigest()
```

---

### 2. `app/services/bvn_verification.py` (215 lines)

**Purpose:** Bank Verification Number validation

**Key Functions:**

```python
class BVNVerificationService:
    def __init__(self):
        self.api_key = settings.BVN_API_KEY
        self.api_url = settings.BVN_API_URL

    async def verify_bvn(
        self,
        bvn: str,
        first_name: str,
        last_name: str,
        dob: str
    ) -> dict:
        """
        Verify BVN matches provided details

        Returns:
            {
                "verified": True/False,
                "match_score": 0.95,
                "mismatches": []
            }
        """
        # Call external BVN API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/verify",
                json={
                    "bvn": bvn,
                    "first_name": first_name,
                    "last_name": last_name,
                    "date_of_birth": dob
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )

        if response.status_code == 200:
            data = response.json()
            return {
                "verified": data.get("match", False),
                "match_score": data.get("confidence", 0.0),
                "mismatches": data.get("mismatches", [])
            }

        return {"verified": False, "error": "API call failed"}
```

---

### 3. `app/api/v1/endpoints/consortium.py` (180 lines)

**Purpose:** Consortium API endpoints

**Endpoints:**

#### POST /api/v1/consortium/query
Query consortium for user fraud history

```python
@router.post("/query")
async def query_consortium(
    request: ConsortiumQueryRequest,
    api_key: str = Depends(verify_api_key)
):
    """Query consortium for user fraud history"""
    service = ConsortiumService()
    result = service.query_user(request.identifiers)
    return result
```

#### POST /api/v1/consortium/share
Share fraud flag with consortium

```python
@router.post("/share")
async def share_fraud_flag(
    request: ConsortiumShareRequest,
    api_key: str = Depends(verify_api_key)
):
    """Share fraud flag with consortium"""
    service = ConsortiumService()
    service.share_fraud_flag(
        request.user_id,
        request.flag,
        request.client_id
    )
    return {"status": "shared"}
```

---

## Testing with curl

### Test 1: Query Consortium

```bash
curl -X POST http://localhost:8000/api/v1/consortium/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "identifiers": {
      "email": "fraudster@example.com",
      "phone": "+2348012345678",
      "device_id": "device123"
    }
  }'
```

**Expected Response:**
```json
{
  "total_fraud_flags": 15,
  "critical_flags": 3,
  "last_fraud_date": "2024-01-10T10:30:00Z",
  "participating_clients": 3
}
```

---

### Test 2: BVN Verification (Mock)

```bash
curl -X POST http://localhost:8000/api/v1/fraud/verify-bvn \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-api-key-12345" \
  -d '{
    "bvn": "12345678901",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01"
  }'
```

**Expected Response:**
```json
{
  "verified": true,
  "match_score": 0.95,
  "mismatches": []
}
```

---

## Success Criteria

By the end of Week 1 (Month 3), you should have:

- ✅ Consortium service querying fraud data
- ✅ BVN verification working (mock or real API)
- ✅ Consortium API endpoints functional
- ✅ Privacy-preserving identifier hashing
- ✅ Cross-client fraud pattern detection

---

## Next Week Preview

**Week 2:** Dashboard & Analytics Endpoints
- Dashboard stats endpoint
- Vertical-specific configurations
- Feedback loop for rule tuning
- Analytics and reporting

---

## File Checklist

Week 1 files to create:
- [ ] app/services/consortium.py
- [ ] app/services/bvn_verification.py
- [ ] app/api/v1/endpoints/consortium.py
- [ ] requirements.txt (in build_guides/month_03/week_01/)

---

**End of Week 1 Guide - Month 3**
