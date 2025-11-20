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
# datetime already imported above


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
# FEATURE CATEGORY SCHEMAS (Phases 4-12: 249+ Features)
# ============================================================================

# PHASE 4: IDENTITY FEATURES (40 features)
class IdentityEmailFeatures(BaseModel):
    """Email identity features (5 features)"""
    address: Optional[str] = None
    domain: Optional[str] = None
    age_days: Optional[int] = Field(None, ge=0)
    reputation_score: Optional[int] = Field(None, ge=0, le=100)
    verification_status: Optional[bool] = None
    class Config:
        extra = "allow"

class IdentityPhoneFeatures(BaseModel):
    """Phone identity features (5 features)"""
    number: Optional[str] = None
    age_days: Optional[int] = Field(None, ge=0)
    country_code: Optional[str] = None
    verification_status: Optional[bool] = None
    carrier_risk: Optional[int] = Field(None, ge=0, le=100)
    class Config:
        extra = "allow"

class IdentityBVNFeatures(BaseModel):
    """BVN/ID identity features (3 features)"""
    bvn: Optional[str] = None
    nin: Optional[str] = None
    verification_status: Optional[bool] = None
    class Config:
        extra = "allow"

class IdentityDeviceFeatures(BaseModel):
    """Device identity features (12 features)"""
    fingerprint: Optional[str] = None
    browser_type: Optional[str] = None
    browser_version: Optional[str] = None
    os: Optional[str] = None
    screen_resolution: Optional[str] = None
    timezone: Optional[str] = None
    installed_fonts: Optional[List[str]] = None
    canvas_fingerprint: Optional[str] = None
    webgl_fingerprint: Optional[str] = None
    gpu_info: Optional[str] = None
    cpu_cores: Optional[int] = None
    battery_level: Optional[int] = Field(None, ge=0, le=100)
    class Config:
        extra = "allow"

class IdentityNetworkFeatures(BaseModel):
    """Network identity features (10 features)"""
    ip_address: Optional[str] = None
    ip_city: Optional[str] = None
    ip_country: Optional[str] = None
    ip_reputation: Optional[int] = Field(None, ge=0, le=100)
    vpn_detected: Optional[bool] = None
    proxy_detected: Optional[bool] = None
    tor_detected: Optional[bool] = None
    datacenter_ip: Optional[bool] = None
    isp: Optional[str] = None
    asn: Optional[str] = None
    class Config:
        extra = "allow"

class IdentityFeatures(BaseModel):
    """Phase 4: All identity features (40 total)"""
    email: Optional[IdentityEmailFeatures] = None
    phone: Optional[IdentityPhoneFeatures] = None
    bvn: Optional[IdentityBVNFeatures] = None
    device: Optional[IdentityDeviceFeatures] = None
    network: Optional[IdentityNetworkFeatures] = None
    class Config:
        extra = "allow"

# PHASE 5: BEHAVIORAL FEATURES (60 features)
class BehavioralSessionFeatures(BaseModel):
    """Session behavior features (15 features)"""
    mouse_movement_score: Optional[int] = Field(None, ge=0, le=100)
    typing_speed_wpm: Optional[int] = None
    keystroke_dynamics_score: Optional[int] = Field(None, ge=0, le=100)
    copy_paste_count: Optional[int] = None
    time_on_page_seconds: Optional[int] = None
    pages_visited: Optional[int] = None
    click_count: Optional[int] = None
    scroll_count: Optional[int] = None
    session_duration_seconds: Optional[int] = None
    navigation_path: Optional[List[str]] = None
    form_field_time_seconds: Optional[int] = None
    hesitation_detected: Optional[bool] = None
    error_corrections: Optional[int] = None
    tab_switches: Optional[int] = None
    window_resized: Optional[bool] = None
    class Config:
        extra = "allow"

