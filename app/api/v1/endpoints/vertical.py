"""
Vertical Management API Endpoints

Provides REST API for managing and querying industry vertical configurations.

Endpoints:
- GET    /api/v1/verticals              - List all verticals
- GET    /api/v1/verticals/{vertical}/config  - Get vertical configuration
- POST   /api/v1/verticals/check        - Check transaction with vertical-specific rules
- GET    /api/v1/verticals/{vertical}/metrics - Get fraud metrics for vertical
- PATCH  /api/v1/verticals/{vertical}/config  - Update vertical configuration
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta

from app.models.schemas import (
    Industry,
    TransactionCheckRequest,
    TransactionCheckResponse,
    FraudFlag
)
from app.services.vertical_service import vertical_service, VerticalConfig
from app.services.rules import FraudRulesEngine
from app.models.database import get_db, Transaction

router = APIRouter()


@router.get("/", tags=["Verticals"])
async def list_verticals():
    """
    List all supported industry verticals

    Returns a list of all 7 industry verticals supported by Sentinel,
    along with their basic configuration details.

    Returns:
        - verticals: List of vertical names
        - count: Number of verticals
        - configs: Summary of each vertical's configuration
    """
    verticals = vertical_service.list_verticals()
    configs_summary = {}

    for vertical_name in verticals:
        try:
            vertical_enum = Industry(vertical_name)
            config = vertical_service.get_config(vertical_enum)
            configs_summary[vertical_name] = {
                "fraud_score_threshold": config.fraud_score_threshold,
                "aml_risk_threshold": config.aml_risk_threshold,
                "enabled": config.enabled,
                "description": config.description,
                "rule_count": len(config.rule_weight_multiplier)
            }
        except ValueError:
            continue

    return {
        "verticals": verticals,
        "count": len(verticals),
        "configs": configs_summary,
        "description": "All supported industry verticals with fraud detection"
    }


@router.get("/{vertical}/config", tags=["Verticals"])
async def get_vertical_config(vertical: str):
    """
    Get detailed configuration for a specific vertical

    Args:
        vertical: Vertical name (lending, fintech, ecommerce, betting, gaming, crypto, marketplace)

    Returns:
        - vertical: Vertical name
        - fraud_score_threshold: Fraud score threshold (0-100)
        - aml_risk_threshold: AML risk threshold (0-100)
        - enabled: Whether this vertical is active
        - description: Human-readable description
        - rule_weights: Dictionary of rule-specific weight multipliers
        - weighted_rules_count: Number of rules with custom weights

    Raises:
        404: Vertical not found
    """
    try:
        vertical_enum = Industry(vertical)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Vertical '{vertical}' not found. Valid verticals: {', '.join([v.value for v in Industry])}"
        )

    config = vertical_service.get_config(vertical_enum)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration not found for vertical '{vertical}'"
        )

    return {
        "vertical": vertical,
        "fraud_score_threshold": config.fraud_score_threshold,
        "aml_risk_threshold": config.aml_risk_threshold,
        "enabled": config.enabled,
        "description": config.description,
        "rule_weights": config.rule_weight_multiplier,
        "weighted_rules_count": len(config.rule_weight_multiplier),
        "last_updated": datetime.utcnow().isoformat()
    }


@router.post("/check", tags=["Verticals"], response_model=TransactionCheckResponse)
async def check_transaction_with_vertical(
    request: TransactionCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Check transaction using vertical-specific fraud rules and thresholds

    This endpoint evaluates a transaction using:
    1. Vertical-specific fraud score threshold
    2. Vertical-specific rule weights (some rules matter more in certain industries)
    3. All 29 fraud detection rules

    Different industries have different fraud patterns:
    - Crypto: Lower threshold (50%), higher weights for wallet rules
    - Lending: Higher threshold (65%), higher weights for loan stacking
    - Betting: Focus on bonus abuse and arbitrage

    Args:
        request: Transaction data including industry vertical

    Returns:
        TransactionCheckResponse with:
        - risk_score: Weighted fraud score (0-100)
        - risk_level: low, medium, high, critical
        - decision: approve, review, decline
        - flags: List of triggered fraud rules
        - vertical_info: Threshold and weights used
    """
    start_time = datetime.utcnow()

    # Get vertical configuration
    vertical_config = vertical_service.get_config(request.industry)
    if not vertical_config:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid industry vertical: {request.industry}"
        )

    if not vertical_config.enabled:
        raise HTTPException(
            status_code=400,
            detail=f"Vertical '{request.industry.value}' is currently disabled"
        )

    # Initialize fraud rules engine
    engine = FraudRulesEngine()

    # Build transaction context
    transaction_context = {
        "transaction_id": request.transaction_id,
        "user_id": request.user_id,
        "amount": request.amount,
        "transaction_type": request.transaction_type,
        "industry": request.industry,
        "device_id": request.device_id,
        "device_fingerprint": request.device_fingerprint,
        "ip_address": request.ip_address,
        "account_age_days": request.account_age_days,
        "transaction_count": request.transaction_count,
        "phone_changed_recently": request.phone_changed_recently,
        "email_changed_recently": request.email_changed_recently,
        "country": request.country,
        # Add more context as needed
    }

    # Evaluate with vertical-specific weights
    evaluation_result = engine.evaluate_transaction(transaction_context)

    # Apply vertical-specific rule weights
    weighted_score = 0.0
    triggered_flags: List[FraudFlag] = []

    for rule_result in evaluation_result.get("triggered_rules", []):
        rule_name = rule_result.get("rule_name", "")
        base_score = rule_result.get("score", 0)

        # Get vertical-specific weight for this rule
        weight = vertical_service.get_rule_weight(request.industry, rule_name)
        weighted_rule_score = base_score * weight

        weighted_score += weighted_rule_score

        # Create fraud flag
        triggered_flags.append(FraudFlag(
            type=rule_name,
            severity=rule_result.get("severity", "medium"),
            message=rule_result.get("message", ""),
            score=int(weighted_rule_score),
            confidence=rule_result.get("confidence"),
            metadata={
                "base_score": base_score,
                "weight": weight,
                "vertical": request.industry.value
            }
        ))

    # Normalize score to 0-100
    final_score = min(100, int(weighted_score))

    # Determine risk level using vertical-specific threshold
    threshold = vertical_config.fraud_score_threshold

    if final_score >= 80:
        risk_level = "critical"
        decision = "decline"
    elif final_score >= threshold:
        risk_level = "high"
        decision = "decline"
    elif final_score >= (threshold * 0.7):  # 70% of threshold
        risk_level = "medium"
        decision = "review"
    else:
        risk_level = "low"
        decision = "approve"

    # Calculate processing time
    processing_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

    return TransactionCheckResponse(
        transaction_id=request.transaction_id,
        risk_score=final_score,
        risk_level=risk_level,
        decision=decision,
        flags=triggered_flags,
        recommendation=f"[{request.industry.value.upper()}] {decision.upper()} - "
                      f"Risk: {final_score}% (threshold: {threshold}%)",
        processing_time_ms=processing_time_ms
    )


