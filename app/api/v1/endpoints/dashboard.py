"""Dashboard and analytics API endpoints"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from app.db.session import get_db
from app.api.deps import get_current_client
from app.models.database import Client, Transaction
from app.models.schemas import (
    DashboardStats,
    TransactionHistory,
    ClientInfo,
    RuleAccuracyInfo
)
from app.services.learning import LearningService

router = APIRouter()


@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """
    Get dashboard statistics

    Returns comprehensive statistics for the dashboard including:
    - Today's transaction summary
    - 30-day summary
    - Risk distribution
    - Fraud type breakdown
    """
    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    month_start = now - timedelta(days=30)

    # Today's transactions
    today_txns = db.query(Transaction).filter(
        Transaction.client_id == client.client_id,
        Transaction.created_at >= today_start
    ).all()

    today_transactions = len(today_txns)
    today_high_risk = sum(1 for t in today_txns if t.risk_level == "high")
    today_medium_risk = sum(1 for t in today_txns if t.risk_level == "medium")
    today_low_risk = sum(1 for t in today_txns if t.risk_level == "low")

    # Estimate fraud prevented today (high risk transactions)
    today_fraud_prevented = sum(
        float(t.amount) for t in today_txns
        if t.risk_level == "high" and t.decision == "decline"
    )

    # 30-day transactions
    month_txns = db.query(Transaction).filter(
        Transaction.client_id == client.client_id,
        Transaction.created_at >= month_start
    ).all()

    month_transactions = len(month_txns)
    month_fraud_caught = sum(1 for t in month_txns if t.is_fraud == True)

    # Estimate fraud prevented (amount)
    month_fraud_prevented = sum(
        float(t.amount) for t in month_txns
        if t.risk_level == "high" and t.decision == "decline"
    )

    # Calculate metrics
    learning_service = LearningService(db)
    metrics = learning_service.calculate_overall_accuracy(client.client_id)

    # Risk distribution
    risk_distribution = {
        "low": sum(1 for t in month_txns if t.risk_level == "low"),
        "medium": sum(1 for t in month_txns if t.risk_level == "medium"),
        "high": sum(1 for t in month_txns if t.risk_level == "high")
    }

    # Fraud types
    fraud_types_dict = {}
    for txn in month_txns:
        if txn.fraud_type:
            fraud_types_dict[txn.fraud_type] = fraud_types_dict.get(txn.fraud_type, 0) + 1

    return DashboardStats(
        today_transactions=today_transactions,
        today_high_risk=today_high_risk,
        today_medium_risk=today_medium_risk,
        today_low_risk=today_low_risk,
        today_fraud_prevented_amount=today_fraud_prevented,
        month_transactions=month_transactions,
        month_fraud_caught=month_fraud_caught,
        month_fraud_prevented_amount=month_fraud_prevented,
        month_false_positive_rate=metrics.get("false_positive_rate", 0),
        month_accuracy=metrics.get("accuracy", 0),
        risk_distribution=risk_distribution,
        fraud_types=fraud_types_dict
    )


@router.get("/dashboard/transactions", response_model=List[TransactionHistory])
async def get_transaction_history(
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    outcome: Optional[str] = Query(None, description="Filter by outcome"),
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get transaction history

    Returns a list of recent transactions with filters for risk level and outcome.
    """
    query = db.query(Transaction).filter(
        Transaction.client_id == client.client_id
    )

    # Apply filters
    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level)

    if outcome:
        if outcome == "fraud":
            query = query.filter(Transaction.is_fraud == True)
        elif outcome == "legitimate":
            query = query.filter(Transaction.is_fraud == False)
        elif outcome == "pending":
            query = query.filter(Transaction.is_fraud == None)

    # Order by newest first
    query = query.order_by(Transaction.created_at.desc())

    # Pagination
    transactions = query.offset(offset).limit(limit).all()

    # Convert to response schema
    result = []
    for txn in transactions:
        outcome_str = None
        if txn.is_fraud is not None:
            outcome_str = "fraud" if txn.is_fraud else "legitimate"
        else:
            outcome_str = "pending"

        result.append(TransactionHistory(
            transaction_id=txn.transaction_id,
            amount=float(txn.amount),
            risk_score=txn.risk_score,
            risk_level=txn.risk_level,
            decision=txn.decision,
            outcome=outcome_str,
            created_at=txn.created_at
        ))

    return result


@router.get("/dashboard/client-info", response_model=ClientInfo)
async def get_client_info(
    client: Client = Depends(get_current_client)
):
    """Get current client information"""
    return ClientInfo(
        client_id=client.client_id,
        company_name=client.company_name,
        plan=client.plan or "starter",
        status=client.status,
        total_checks=client.total_checks,
        total_fraud_caught=client.total_fraud_caught,
        total_amount_saved=float(client.total_amount_saved or 0),
        created_at=client.created_at
    )


@router.get("/dashboard/rule-accuracy", response_model=List[RuleAccuracyInfo])
async def get_rule_accuracy(
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db)
):
    """
    Get fraud detection rule accuracy metrics

    Returns accuracy statistics for each fraud detection rule.
    """
    learning_service = LearningService(db)
    accuracies = learning_service.get_all_rule_accuracies()

    return [
        RuleAccuracyInfo(
            rule_name=acc["rule_name"],
            triggered_count=acc["triggered_count"],
            accuracy=acc["accuracy"],
            precision=acc["precision"],
            recall=0.0,  # Would need false negatives to calculate
            current_weight=acc["current_weight"]
        )
        for acc in accuracies
    ]