class BehavioralLoginFeatures(BaseModel):
    """Login behavior features (13 features)"""
    login_frequency: Optional[int] = None
    login_time_hour: Optional[int] = Field(None, ge=0, le=23)
    failed_login_attempts_24h: Optional[int] = None
    failed_login_velocity: Optional[int] = None
    password_reset_requests: Optional[int] = None
    password_reset_txn_time_gap: Optional[int] = None
    two_factor_enabled: Optional[bool] = None
    biometric_auth: Optional[bool] = None
    social_login: Optional[bool] = None
    remember_me_used: Optional[bool] = None
    autofill_used: Optional[bool] = None
    new_device_login: Optional[bool] = None
    unusual_location_login: Optional[bool] = None
    class Config:
        extra = "allow"

class BehavioralTransactionFeatures(BaseModel):
    """Transaction behavior features (17 features)"""
    velocity_last_hour: Optional[int] = None
    velocity_last_day: Optional[int] = None
    velocity_last_week: Optional[int] = None
    transaction_count_lifetime: Optional[int] = None
    avg_transaction_amount: Optional[float] = None
    max_transaction_amount: Optional[float] = None
    min_transaction_amount: Optional[float] = None
    txn_time_hour: Optional[int] = Field(None, ge=0, le=23)
    txn_day_of_week: Optional[int] = Field(None, ge=0, le=6)
    holiday_transaction: Optional[bool] = None
    weekend_transaction: Optional[bool] = None
    after_hours_transaction: Optional[bool] = None
    first_transaction_amount: Optional[float] = None
    time_since_last_txn_hours: Optional[int] = None
    time_since_signup_days: Optional[int] = None
    txn_to_signup_ratio: Optional[float] = None
    new_funding_immediate_withdrawal: Optional[bool] = None
    class Config:
        extra = "allow"

class BehavioralInteractionFeatures(BaseModel):
    """Interaction behavior features (15 features)"""
    referrer_source: Optional[str] = None
    campaign_tracking: Optional[str] = None
    utm_parameters: Optional[Dict[str, str]] = None
    ad_click: Optional[bool] = None
    api_calls_made: Optional[int] = None
    api_errors: Optional[int] = None
    swipe_gestures_count: Optional[int] = None
    pinch_zoom_count: Optional[int] = None
    app_switches: Optional[int] = None
    screen_orientation_changes: Optional[int] = None
    home_button_pressed: Optional[bool] = None
    notification_interacted: Optional[bool] = None
    deeplink_used: Optional[bool] = None
    page_refresh_count: Optional[int] = None
    browser_back_button: Optional[int] = None
    class Config:
        extra = "allow"

class BehavioralFeatures(BaseModel):
    """Phase 5: All behavioral features (60 total)"""
    session: Optional[BehavioralSessionFeatures] = None
    login: Optional[BehavioralLoginFeatures] = None
    transaction: Optional[BehavioralTransactionFeatures] = None
    interaction: Optional[BehavioralInteractionFeatures] = None
    class Config:
        extra = "allow"

# PHASE 6: TRANSACTION FEATURES (40 features)
class TransactionCardFeatures(BaseModel):
    """Card transaction features (9 features)"""
    bin: Optional[str] = None
    last_four: Optional[str] = None
    expiry_date: Optional[str] = None
    card_country: Optional[str] = None
    card_age_days: Optional[int] = None
    card_reputation_score: Optional[int] = Field(None, ge=0, le=100)
    new_card_large_withdrawal: Optional[bool] = None
    card_testing_pattern: Optional[bool] = None
    multiple_cards_same_device: Optional[int] = None
    class Config:
        extra = "allow"

class TransactionBankingFeatures(BaseModel):
    """Banking transaction features (4 features)"""
    account_number: Optional[str] = None
    account_age_days: Optional[int] = None
    new_account_withdrawal: Optional[bool] = None
    account_verification: Optional[bool] = None
    class Config:
        extra = "allow"