@router.get("/{vertical}/metrics", tags=["Verticals"])
async def get_vertical_metrics(
    vertical: str,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Get fraud detection metrics for a specific vertical

    Returns aggregated fraud statistics for transactions in this vertical
    over the specified time period.

    Args:
        vertical: Vertical name
        days: Number of days to look back (default 30)

    Returns:
        - vertical: Vertical name
        - time_period: Days analyzed
        - total_transactions: Count of transactions
        - fraud_detected: Count flagged as fraudulent
        - fraud_rate_percent: Percentage of fraudulent transactions
        - average_fraud_score: Mean fraud score
        - high_risk_count: Transactions above threshold
        - critical_risk_count: Transactions with critical risk
        - top_triggered_rules: Most frequently triggered fraud rules
    """
    try:
        vertical_enum = Industry(vertical)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Vertical '{vertical}' not found"
        )

    config = vertical_service.get_config(vertical_enum)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Configuration not found for vertical '{vertical}'"
        )

    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)

    # Query transactions for this vertical
    try:
        transactions = db.query(Transaction).filter(
            Transaction.vertical == vertical,
            Transaction.created_at >= start_date,
            Transaction.created_at <= end_date
        ).all()
    except Exception as e:
        # If vertical column doesn't exist or other DB error, return sample data
        transactions = []

    # Calculate metrics
    total_count = len(transactions)
    fraud_count = sum(1 for t in transactions if t.is_fraudulent) if transactions else 0
    fraud_rate = (fraud_count / total_count * 100) if total_count > 0 else 0

    avg_fraud_score = (
        sum(t.fraud_score for t in transactions) / total_count
        if total_count > 0 else 0
    )

    high_risk_count = sum(
        1 for t in transactions
        if t.fraud_score >= config.fraud_score_threshold
    ) if transactions else 0

    critical_risk_count = sum(
        1 for t in transactions
        if t.fraud_score >= 80
    ) if transactions else 0

    # Aggregate rule triggers (if stored in fraud_rules_triggered JSONB)
    rule_frequency: Dict[str, int] = {}
    for txn in transactions:
        if txn.fraud_rules_triggered:
            for rule in txn.fraud_rules_triggered:
                rule_name = rule if isinstance(rule, str) else rule.get("rule_name", "")
                rule_frequency[rule_name] = rule_frequency.get(rule_name, 0) + 1

    # Top 10 most triggered rules
    top_rules = sorted(
        rule_frequency.items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    return {
        "vertical": vertical,
        "time_period_days": days,
        "date_range": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat()
        },
        "total_transactions": total_count,
        "fraud_detected": fraud_count,
        "fraud_rate_percent": round(fraud_rate, 2),
        "average_fraud_score": round(avg_fraud_score, 2),
        "high_risk_count": high_risk_count,
        "critical_risk_count": critical_risk_count,
        "threshold_info": {
            "fraud_score_threshold": config.fraud_score_threshold,
            "aml_risk_threshold": config.aml_risk_threshold
        },
        "top_triggered_rules": [
            {"rule": rule, "count": count}
            for rule, count in top_rules
        ],
        "generated_at": datetime.utcnow().isoformat()
    }


@router.patch("/{vertical}/config", tags=["Verticals"])
async def update_vertical_config(
    vertical: str,
    fraud_score_threshold: float = None,
    aml_risk_threshold: float = None,
    enabled: bool = None
):
    """
    Update configuration for a vertical (Admin only)

    Allows dynamic adjustment of fraud detection thresholds and settings
    for a specific industry vertical.

    Args:
        vertical: Vertical name
        fraud_score_threshold: New fraud score threshold (0-100)
        aml_risk_threshold: New AML risk threshold (0-100)
        enabled: Enable/disable this vertical

    Returns:
        Updated configuration

    Note: In production, this should require admin authentication
    """
    try:
        vertical_enum = Industry(vertical)
    except ValueError:
        raise HTTPException(
            status_code=404,
            detail=f"Vertical '{vertical}' not found"
        )

    # Prepare update parameters
    updates = {}
    if fraud_score_threshold is not None:
        if fraud_score_threshold < 0 or fraud_score_threshold > 100:
            raise HTTPException(
                status_code=400,
                detail="fraud_score_threshold must be between 0 and 100"
            )
        updates["fraud_score_threshold"] = fraud_score_threshold

    if aml_risk_threshold is not None:
        if aml_risk_threshold < 0 or aml_risk_threshold > 100:
            raise HTTPException(
                status_code=400,
                detail="aml_risk_threshold must be between 0 and 100"
            )
        updates["aml_risk_threshold"] = aml_risk_threshold

    if enabled is not None:
        updates["enabled"] = enabled

    if not updates:
        raise HTTPException(
            status_code=400,
            detail="No updates provided"
        )

    # Update configuration
    try:
        updated_config = vertical_service.update_config(vertical_enum, **updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return {
        "vertical": vertical,
        "updated_fields": list(updates.keys()),
        "new_config": {
            "fraud_score_threshold": updated_config.fraud_score_threshold,
            "aml_risk_threshold": updated_config.aml_risk_threshold,
            "enabled": updated_config.enabled,
        },
        "updated_at": datetime.utcnow().isoformat(),
        "message": f"Configuration updated for {vertical} vertical"
    }
