"""Feedback API endpoints"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.db.session import get_db
from app.api.deps import get_current_client
from app.models.database import Client, Transaction
from app.models.schemas import FeedbackRequest, FeedbackResponse
from app.services.learning import LearningService
from app.services.consortium import ConsortiumService

router = APIRouter()


@router.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    feedback: FeedbackRequest,
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """
    Submit feedback about a transaction's actual outcome

    This endpoint allows you to report whether a transaction was actually
    fraudulent or legitimate. This feedback improves the system's accuracy
    over time through continuous learning.

    **Use Cases**:
    - Confirm fraud after investigation
    - Report false positives
    - Update fraud type information

    **Example Request**:
    ```json
    {
        "transaction_id": "txn_12345",
        "actual_outcome": "fraud",
        "fraud_type": "loan_stacking",
        "notes": "Customer confirmed they didn't apply. SIM swap attack.",
        "amount_saved": 250000
    }
    ```

    **Impact**:
    - Updates rule accuracy metrics
    - Adjusts rule weights for better predictions
    - Contributes to consortium intelligence
    - Tracks total fraud prevented
    """
    try:
        # Get the transaction
        transaction = db.query(Transaction).filter(
            Transaction.transaction_id == feedback.transaction_id,
            Transaction.client_id == client.client_id
        ).first()

        if not transaction:
            raise HTTPException(
                status_code=404,
                detail=f"Transaction {feedback.transaction_id} not found"
            )

        # Update transaction with feedback
        transaction.is_fraud = (feedback.actual_outcome == "fraud")
        transaction.fraud_type = feedback.fraud_type
        transaction.fraud_confirmed_at = datetime.utcnow()
        transaction.feedback_notes = feedback.notes
        transaction.amount_saved = feedback.amount_saved

        db.commit()

        # Process feedback for learning
        learning_service = LearningService(db)
        learning_result = learning_service.process_feedback(
            transaction_id=feedback.transaction_id,
            actual_outcome=feedback.actual_outcome,
            fraud_type=feedback.fraud_type
        )

        # If fraud confirmed, update consortium intelligence
        if feedback.actual_outcome == "fraud":
            from app.models.schemas import TransactionCheckRequest

            # Recreate transaction request from stored data
            txn_request = TransactionCheckRequest(
                transaction_id=transaction.transaction_id,
                user_id=transaction.user_id,
                amount=float(transaction.amount),
                transaction_type=transaction.transaction_type,
                device_id=transaction.device_id,
                bvn=transaction.bvn,
                phone=transaction.phone,
                email=transaction.email
            )

            consortium = ConsortiumService(db, client.client_id)
            consortium.report_fraud(
                transaction=txn_request,
                fraud_type=feedback.fraud_type or "unknown",
                amount=feedback.amount_saved or float(transaction.amount)
            )

            # Update client statistics
            client.total_fraud_caught += 1
            if feedback.amount_saved:
                client.total_amount_saved = (client.total_amount_saved or 0) + feedback.amount_saved
            db.commit()

        # Build response
        accuracy_impact = None
        if learning_result.get("updated_rules"):
            rules = learning_result["updated_rules"]
            accuracy_impact = f"Updated {len(rules)} rule(s) accuracy"

        return FeedbackResponse(
            status="received",
            message="Feedback processed successfully",
            accuracy_impact=accuracy_impact,
            total_feedback_count=learning_result["total_feedback_count"]
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process feedback: {str(e)}"
        )