class TransactionAddressFeatures(BaseModel):
    """Address transaction features (3 features)"""
    billing_address: Optional[str] = None
    shipping_address: Optional[str] = None
    address_distance_km: Optional[float] = None
    class Config:
        extra = "allow"

class TransactionCryptoFeatures(BaseModel):
    """Crypto transaction features (5 features)"""
    wallet_address: Optional[str] = None
    wallet_reputation: Optional[int] = Field(None, ge=0, le=100)
    wallet_age_days: Optional[int] = None
    deposit_within_24h: Optional[bool] = None
    withdrawal_after_deposit: Optional[bool] = None
    class Config:
        extra = "allow"

class TransactionMerchantFeatures(BaseModel):
    """Merchant transaction features (5 features)"""
    merchant_category: Optional[str] = None
    merchant_high_risk: Optional[bool] = None
    merchant_fraud_cluster: Optional[bool] = None
    merchant_chargeback_rate: Optional[float] = None
    merchant_refund_rate: Optional[float] = None
    class Config:
        extra = "allow"

class TransactionFeatures(BaseModel):
    """Phase 6: All transaction features (40 total)"""
    card: Optional[TransactionCardFeatures] = None
    banking: Optional[TransactionBankingFeatures] = None
    address: Optional[TransactionAddressFeatures] = None
    crypto: Optional[TransactionCryptoFeatures] = None
    merchant: Optional[TransactionMerchantFeatures] = None
    class Config:
        extra = "allow"

# PHASE 7: NETWORK/CONSORTIUM FEATURES (40 features)
class NetworkConsortiumMatching(BaseModel):
    """Consortium matching features (8 features)"""
    email_seen_elsewhere: Optional[bool] = None
    phone_seen_elsewhere: Optional[bool] = None
    device_seen_elsewhere: Optional[bool] = None
    ip_seen_elsewhere: Optional[bool] = None
    card_seen_elsewhere: Optional[bool] = None
    address_seen_elsewhere: Optional[bool] = None
    bank_account_seen_elsewhere: Optional[bool] = None
    bvn_seen_elsewhere: Optional[bool] = None
    class Config:
        extra = "allow"

class NetworkFraudLinkage(BaseModel):
    """Fraud linkage features (8 features)"""
    email_linked_to_fraud: Optional[bool] = None
    phone_linked_to_fraud: Optional[bool] = None
    device_linked_to_fraud: Optional[bool] = None
    ip_linked_to_fraud: Optional[bool] = None
    card_linked_to_fraud: Optional[bool] = None
    address_linked_to_fraud: Optional[bool] = None
    bank_account_linked_to_fraud: Optional[bool] = None
    bvn_linked_to_fraud: Optional[bool] = None
    class Config:
        extra = "allow"

class NetworkVelocity(BaseModel):
    """Network velocity features (7 features)"""
    velocity_email: Optional[int] = None
    velocity_phone: Optional[int] = None
    velocity_device: Optional[int] = None
    velocity_ip: Optional[int] = None
    velocity_card: Optional[int] = None
    velocity_bank_account: Optional[int] = None
    velocity_bvn: Optional[int] = None
    class Config:
        extra = "allow"

class NetworkGraphAnalysis(BaseModel):
    """Graph analysis features (10 features)"""
    connected_accounts_detected: Optional[bool] = None
    fraud_ring_detected: Optional[bool] = None
    same_ip_multiple_users: Optional[int] = None
    same_device_multiple_users: Optional[int] = None
    same_address_multiple_users: Optional[int] = None
    same_bvn_multiple_accounts: Optional[int] = None
    same_contact_multiple_users: Optional[int] = None
    synthetic_identity_cluster: Optional[bool] = None
    money_mule_network_detected: Optional[bool] = None
    loan_stacking_ring_detected: Optional[bool] = None
    class Config:
        extra = "allow"

