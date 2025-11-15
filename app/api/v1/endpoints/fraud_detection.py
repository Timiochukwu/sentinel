"""Fraud detection API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_client, check_rate_limit
from app.models.database import Client
from app.models.schemas import TransactionCheckRequest, TransactionCheckResponse
from app.core.fraud_detector import FraudDetector

router = APIRouter()


@router.post("/check-transaction", response_model=TransactionCheckResponse)
async def check_transaction(
    transaction: TransactionCheckRequest,
    client: Client = Depends(check_rate_limit),
    db: Session = Depends(get_db)
):
    """
    Check a transaction for fraud

    This is the main fraud detection endpoint. It analyzes the transaction
    and returns a risk score, risk level, decision, and specific fraud flags.

    **Performance**: Typically responds in <100ms

    **Rate Limit**: Based on your plan (10,000 - unlimited requests/hour)

    **Example Request**:
    ```json
    {
        "transaction_id": "txn_12345",
        "user_id": "user_789",
        "amount": 250000,
        "transaction_type": "loan_disbursement",
        "device_id": "abc123",
        "ip_address": "197.210.226.45",
        "account_age_days": 3,
        "transaction_count": 0,
        "phone_changed_recently": true
    }
    ```

    **Example Response**:
    ```json
    {
        "transaction_id": "txn_12345",
        "risk_score": 85,
        "risk_level": "high",
        "decision": "decline",
        "flags": [
            {
                "type": "new_account",
                "severity": "medium",
                "message": "Account only 3 days old",
                "score": 30,
                "confidence": 0.87
            }
        ],
        "recommendation": "Decline or request video verification",
        "processing_time_ms": 87
    }
    ```
    """
    try:
        # Initialize fraud detector
        detector = FraudDetector(db=db, client_id=client.client_id)

        # Run fraud detection
        result = detector.check_transaction(transaction)

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fraud detection failed: {str(e)}"
        )


@router.get("/transaction/{transaction_id}", response_model=TransactionCheckResponse)
async def get_transaction(
    transaction_id: str,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """
    Get fraud detection result for a specific transaction

    Retrieves the fraud detection results for a previously checked transaction.
    """
    from app.models.database import Transaction

    transaction = db.query(Transaction).filter(
        Transaction.transaction_id == transaction_id,
        Transaction.client_id == client.client_id
    ).first()

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction {transaction_id} not found"
        )

    # Convert database record to response schema
    from app.models.schemas import FraudFlag

    flags = []
    if transaction.flags:
        flags = [
            FraudFlag(
                type=flag.get("type"),
                severity=flag.get("severity"),
                message=flag.get("message"),
                score=flag.get("score"),
                confidence=flag.get("confidence"),
                metadata=flag.get("metadata")
            )
            for flag in transaction.flags
        ]

    return TransactionCheckResponse(
        transaction_id=transaction.transaction_id,
        risk_score=transaction.risk_score,
        risk_level=transaction.risk_level,
        decision=transaction.decision,
        flags=flags,
        recommendation=None,  # Not stored in DB
        processing_time_ms=transaction.processing_time_ms
    )
