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


@router.get("/dashboard/transactions")
async def get_transaction_history(
    client: Client = Depends(get_current_client),
    db: Session = Depends(get_db),
    # Basic filters
    risk_level: Optional[str] = Query(None, description="Filter by single risk level (use risk_levels for multiple)"),
    risk_levels: Optional[str] = Query(None, description="Filter by multiple risk levels (comma-separated: low,medium,high)"),
    decision: Optional[str] = Query(None, description="Filter by decision (approve, review, decline)"),
    decisions: Optional[str] = Query(None, description="Filter by multiple decisions (comma-separated)"),
    outcome: Optional[str] = Query(None, description="Filter by outcome (fraud, legitimate, pending)"),
    # Date range filters
    start_date: Optional[str] = Query(None, description="Start date (ISO format: 2024-01-01)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format: 2024-12-31)"),
    # Amount range filters
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum transaction amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum transaction amount"),
    # Search query
    search: Optional[str] = Query(None, description="Search by transaction_id or user_id"),
    # Pagination
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Get transaction history with advanced filtering

    Returns a list of recent transactions with comprehensive filtering options:
    - Risk levels (single or multiple)
    - Decisions (approve, review, decline)
    - Outcomes (fraud, legitimate, pending)
    - Date range (start_date to end_date)
    - Amount range (min_amount to max_amount)
    - Search (transaction_id or user_id)
    - Pagination (limit, offset)

    Returns:
        {
            "transactions": [...],
            "total": 1234,
            "offset": 0,
            "limit": 50
        }
    """
    query = db.query(Transaction).filter(
        Transaction.client_id == client.client_id
    )

    # Risk level filters
    if risk_levels:
        # Multiple risk levels (comma-separated: "low,medium,high")
        levels = [level.strip() for level in risk_levels.split(",")]
        query = query.filter(Transaction.risk_level.in_(levels))
    elif risk_level:
        # Single risk level (backwards compatibility)
        query = query.filter(Transaction.risk_level == risk_level)

    # Decision filters
    if decisions:
        # Multiple decisions (comma-separated: "approve,review,decline")
        decision_list = [d.strip() for d in decisions.split(",")]
        query = query.filter(Transaction.decision.in_(decision_list))
    elif decision:
        # Single decision (backwards compatibility)
        query = query.filter(Transaction.decision == decision)

    # Outcome filter
    if outcome:
        if outcome == "fraud":
            query = query.filter(Transaction.is_fraud == True)
        elif outcome == "legitimate":
            query = query.filter(Transaction.is_fraud == False)
        elif outcome == "pending":
            query = query.filter(Transaction.is_fraud == None)

    # Date range filters
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(Transaction.created_at >= start_dt)
        except ValueError:
            pass  # Invalid date format, skip filter

    if end_date:
        try:
            # Add 23:59:59 to include entire end day
            end_dt = datetime.fromisoformat(end_date)
            end_dt = end_dt.replace(hour=23, minute=59, second=59)
            query = query.filter(Transaction.created_at <= end_dt)
        except ValueError:
            pass  # Invalid date format, skip filter

    # Amount range filters
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)

    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)

    # Search filter (transaction_id or user_id)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Transaction.transaction_id.ilike(search_pattern)) |
            (Transaction.user_id.ilike(search_pattern))
        )

    # Get total count before pagination (for frontend pagination UI)
    total_count = query.count()

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

        result.append({
            "transaction_id": txn.transaction_id,
            "user_id": txn.user_id,
            "amount": float(txn.amount),
            "risk_score": txn.risk_score,
            "risk_level": txn.risk_level,
            "decision": txn.decision,
            "outcome": outcome_str,
            "created_at": txn.created_at.isoformat() if txn.created_at else None
        })

    # Return transactions with pagination metadata
    return {
        "transactions": result,
        "total": total_count,
        "offset": offset,
        "limit": limit
    }


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