class NetworkFeatures(BaseModel):
    """Phase 7: All network features (40 total)"""
    consortium_matching: Optional[NetworkConsortiumMatching] = None
    fraud_linkage: Optional[NetworkFraudLinkage] = None
    velocity: Optional[NetworkVelocity] = None
    graph_analysis: Optional[NetworkGraphAnalysis] = None
    class Config:
        extra = "allow"

# PHASE 8: ACCOUNT TAKEOVER (ATO) SIGNALS (15 features)
class ATOClassicPatterns(BaseModel):
    """Classic ATO patterns (10 features)"""
    password_reset_txn: Optional[bool] = None
    failed_login_velocity: Optional[int] = None
    new_device_behavior_change: Optional[bool] = None
    password_change_withdrawal: Optional[bool] = None
    geographic_impossibility: Optional[bool] = None
    new_device_high_value: Optional[bool] = None
    device_change_behavior_change: Optional[bool] = None
    suspicious_location_login: Optional[bool] = None
    multiple_failed_logins_ips: Optional[bool] = None
    session_hijacking_detected: Optional[bool] = None
    class Config:
        extra = "allow"

class ATOBehavioralDeviation(BaseModel):
    """Behavioral deviation features (5 features)"""
    typing_pattern_deviation: Optional[bool] = None
    mouse_movement_deviation: Optional[bool] = None
    navigation_pattern_deviation: Optional[bool] = None
    transaction_pattern_deviation: Optional[bool] = None
    time_of_day_deviation: Optional[bool] = None
    class Config:
        extra = "allow"

class ATOSignals(BaseModel):
    """Phase 8: All ATO signals (15 total)"""
    classic_patterns: Optional[ATOClassicPatterns] = None
    behavioral_deviation: Optional[ATOBehavioralDeviation] = None
    class Config:
        extra = "allow"

# PHASE 9: FUNDING SOURCE FRAUD (10 features)
class FundingNewSources(BaseModel):
    """New funding source features (5 features)"""
    new_card_withdrawal: Optional[bool] = None
    new_bank_account_withdrawal: Optional[bool] = None
    card_added_withdrew_same_day: Optional[bool] = None
    multiple_sources_added_quickly: Optional[bool] = None
    funding_source_high_risk_country: Optional[bool] = None
    class Config:
        extra = "allow"

class FundingCardTesting(BaseModel):
    """Card testing features (5 features)"""
    dollar_one_authorizations: Optional[int] = None
    small_fails_large_success: Optional[bool] = None
    multiple_cards_tested_device: Optional[bool] = None
    bin_attack_pattern: Optional[bool] = None
    funding_source_velocity: Optional[int] = None
    class Config:
        extra = "allow"

class FundingFraudSignals(BaseModel):
    """Phase 9: All funding fraud signals (10 total)"""
    new_sources: Optional[FundingNewSources] = None
    card_testing: Optional[FundingCardTesting] = None
    class Config:
        extra = "allow"

# PHASE 10: MERCHANT-LEVEL ABUSE (10 features)
class MerchantRisk(BaseModel):
    """Merchant risk features (4 features)"""
    high_risk_category: Optional[bool] = None
    merchant_fraud_cluster: Optional[bool] = None
    merchant_chargeback_rate: Optional[float] = None
    merchant_refund_rate: Optional[float] = None
    class Config:
        extra = "allow"

class MerchantAbusePatterns(BaseModel):
    """Merchant abuse features (6 features)"""
    refund_abuse_detected: Optional[bool] = None
    cashback_abuse_detected: Optional[bool] = None
    promo_abuse_detected: Optional[bool] = None
    loyalty_points_abuse: Optional[bool] = None
    referral_fraud: Optional[bool] = None
    fake_merchant_transactions: Optional[bool] = None
    class Config:
        extra = "allow"

