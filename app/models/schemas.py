"""Pydantic schemas for request/response validation"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from decimal import Decimal


# Request Schemas
class TransactionCheckRequest(BaseModel):
    """Request schema for fraud detection check"""

    transaction_id: str = Field(..., description="Unique transaction identifier")
    user_id: str = Field(..., description="User identifier")
    amount: float = Field(..., description="Transaction amount in Naira", ge=0)
    transaction_type: str = Field(
        default="loan_disbursement",
        description="Type of transaction (loan_disbursement, withdrawal, transfer, etc.)"
    )

    # Device and network info
    device_id: Optional[str] = Field(None, description="Device identifier")
    ip_address: Optional[str] = Field(None, description="IP address of transaction")

    # Account info
    account_age_days: Optional[int] = Field(None, description="Age of account in days", ge=0)
    transaction_count: Optional[int] = Field(None, description="Previous transaction count", ge=0)

    # Contact changes
    phone_changed_recently: Optional[bool] = Field(False, description="Phone changed in last 48 hours")
    email_changed_recently: Optional[bool] = Field(False, description="Email changed in last 48 hours")

    # Optional PII (will be hashed)
    bvn: Optional[str] = Field(None, description="Bank Verification Number (will be hashed)")
    phone: Optional[str] = Field(None, description="Phone number (will be hashed)")
    email: Optional[str] = Field(None, description="Email address (will be hashed)")

    # Geolocation
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    city: Optional[str] = Field(None, description="City of transaction")
    country: Optional[str] = Field(default="Nigeria", description="Country of transaction")

    # Additional context
    is_first_transaction: Optional[bool] = Field(False, description="Is this the user's first transaction")
    dormant_days: Optional[int] = Field(None, description="Days since last activity", ge=0)
    previous_fraud_count: Optional[int] = Field(0, description="Number of previous fraud cases", ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_12345",
                "user_id": "user_789",
                "amount": 250000,
                "transaction_type": "loan_disbursement",
                "device_id": "abc123",
                "ip_address": "197.210.226.45",
                "account_age_days": 3,
                "transaction_count": 0,
                "phone_changed_recently": True,
                "email_changed_recently": False
            }
        }


# Response Schemas
class FraudFlag(BaseModel):
    """Individual fraud flag/indicator"""

    type: str = Field(..., description="Type of fraud flag")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    message: str = Field(..., description="Human-readable description")
    score: int = Field(..., description="Risk score contribution", ge=0, le=100)
    confidence: Optional[float] = Field(None, description="Confidence level (0-1)", ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class TransactionCheckResponse(BaseModel):
    """Response schema for fraud detection check"""

    transaction_id: str
    risk_score: int = Field(..., description="Risk score 0-100", ge=0, le=100)
    risk_level: str = Field(..., description="Risk level (low, medium, high)")
    decision: str = Field(..., description="Decision (approve, review, decline)")
    flags: List[FraudFlag] = Field(default=[], description="List of fraud flags detected")
    recommendation: Optional[str] = Field(None, description="Recommended action")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")

    # Consortium intelligence
    consortium_alerts: Optional[List[str]] = Field(
        None,
        description="Alerts from consortium intelligence"
    )

    class Config:
        json_schema_extra = {
            "example": {
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
                    },
                    {
                        "type": "loan_stacking",
                        "severity": "critical",
                        "message": "Applied to 3 other lenders this week",
                        "score": 40
                    }
                ],
                "recommendation": "Decline or request video verification",
                "processing_time_ms": 87
            }
        }


class FeedbackRequest(BaseModel):
    """Request schema for submitting fraud outcome feedback"""

    transaction_id: str = Field(..., description="Transaction ID to update")
    actual_outcome: str = Field(..., description="Actual outcome (fraud or legitimate)")
    fraud_type: Optional[str] = Field(None, description="Type of fraud if confirmed")
    notes: Optional[str] = Field(None, description="Additional notes")
    amount_saved: Optional[float] = Field(None, description="Amount saved if fraud prevented", ge=0)

    @validator('actual_outcome')
    def validate_outcome(cls, v):
        if v not in ['fraud', 'legitimate']:
            raise ValueError('actual_outcome must be either "fraud" or "legitimate"')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_12345",
                "actual_outcome": "fraud",
                "fraud_type": "loan_stacking",
                "notes": "Customer confirmed they didn't apply. SIM swap attack.",
                "amount_saved": 250000
            }
        }


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission"""

    status: str
    message: str
    accuracy_impact: Optional[str] = None
    total_feedback_count: int


# Dashboard/Analytics Schemas
class DashboardStats(BaseModel):
    """Dashboard statistics"""

    # Today's summary
    today_transactions: int
    today_high_risk: int
    today_medium_risk: int
    today_low_risk: int
    today_fraud_prevented_amount: float

    # 30-day summary
    month_transactions: int
    month_fraud_caught: int
    month_fraud_prevented_amount: float
    month_false_positive_rate: float
    month_accuracy: float

    # Distribution
    risk_distribution: Dict[str, int]  # {"low": 1124, "medium": 89, "high": 34}
    fraud_types: Dict[str, int]  # {"loan_stacking": 15, "sim_swap": 8, ...}


class TransactionHistory(BaseModel):
    """Transaction history item"""

    transaction_id: str
    amount: float
    risk_score: int
    risk_level: str
    decision: str
    outcome: Optional[str]  # fraud, legitimate, pending
    created_at: datetime


class ClientInfo(BaseModel):
    """Client information"""

    client_id: str
    company_name: str
    plan: str
    status: str
    total_checks: int
    total_fraud_caught: int
    total_amount_saved: float
    created_at: datetime


class RuleAccuracyInfo(BaseModel):
    """Rule accuracy information"""

    rule_name: str
    triggered_count: int
    accuracy: float
    precision: float
    recall: float
    current_weight: float


# Health check
class HealthCheck(BaseModel):
    """Health check response"""

    status: str
    version: str
    database: str
    redis: str
    timestamp: datetime
