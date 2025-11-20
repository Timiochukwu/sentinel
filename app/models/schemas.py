"""
Pydantic Schemas for Request/Response Validation

What are Pydantic schemas?
- Data validation models that ensure API requests/responses have correct structure
- Think of them like a "contract" - data must match the schema or it's rejected
- Automatic type checking, validation, and documentation generation

Why use Pydantic?
- Catches bugs early (invalid data rejected before reaching code)
- Auto-generates API documentation (FastAPI /docs shows all fields)
- Type safety (can't accidentally send string where number expected)
- Better error messages (tells users exactly what's wrong with their request)

Example:
    Without Pydantic:
        amount = request.get("amount")  # Could be None, string, anything!
        if not amount or not isinstance(amount, (int, float)) or amount < 0:
            return {"error": "Invalid amount"}

    With Pydantic:
        class TransactionRequest(BaseModel):
            amount: float = Field(..., ge=0)  # Must be float, must be >= 0

        # FastAPI automatically validates and rejects invalid requests!
        # No manual checking needed!

File Structure:
- Enums (TransactionType, Industry) - predefined valid values
- Request Schemas (TransactionCheckRequest) - API input validation
- Response Schemas (TransactionCheckResponse, FraudFlag) - API output structure
- Health/Analytics Schemas (HealthCheck, DashboardStats) - system status

All schemas are used by FastAPI for:
1. Request validation (reject invalid data)
2. Response serialization (convert Python objects to JSON)
3. API documentation (auto-generate OpenAPI/Swagger docs)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from decimal import Decimal
from enum import Enum


# ============================================================================
# ENUMS - Predefined Valid Values
# ============================================================================

class TransactionType(str, Enum):
    """
    Supported transaction types across all industries

    An Enum restricts values to a predefined list. This prevents typos
    and ensures consistency across the application.

    Why use Enums?
    - Type safety: Can't accidentally use "lone_disbursement" (typo)
    - Auto-complete: IDEs show all valid values
    - Documentation: Clear list of what's supported
    - Validation: FastAPI rejects invalid transaction types

    Example:
        Valid:   transaction_type="loan_disbursement"
        Invalid: transaction_type="loan"  # Rejected with 422 error

    Organized by industry vertical:
    - Fintech/Lending: Loans, transfers, withdrawals
    - E-commerce: Purchases, refunds, chargebacks
    - Betting/Gaming: Bets, withdrawals, bonus claims
    - Crypto: Deposits, withdrawals, P2P trades, swaps
    - Marketplace: Seller payouts, buyer payments, escrow
    """

    # Fintech/Lending - Traditional financial transactions
    LOAN_DISBURSEMENT = "loan_disbursement"  # Lender gives money to borrower
    LOAN_REPAYMENT = "loan_repayment"        # Borrower repays loan
    TRANSFER = "transfer"                     # Send money to another user
    WITHDRAWAL = "withdrawal"                 # Withdraw to bank account
    DEPOSIT = "deposit"                       # Add money to account
    BILL_PAYMENT = "bill_payment"            # Pay utility bills, airtime, etc.

    # E-commerce - Online shopping transactions
    PURCHASE = "purchase"                     # Buy product/service
    REFUND = "refund"                        # Return purchase
    CHARGEBACK = "chargeback"                # Dispute charge with bank
    CHECKOUT = "checkout"                     # Initialize checkout process

    # Betting/Gaming - Gambling and gaming transactions
    BET_PLACEMENT = "bet_placement"          # Place a bet
    BET_WITHDRAWAL = "bet_withdrawal"        # Withdraw winnings
    BONUS_CLAIM = "bonus_claim"              # Claim welcome/promotion bonus
    DEPOSIT_BONUS = "deposit_bonus"          # Deposit + receive bonus

    # Crypto - Cryptocurrency transactions
    CRYPTO_DEPOSIT = "crypto_deposit"        # Deposit crypto (buy)
    CRYPTO_WITHDRAWAL = "crypto_withdrawal"  # Withdraw crypto (sell)
    P2P_TRADE = "p2p_trade"                  # Peer-to-peer crypto trade
    SWAP = "swap"                            # Exchange one crypto for another
    STAKING = "staking"                      # Lock crypto for rewards

    # Marketplace - Multi-sided marketplace transactions
    SELLER_PAYOUT = "seller_payout"          # Pay seller for sale
    BUYER_PAYMENT = "buyer_payment"          # Buyer pays for product
    ESCROW_RELEASE = "escrow_release"        # Release escrowed funds
    MARKETPLACE_WITHDRAWAL = "marketplace_withdrawal"  # Withdraw marketplace earnings


class Industry(str, Enum):
    """
    Industry vertical

    Sentinel supports fraud detection across multiple industries.
    Each industry has specific fraud patterns and rules.

    Why separate industries?
    - Different fraud patterns (loan stacking vs bonus abuse)
    - Different risk factors (BVN for fintech, wallets for crypto)
    - Industry-specific fraud rules can be enabled/disabled

    Example:
        Fintech: Focus on loan stacking, SIM swap
        Betting: Focus on bonus abuse, multi-accounting
        Crypto: Focus on suspicious wallets, P2P velocity
    """
    FINTECH = "fintech"          # Digital banking, payments
    LENDING = "lending"          # Loan providers
    ECOMMERCE = "ecommerce"      # Online shopping
    BETTING = "betting"          # Sports betting
    GAMING = "gaming"            # Online gaming
    CRYPTO = "crypto"            # Cryptocurrency exchanges
    MARKETPLACE = "marketplace"  # Multi-sided marketplaces


# ============================================================================
# REQUEST SCHEMAS - API Input Validation
# ============================================================================

class TransactionCheckRequest(BaseModel):
    """
    Request schema for fraud detection check

    This is the main input to Sentinel's fraud detection API.
    Clients send transaction data in this format to check for fraud.

    Required fields:
    - transaction_id: Your unique transaction ID (for tracking)
    - user_id: User making the transaction
    - amount: Transaction amount in Nigerian Naira (₦)

    Optional but recommended fields:
    - device_id, ip_address: For device fingerprinting
    - account_age_days: How old is the user's account
    - phone_changed_recently: SIM swap indicator
    - Industry-specific fields (card_bin, wallet_address, etc.)

    Field Validation:
    - amount must be >= 0 (can't have negative transactions)
    - All fields have type checking (string, float, bool, etc.)
    - Invalid requests are rejected with clear error messages

    Example request:
        {
            "transaction_id": "txn_12345",
            "user_id": "user_789",
            "amount": 250000,
            "transaction_type": "loan_disbursement",
            "device_id": "iphone_abc",
            "account_age_days": 3,
            "phone_changed_recently": true
        }

    The more fields you provide, the more accurate fraud detection will be!
    """

    # REQUIRED FIELDS
    transaction_id: str = Field(..., description="Unique transaction identifier")
    user_id: str = Field(..., description="User identifier")
    amount: float = Field(..., description="Transaction amount in Naira", ge=0)  # ge=0 means "greater than or equal to 0"
    transaction_type: TransactionType = Field(
        default=TransactionType.LOAN_DISBURSEMENT,
        description="Type of transaction (loan_disbursement, purchase, bet_placement, etc.)"
    )
    industry: Industry = Field(
        default=Industry.LENDING,
        description="Industry vertical (fintech, lending, crypto, ecommerce, betting, marketplace, gaming)"
    )

    # Device and network info
    device_id: Optional[str] = Field(None, description="Device identifier")
    device_fingerprint: Optional[str] = Field(None, description="Browser fingerprint hash from FingerprintJS (for loan stacking detection)")
    fingerprint_components: Optional[Dict[str, Any]] = Field(None, description="Detailed fingerprint components (screen, canvas, WebGL, etc.)")
    ip_address: Optional[str] = Field(None, description="IP address of transaction")
    user_agent: Optional[str] = Field(None, description="Browser user agent")

    # Account info
    account_age_days: Optional[int] = Field(None, description="Age of account in days", ge=0)
    transaction_count: Optional[int] = Field(None, description="Previous transaction count", ge=0)

    # Contact changes
    phone_changed_recently: Optional[bool] = Field(False, description="Phone changed in last 48 hours")
    email_changed_recently: Optional[bool] = Field(False, description="Email changed in last 48 hours")
    address_changed_recently: Optional[bool] = Field(False, description="Address changed in last 7 days")

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

    # E-commerce specific fields
    card_bin: Optional[str] = Field(None, description="First 6 digits of card number")
    card_last4: Optional[str] = Field(None, description="Last 4 digits of card")
    card_type: Optional[str] = Field(None, description="Card type (debit, credit)")
    payment_method: Optional[str] = Field(None, description="Payment method (card, transfer, wallet)")
    shipping_address_matches_billing: Optional[bool] = Field(None, description="Address match flag")
    is_digital_goods: Optional[bool] = Field(None, description="Digital vs physical goods")

    # Betting/Gaming specific fields
    bet_count_today: Optional[int] = Field(None, description="Number of bets today", ge=0)
    bonus_balance: Optional[float] = Field(None, description="Current bonus balance", ge=0)
    withdrawal_count_today: Optional[int] = Field(None, description="Withdrawals today", ge=0)
    bet_pattern_unusual: Optional[bool] = Field(None, description="Unusual betting pattern detected")

    # Crypto specific fields
    wallet_address: Optional[str] = Field(None, description="Crypto wallet address")
    blockchain: Optional[str] = Field(None, description="Blockchain network (bitcoin, ethereum, etc)")
    is_new_wallet: Optional[bool] = Field(None, description="First time using this wallet")
    wallet_age_days: Optional[int] = Field(None, description="Age of wallet in days", ge=0)

    # Marketplace specific fields
    seller_id: Optional[str] = Field(None, description="Seller identifier")
    seller_rating: Optional[float] = Field(None, description="Seller rating 0-5", ge=0, le=5)
    seller_account_age_days: Optional[int] = Field(None, description="Seller account age", ge=0)
    product_category: Optional[str] = Field(None, description="Product category")
    is_high_value_item: Optional[bool] = Field(None, description="Item value >₦100k")

    class Config:
        json_schema_extra = {
            "example": {
                "transaction_id": "txn_12345",
                "user_id": "user_789",
                "amount": 250000,
                "transaction_type": "loan_disbursement",
                "industry": "lending",
                "device_id": "abc123",
                "ip_address": "197.210.226.45",
                "account_age_days": 3,
                "transaction_count": 0,
                "phone_changed_recently": True,
                "email_changed_recently": False
            },
            "title": "Fraud Detection Request"
        }


# ============================================================================
# RESPONSE SCHEMAS - API Output Structure
# ============================================================================

class FraudFlag(BaseModel):
    """
    Individual fraud flag/indicator

    When a fraud rule is triggered, it creates a FraudFlag that explains:
    - What fraud pattern was detected
    - How severe it is
    - How much it contributes to the overall risk score

    Multiple flags can be triggered for a single transaction.
    All flags are combined to calculate the final risk score.

    Example:
        A new account requesting a large loan might trigger:
        1. FraudFlag(type="new_account_large_amount", score=30, severity="medium")
        2. FraudFlag(type="sim_swap_pattern", score=45, severity="critical")
        Total risk score = 30 + 45 = 75 (high risk)

    Fields:
    - type: Machine-readable fraud pattern name (e.g., "loan_stacking")
    - severity: Human-readable severity (low, medium, high, critical)
    - message: Plain English explanation of what's suspicious
    - score: How many points this adds to risk score (0-100)
    - confidence: How confident we are (0.0-1.0, where 1.0 = 100% certain)
    - metadata: Extra details (e.g., list of lenders for loan stacking)
    """

    type: str = Field(..., description="Type of fraud flag (e.g., 'loan_stacking', 'sim_swap_pattern')")
    severity: str = Field(..., description="Severity level (low, medium, high, critical)")
    message: str = Field(..., description="Human-readable explanation of what's suspicious")
    score: int = Field(..., description="Risk score contribution (0-100)", ge=0, le=100)
    confidence: Optional[float] = Field(None, description="Confidence level (0.0-1.0)", ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context (varies by flag type)")


class TransactionCheckResponse(BaseModel):
    """
    Response schema for fraud detection check

    This is what Sentinel returns after analyzing a transaction.
    It contains everything you need to make a decision.

    Key fields:
    - risk_score: 0-100 score (0 = safe, 100 = definitely fraud)
    - decision: What to do (approve, review, decline)
    - flags: List of specific fraud indicators detected
    - recommendation: Human-readable advice for customer service

    Risk Score Ranges:
    - 0-39: LOW RISK → Approve automatically
    - 40-69: MEDIUM RISK → Manual review recommended
    - 70-100: HIGH RISK → Decline or require strong verification

    Example response:
        {
            "transaction_id": "txn_12345",
            "risk_score": 75,
            "risk_level": "high",
            "decision": "decline",
            "flags": [
                {
                    "type": "new_account_large_amount",
                    "severity": "medium",
                    "message": "Account only 3 days old requesting ₦500,000",
                    "score": 30
                },
                {
                    "type": "sim_swap_pattern",
                    "severity": "critical",
                    "message": "Phone changed + new device + withdrawal",
                    "score": 45
                }
            ],
            "recommendation": "DECLINE - High risk of SIM swap attack",
            "processing_time_ms": 87
        }

    What to do with the response:
    - If decision="approve": Process transaction automatically
    - If decision="review": Send to manual review queue
    - If decision="decline": Reject or require video verification
    - Always show recommendation to customer service team
    - Store flags for fraud analysis and ML training
    """

    transaction_id: str  # Echo back the transaction ID from request
    risk_score: int = Field(..., description="Risk score 0-100 (0=safe, 100=fraud)", ge=0, le=100)
    risk_level: str = Field(..., description="Risk level: low, medium, or high")
    decision: str = Field(..., description="Recommended decision: approve, review, or decline")
    flags: List[FraudFlag] = Field(default=[], description="List of fraud flags detected (empty list if no flags)")
    recommendation: Optional[str] = Field(None, description="Human-readable recommendation for customer service")
    processing_time_ms: int = Field(..., description="How long fraud detection took (in milliseconds)")

    # Consortium intelligence (only included if available)
    consortium_alerts: Optional[List[str]] = Field(
        None,
        description="Alerts from consortium intelligence (e.g., 'Applied to 3 other lenders this week')"
    )

    # Cache indicator (only included if this is a cached/duplicate transaction result)
    cached: Optional[bool] = Field(
        None,
        description="True if this result was retrieved from cache or duplicate transaction check"
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