class MerchantAbuseSignals(BaseModel):
    """Phase 10: All merchant abuse signals (10 total)"""
    merchant_risk: Optional[MerchantRisk] = None
    abuse_patterns: Optional[MerchantAbusePatterns] = None
    class Config:
        extra = "allow"

# PHASE 11: ML-DERIVED FEATURES (9 features)
class MLStatisticalOutliers(BaseModel):
    """Statistical outlier features (3 features)"""
    outlier_score: Optional[float] = Field(None, ge=0, le=1)
    anomaly_score: Optional[float] = Field(None, ge=0, le=1)
    z_score: Optional[float] = None
    class Config:
        extra = "allow"

class MLModelScores(BaseModel):
    """ML model score features (4 features)"""
    xgboost_risk_score: Optional[float] = Field(None, ge=0, le=1)
    neural_network_score: Optional[float] = Field(None, ge=0, le=1)
    random_forest_score: Optional[float] = Field(None, ge=0, le=1)
    ensemble_model_score: Optional[float] = Field(None, ge=0, le=1)
    class Config:
        extra = "allow"

class MLDeepLearning(BaseModel):
    """Deep learning features (2 features)"""
    lstm_sequence_prediction: Optional[float] = Field(None, ge=0, le=1)
    gnn_graph_score: Optional[float] = Field(None, ge=0, le=1)
    class Config:
        extra = "allow"

class MLDerivedFeatures(BaseModel):
    """Phase 11: All ML-derived features (9 total)"""
    statistical_outliers: Optional[MLStatisticalOutliers] = None
    model_scores: Optional[MLModelScores] = None
    deep_learning: Optional[MLDeepLearning] = None
    class Config:
        extra = "allow"

# PHASE 12: DERIVED/COMPUTED FEATURES (25 features)
class DerivedSimilarity(BaseModel):
    """Similarity features (6 features)"""
    fraudster_profile_similarity: Optional[float] = Field(None, ge=0, le=1)
    username_similarity: Optional[float] = Field(None, ge=0, le=1)
    email_similarity: Optional[float] = Field(None, ge=0, le=1)
    address_similarity: Optional[float] = Field(None, ge=0, le=1)
    behavior_similarity: Optional[float] = Field(None, ge=0, le=1)
    transaction_pattern_similarity: Optional[float] = Field(None, ge=0, le=1)
    class Config:
        extra = "allow"

class DerivedLinkage(BaseModel):
    """Linkage features (4 features)"""
    entity_resolution_score: Optional[float] = Field(None, ge=0, le=1)
    identity_matching_score: Optional[float] = Field(None, ge=0, le=1)
    soft_linking_score: Optional[float] = Field(None, ge=0, le=1)
    hard_linking_score: Optional[float] = Field(None, ge=0, le=1)
    class Config:
        extra = "allow"

class DerivedClustering(BaseModel):
    """Clustering features (7 features)"""
    family_connections_detected: Optional[bool] = None
    business_connections_detected: Optional[bool] = None
    geographic_connections_detected: Optional[bool] = None
    temporal_connections_detected: Optional[bool] = None
    community_detection_score: Optional[float] = Field(None, ge=0, le=1)
    cluster_membership_score: Optional[float] = Field(None, ge=0, le=1)
    graph_centrality_score: Optional[float] = Field(None, ge=0, le=1)
    class Config:
        extra = "allow"

class DerivedAggregateRisk(BaseModel):
    """Aggregate risk features (8 features)"""
    final_risk_score: Optional[int] = Field(None, ge=0, le=100)
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    explainability_score: Optional[float] = Field(None, ge=0, le=1)
    feature_importance_ranking: Optional[List[str]] = None
    fraud_probability: Optional[float] = Field(None, ge=0, le=1)
    false_positive_probability: Optional[float] = Field(None, ge=0, le=1)
    model_prediction: Optional[str] = None
    rule_violations_count: Optional[int] = None
    class Config:
        extra = "allow"

class DerivedFeatures(BaseModel):
    """Phase 12: All derived/computed features (25 total)"""
    similarity: Optional[DerivedSimilarity] = None
    linkage: Optional[DerivedLinkage] = None
    clustering: Optional[DerivedClustering] = None
    aggregate_risk: Optional[DerivedAggregateRisk] = None
    class Config:
        extra = "allow"


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

    # PHASE 1 FEATURES (10 new fraud detection features)
    # 1. Email age/reputation
    email_domain_age_days: Optional[int] = Field(None, description="Email domain age in days", ge=0)
    email_reputation_score: Optional[int] = Field(None, description="Email reputation 0-100", ge=0, le=100)

    # 2. IP reputation
    ip_reputation_score: Optional[int] = Field(None, description="IP reputation 0-100", ge=0, le=100)

    # 3. Failed login attempts
    failed_login_count_24h: Optional[int] = Field(0, description="Failed logins in 24h", ge=0)
    failed_login_count_7d: Optional[int] = Field(0, description="Failed logins in 7 days", ge=0)

    # 4. Time of day analysis
    transaction_hour: Optional[int] = Field(None, description="Hour of transaction (0-23)", ge=0, le=23)
    is_unusual_time: Optional[bool] = Field(False, description="Transaction at unusual hours")

    # 5. First transaction amount
    first_transaction_amount: Optional[float] = Field(None, description="User's first transaction amount", ge=0)

    # 6. Card BIN reputation
    card_bin_reputation_score: Optional[int] = Field(None, description="Card BIN reputation 0-100", ge=0, le=100)

    # 7. Phone verification status
    phone_verified: Optional[bool] = Field(False, description="Is phone number verified")
    phone_verification_method: Optional[str] = Field(None, description="Verification method (sms, call, app)")

    # 9. Transaction vs signup time gap
    account_signup_date: Optional[datetime] = Field(None, description="When account was created")
    days_since_signup: Optional[int] = Field(None, description="Days since account signup", ge=0)

    # 10. Platform/OS consistency
    platform_os: Optional[str] = Field(None, description="Platform/OS (iOS 14.5, Android 11, Windows 10, etc)")
    platform_os_consistent: Optional[bool] = Field(None, description="Is OS consistent with user history")

    # PHASE 2 FEATURES (20 new features for 80-85% detection)
    # Browser fingerprinting
    browser_fonts_hash: Optional[str] = Field(None, description="Hash of installed browser fonts")
    canvas_fingerprint: Optional[str] = Field(None, description="Canvas fingerprint hash")
    webgl_fingerprint: Optional[str] = Field(None, description="WebGL fingerprint hash")
    screen_resolution: Optional[str] = Field(None, description="Screen resolution (e.g. 1920x1080)")
    timezone_offset: Optional[int] = Field(None, description="Timezone UTC offset in minutes")

    # Behavioral analytics
    session_duration_seconds: Optional[int] = Field(None, description="Session duration in seconds", ge=0)
    mouse_movement_score: Optional[int] = Field(None, description="Mouse movement humanness 0-100", ge=0, le=100)
    typing_speed_wpm: Optional[int] = Field(None, description="Typing speed in WPM", ge=0)
    copy_paste_count: Optional[int] = Field(None, description="Copy/paste actions count", ge=0)

    # Identity verification
    social_media_verified: Optional[bool] = Field(False, description="Social media profile verified")
    social_media_age_days: Optional[int] = Field(None, description="Social media account age", ge=0)
    address_verified: Optional[bool] = Field(False, description="Address verified by 3rd party")

    # Transaction patterns
    shipping_distance_km: Optional[int] = Field(None, description="Distance billing to shipping", ge=0)
    transaction_frequency_per_day: Optional[float] = Field(None, description="Avg transactions per day", ge=0)
    avg_transaction_amount: Optional[float] = Field(None, description="User avg transaction amount", ge=0)
    chargeback_history_count: Optional[int] = Field(0, description="Total chargebacks", ge=0)
    refund_history_count: Optional[int] = Field(0, description="Total refunds", ge=0)
    holiday_weekend_transaction: Optional[bool] = Field(False, description="Transaction on holiday/weekend")

    # PHASE 3 FEATURES (50 new features for 85-90% detection)
    # Behavioral biometrics
    keystroke_dynamics_score: Optional[int] = Field(None, description="Keystroke biometric 0-100", ge=0, le=100)
    swipe_pattern_score: Optional[int] = Field(None, description="Swipe pattern 0-100", ge=0, le=100)
    touch_pressure_consistent: Optional[bool] = Field(None, description="Touch pressure consistent")
    acceleration_pattern_score: Optional[int] = Field(None, description="Device acceleration pattern 0-100", ge=0, le=100)
    scroll_behavior_score: Optional[int] = Field(None, description="Scroll behavior 0-100", ge=0, le=100)

    # Network graph analysis
    co_user_count: Optional[int] = Field(None, description="Users sharing same device/IP/email", ge=0)
    shared_email_with_fraud: Optional[bool] = Field(False, description="Email linked to fraud")
    shared_phone_with_fraud: Optional[bool] = Field(False, description="Phone linked to fraud")
    shared_device_with_fraud: Optional[bool] = Field(False, description="Device linked to fraud")
    shared_ip_with_fraud: Optional[bool] = Field(False, description="IP linked to fraud")

    # Entity clustering
    first_name_uniqueness: Optional[float] = Field(None, description="First name uniqueness 0-1", ge=0, le=1)
    last_name_uniqueness: Optional[float] = Field(None, description="Last name uniqueness 0-1", ge=0, le=1)
    email_domain_legitimacy: Optional[int] = Field(None, description="Email domain legitimacy 0-100", ge=0, le=100)
    phone_carrier_risk: Optional[int] = Field(None, description="Phone carrier risk 0-100", ge=0, le=100)
    bvn_fraud_match_count: Optional[int] = Field(0, description="BVN fraud matches", ge=0)

    # Relationship mapping
    family_member_with_fraud: Optional[bool] = Field(False, description="Family member has fraud")
    known_fraudster_pattern: Optional[bool] = Field(False, description="Matches known fraudster pattern")
    linked_to_synthetic_fraud: Optional[bool] = Field(False, description="Synthetic identity indicator")
    velocity_between_verticals: Optional[int] = Field(None, description="Cross-vertical velocity", ge=0)
    account_resurrection_attempt: Optional[bool] = Field(False, description="Old account reactivation")

    # Historical pattern matching
    account_history_matches_fraud: Optional[int] = Field(None, description="Fraud pattern matches", ge=0)
    merchant_mcc_history: Optional[List[str]] = Field(None, description="MCC codes history")
    previously_declined_transaction: Optional[bool] = Field(False, description="Was previously declined")
    refund_abuse_pattern: Optional[bool] = Field(False, description="Serial refund pattern")
    chargeback_abuse_pattern: Optional[bool] = Field(False, description="Serial chargeback pattern")

    # ML-derived features
    entropy_score: Optional[float] = Field(None, description="Information entropy 0-1", ge=0, le=1)
    anomaly_score: Optional[float] = Field(None, description="ML anomaly score 0-1", ge=0, le=1)
    transaction_legitimacy_score: Optional[int] = Field(None, description="Legitimacy 0-100", ge=0, le=100)
    user_profile_deviation: Optional[float] = Field(None, description="Profile deviation 0-1", ge=0, le=1)
    risk_factor_clustering: Optional[Dict[str, Any]] = Field(None, description="Grouped risk factors")

    # Device intelligence
    device_manufacturer_risk: Optional[int] = Field(None, description="Manufacturer risk 0-100", ge=0, le=100)
    device_model_age_months: Optional[int] = Field(None, description="Device model age", ge=0)
    emulator_detected: Optional[bool] = Field(False, description="Emulator detected")
    jailbreak_detected: Optional[bool] = Field(False, description="Jailbreak/root detected")
    suspicious_app_installed: Optional[bool] = Field(False, description="Malware/fraud app found")

    # Industry-specific signals
    lending_cross_sell_pattern: Optional[bool] = Field(False, description="Lending cross-sell fraud")
    ecommerce_dropshipper_pattern: Optional[bool] = Field(False, description="Dropshipping fraud")
    crypto_pump_dump_signal: Optional[bool] = Field(False, description="Pump & dump signal")
    betting_arbitrage_likelihood: Optional[int] = Field(None, description="Arbitrage likelihood 0-100", ge=0, le=100)
    marketplace_seller_collusion: Optional[bool] = Field(False, description="Seller collusion")

    # Complex pattern detection
    transaction_pattern_entropy: Optional[float] = Field(None, description="Pattern entropy 0-1", ge=0, le=1)
    behavioral_consistency_score: Optional[int] = Field(None, description="Behavior consistency 0-100", ge=0, le=100)
    account_age_velocity_ratio: Optional[float] = Field(None, description="Age/velocity ratio", ge=0)
    geographic_consistency_score: Optional[int] = Field(None, description="Geographic consistency 0-100", ge=0, le=100)
    temporal_consistency_score: Optional[int] = Field(None, description="Temporal consistency 0-100", ge=0, le=100)

    # Cross-transaction analytics
    multi_account_cross_funding: Optional[bool] = Field(False, description="Cross-account funding")
    round_trip_transaction: Optional[bool] = Field(False, description="Money out and back")
    test_transaction_pattern: Optional[bool] = Field(False, description="Small before large pattern")
    rapid_account_progression: Optional[bool] = Field(False, description="Quick tier upgrade")
    suspicious_beneficiary_pattern: Optional[bool] = Field(False, description="Abnormal beneficiary")

    # Advanced ML features
    deep_learning_fraud_score: Optional[float] = Field(None, description="DL model score 0-1", ge=0, le=1)
    ensemble_model_confidence: Optional[float] = Field(None, description="Ensemble confidence 0-1", ge=0, le=1)

    # PHASES 4-12: COMPREHENSIVE FEATURE CATEGORIES (249+ features)
    # Phase 4: Identity Features (40 features)
    identity_features: Optional[IdentityFeatures] = Field(None, description="Email, phone, BVN, device, network identity")

    # Phase 5: Behavioral Features (60 features)
    behavioral_features: Optional[BehavioralFeatures] = Field(None, description="Session, login, transaction, interaction patterns")

    # Phase 6: Transaction Features (40 features)
    transaction_features: Optional[TransactionFeatures] = Field(None, description="Card, banking, address, crypto, merchant data")

    # Phase 7: Network/Consortium Features (40 features)
    network_features: Optional[NetworkFeatures] = Field(None, description="Fraud linkage and graph analysis")

    # Phase 8: Account Takeover Signals (15 features)
    ato_signals: Optional[ATOSignals] = Field(None, description="Classic ATO patterns and behavioral deviations")

    # Phase 9: Funding Source Fraud (10 features)
    funding_fraud_signals: Optional[FundingFraudSignals] = Field(None, description="Card testing and new funding abuse")

    # Phase 10: Merchant-Level Abuse (10 features)
    merchant_abuse_signals: Optional[MerchantAbuseSignals] = Field(None, description="Merchant risk and abuse patterns")

    # Phase 11: ML-Derived Features (9 features)
    ml_derived_features: Optional[MLDerivedFeatures] = Field(None, description="Statistical outliers and ML model scores")

    # Phase 12: Derived/Computed Features (25 features)
    derived_features: Optional[DerivedFeatures] = Field(None, description="Similarity, linkage, clustering, and aggregate risk")

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
