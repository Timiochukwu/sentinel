"""Database models for Sentinel"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, Numeric, DateTime,
    Index, JSON, Text, TIMESTAMP
)
from sqlalchemy.dialects.postgresql import INET, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func


Base = declarative_base()


class Transaction(Base):
    """Transaction table - stores all fraud check requests and results"""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(255), unique=True, nullable=False, index=True)
    client_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_type = Column(String(50))
    industry = Column(String(50), default="lending", nullable=False, index=True)  # New: industry vertical (fintech, lending, crypto, ecommerce, betting, marketplace, gaming)

    # Detection inputs
    device_id = Column(String(255))
    device_fingerprint = Column(String(255), index=True)  # Stable browser fingerprint for fraud detection
    fingerprint_components = Column(JSONB)  # Detailed fingerprint data for forensics
    ip_address = Column(INET)
    account_age_days = Column(Integer)
    transaction_count = Column(Integer)
    phone_changed_recently = Column(Boolean, default=False)
    email_changed_recently = Column(Boolean, default=False)
    bvn = Column(String(255))  # Will be hashed before storage
    phone = Column(String(50))  # Will be hashed before storage
    email = Column(String(255))  # Will be hashed before storage

    # Geolocation
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    city = Column(String(100))
    country = Column(String(100))

    # PHASE 1 FEATURES (10 new features for 70% fraud detection)
    # 1. Email age/reputation
    email_domain_age_days = Column(Integer)  # How old is the email domain
    email_reputation_score = Column(Integer)  # 0-100 reputation score

    # 2. IP reputation
    ip_reputation_score = Column(Integer)  # 0-100, 100=clean, 0=known fraud IP

    # 3. Failed login attempts
    failed_login_count_24h = Column(Integer, default=0)  # Failed logins in 24h
    failed_login_count_7d = Column(Integer, default=0)   # Failed logins in 7 days
    last_failed_login_at = Column(TIMESTAMP)

    # 4. Time of day analysis
    transaction_hour = Column(Integer)  # Hour of transaction (0-23)
    is_unusual_time = Column(Boolean, default=False)  # Outside normal hours

    # 5. First transaction amount
    first_transaction_amount = Column(Numeric(15, 2))  # User's first transaction amount

    # 6. Card BIN reputation (stored here for quick access)
    card_bin_reputation_score = Column(Integer)  # 0-100 reputation

    # 7. Phone verification status
    phone_verified = Column(Boolean, default=False)
    phone_verified_at = Column(TIMESTAMP)
    phone_verification_method = Column(String(50))  # sms, call, app

    # 8. Multiple accounts same device (already have device_fingerprint)
    # Can be calculated from device_fingerprint count

    # 9. Transaction vs signup time gap
    account_signup_date = Column(TIMESTAMP)  # When account was created
    days_since_signup = Column(Integer)  # Calculated field: now - signup_date

    # 10. Platform/OS consistency
    platform_os = Column(String(100))  # "iOS 14.5", "Android 11", "Windows 10", "macOS Big Sur"
    platform_os_consistent = Column(Boolean)  # Same OS as usual

    # PHASE 2 FEATURES (20 new features for 80-85% fraud detection)
    # Browser fingerprinting (Rules 40-44)
    browser_fonts_hash = Column(String(255))  # Hash of installed fonts
    canvas_fingerprint = Column(String(255))  # Canvas fingerprint
    webgl_fingerprint = Column(String(255))  # WebGL fingerprint
    screen_resolution = Column(String(50))  # "1920x1080"
    timezone_offset = Column(Integer)  # UTC offset in minutes

    # Behavioral analytics (Rules 45-48)
    session_duration_seconds = Column(Integer)  # How long user spent on page
    mouse_movement_score = Column(Integer)  # 0-100, how human-like (100=very human)
    typing_speed_wpm = Column(Integer)  # Estimated words per minute
    copy_paste_count = Column(Integer)  # Number of copy/paste actions

    # Identity verification (Rules 49-51)
    social_media_verified = Column(Boolean, default=False)  # Social profile verified
    social_media_age_days = Column(Integer)  # Age of social media account
    address_verified = Column(Boolean, default=False)  # Address verified via 3rd party

    # Transaction patterns (Rules 52-57)
    shipping_distance_km = Column(Integer)  # Distance from billing to shipping
    transaction_frequency_per_day = Column(Numeric(5, 2))  # Avg txns per day
    avg_transaction_amount = Column(Numeric(15, 2))  # User's average transaction
    chargeback_history_count = Column(Integer, default=0)  # Total chargebacks
    refund_history_count = Column(Integer, default=0)  # Total refunds
    holiday_weekend_transaction = Column(Boolean, default=False)  # Txn on holiday/weekend

    # PHASE 3 FEATURES (50 new features for 85-90% fraud detection)
    # Behavioral biometrics (Rules 58-62)
    keystroke_dynamics_score = Column(Integer)  # 0-100 biometric score
    swipe_pattern_score = Column(Integer)  # Mobile: swipe pattern analysis
    touch_pressure_consistent = Column(Boolean)  # Pressure pattern consistent
    acceleration_pattern_score = Column(Integer)  # Device movement pattern
    scroll_behavior_score = Column(Integer)  # Scrolling pattern analysis

    # Network graph analysis (Rules 63-67)
    co_user_count = Column(Integer)  # Users sharing same device/IP/email
    shared_email_with_fraud = Column(Boolean, default=False)  # Email used in fraud
    shared_phone_with_fraud = Column(Boolean, default=False)  # Phone used in fraud
    shared_device_with_fraud = Column(Boolean, default=False)  # Device used in fraud
    shared_ip_with_fraud = Column(Boolean, default=False)  # IP used in fraud

    # Entity clustering (Rules 68-72)
    first_name_uniqueness = Column(Numeric(5, 2))  # 0-1 how common name is
    last_name_uniqueness = Column(Numeric(5, 2))  # 0-1 how common name is
    email_domain_legitimacy = Column(Integer)  # 0-100 domain legitimacy score
    phone_carrier_risk = Column(Integer)  # 0-100 carrier risk (0=safe, 100=risky)
    bvn_fraud_match_count = Column(Integer, default=0)  # BVN linked to fraud

    # Relationship mapping (Rules 73-77)
    family_member_with_fraud = Column(Boolean, default=False)  # Related account has fraud
    known_fraudster_pattern = Column(Boolean, default=False)  # Matches known fraudster
    linked_to_synthetic_fraud = Column(Boolean, default=False)  # Synthetic identity
    velocity_between_verticals = Column(Integer)  # Velocity across different verticals
    account_resurrection_attempt = Column(Boolean, default=False)  # Old account reactivated

    # Historical pattern matching (Rules 78-82)
    account_history_matches_fraud = Column(Integer)  # Count of matching patterns
    merchant_mcc_history = Column(JSONB)  # MCC codes merchant has used
    previously_declined_transaction = Column(Boolean, default=False)  # Was declined before
    refund_abuse_pattern = Column(Boolean, default=False)  # Serial refund pattern
    chargeback_abuse_pattern = Column(Boolean, default=False)  # Serial chargeback pattern

    # ML-derived features (Rules 83-87)
    entropy_score = Column(Numeric(5, 2))  # Information entropy (randomness)
    anomaly_score = Column(Numeric(5, 2))  # 0-1 anomaly score from ML
    transaction_legitimacy_score = Column(Integer)  # 0-100 legitimacy
    user_profile_deviation = Column(Numeric(5, 2))  # How much deviates from profile
    risk_factor_clustering = Column(JSONB)  # Risk factors grouped by type

    # Device intelligence (Rules 88-92)
    device_manufacturer_risk = Column(Integer)  # 0-100 risk of manufacturer
    device_model_age_months = Column(Integer)  # How old is device model
    emulator_detected = Column(Boolean, default=False)  # Running on emulator
    jailbreak_detected = Column(Boolean, default=False)  # iOS jailbreak/Android root
    suspicious_app_installed = Column(Boolean, default=False)  # Malware/fraud app

    # Industry-specific signals (Rules 93-97)
    lending_cross_sell_pattern = Column(Boolean, default=False)  # Lending cross-sell fraud
    ecommerce_dropshipper_pattern = Column(Boolean, default=False)  # Dropshipping fraud
    crypto_pump_dump_signal = Column(Boolean, default=False)  # Pump & dump pattern
    betting_arbitrage_likelihood = Column(Integer)  # 0-100 likelihood
    marketplace_seller_collusion = Column(Boolean, default=False)  # Colluding sellers

    # Complex pattern detection (Rules 98-102)
    transaction_pattern_entropy = Column(Numeric(5, 2))  # Randomness of patterns
    behavioral_consistency_score = Column(Integer)  # 0-100 consistency over time
    account_age_velocity_ratio = Column(Numeric(5, 2))  # Velocity vs account age
    geographic_consistency_score = Column(Integer)  # 0-100 location consistency
    temporal_consistency_score = Column(Integer)  # 0-100 time pattern consistency

    # Cross-transaction analytics (Rules 103-107)
    multi_account_cross_funding = Column(Boolean, default=False)  # Money flowing between accounts
    round_trip_transaction = Column(Boolean, default=False)  # Money goes out and comes back
    test_transaction_pattern = Column(Boolean, default=False)  # Small txns before large ones
    rapid_account_progression = Column(Boolean, default=False)  # Account tier upgrade quickly
    suspicious_beneficiary_pattern = Column(Boolean, default=False)  # Beneficiary pattern abnormal

    # Advanced ML features (Rules 108-109)
    deep_learning_fraud_score = Column(Numeric(5, 2))  # 0-1 from deep learning model
    ensemble_model_confidence = Column(Numeric(5, 2))  # 0-1 ensemble confidence

    # Detection outputs
    risk_score = Column(Integer, index=True)
    risk_level = Column(String(20))  # low, medium, high
    decision = Column(String(20))  # approve, review, decline
    flags = Column(JSONB)  # Array of fraud flags
    processing_time_ms = Column(Integer)

    # Actual outcome (filled via feedback)
    is_fraud = Column(Boolean, default=None, nullable=True)
    fraud_type = Column(String(100))
    fraud_confirmed_at = Column(TIMESTAMP)
    amount_saved = Column(Numeric(15, 2))
    feedback_notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_client_created', 'client_id', 'created_at'),
        Index('idx_risk_level', 'risk_level'),
        Index('idx_decision', 'decision'),
        Index('idx_is_fraud', 'is_fraud'),
        Index('idx_device_fingerprint', 'device_fingerprint'),  # For loan stacking detection
        Index('idx_fingerprint_client', 'device_fingerprint', 'client_id'),  # For consortium detection
    )


class ConsortiumIntelligence(Base):
    """Consortium intelligence - privacy-preserving cross-lender fraud patterns"""

    __tablename__ = "consortium_intelligence"

    id = Column(Integer, primary_key=True, index=True)

    # Hashed identifiers (privacy-preserving - NO raw PII stored)
    device_hash = Column(String(64), unique=True, index=True)
    bvn_hash = Column(String(64), index=True)
    phone_hash = Column(String(64), index=True)
    email_hash = Column(String(64), index=True)

    # Fraud signals
    fraud_count = Column(Integer, default=0)
    first_seen_at = Column(TIMESTAMP, default=datetime.utcnow)
    last_seen_at = Column(TIMESTAMP, default=datetime.utcnow)
    client_count = Column(Integer, default=0)  # How many clients flagged this

    # Metadata
    fraud_types = Column(JSONB)  # ["loan_stacking", "sim_swap"]
    total_amount_involved = Column(Numeric(15, 2), default=0)
    risk_level = Column(String(20))  # low, medium, high, critical

    # Multi-vertical support (NEW)
    verticals = Column(JSONB)  # Industries where fraud detected: ["lending", "crypto"]
    vertical_fraud_counts = Column(JSONB)  # Per-vertical fraud counts: {"lending": 5, "crypto": 2}

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes for performance
    __table_args__ = (
        Index('idx_fraud_count', 'fraud_count'),
        Index('idx_client_count', 'client_count'),
        Index('idx_last_seen', 'last_seen_at'),
    )


class Client(Base):
    """Clients table - stores customer information and configuration"""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=False)

    # Subscription
    plan = Column(String(50))  # starter, growth, enterprise
    monthly_fee = Column(Numeric(10, 2))
    status = Column(String(20), default="active")  # active, suspended, churned

    # API access
    api_key = Column(String(255), unique=True, index=True)
    api_rate_limit = Column(Integer, default=10000)  # requests/hour

    # Configuration
    risk_threshold_high = Column(Integer, default=70)
    risk_threshold_medium = Column(Integer, default=40)
    enabled_rules = Column(JSONB)  # List of enabled rule names
    custom_rules = Column(JSONB)  # Custom rules defined by client

    # Multi-vertical configuration (NEW)
    enabled_verticals = Column(JSONB, default=lambda: ['lending'])  # List of enabled verticals: ['lending', 'crypto', 'ecommerce', 'betting', 'payments', 'transfers']
    vertical_thresholds = Column(JSONB)  # Per-vertical risk thresholds: {"crypto": {"high": 65, "medium": 35}, "ecommerce": {...}}
    vertical_weights = Column(JSONB)  # Per-vertical rule weights for ML: {"crypto": {"new_wallet_high_value": 1.2}, ...}

    # Metrics
    total_checks = Column(Integer, default=0)
    total_fraud_caught = Column(Integer, default=0)
    total_amount_saved = Column(Numeric(15, 2), default=0)

    # Per-vertical metrics (NEW)
    vertical_metrics = Column(JSONB)  # Per-vertical statistics: {"lending": {"checks": 100, "fraud_caught": 5, "amount_saved": 2500000}, "crypto": {...}}

    # Contact information
    contact_name = Column(String(255))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))

    # Webhook configuration
    webhook_url = Column(String(500))  # URL to receive webhook notifications
    webhook_secret = Column(String(255))  # Secret for HMAC signature verification
    webhook_events = Column(JSONB)  # List of events to send: ["transaction.high_risk", "fraud.confirmed"]

    # ML configuration
    ml_enabled = Column(Boolean, default=True)  # Use ML predictions
    ml_weight = Column(Numeric(3, 2), default=0.7)  # Weight for ML vs rules (0.0-1.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Index
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_plan', 'plan'),
    )


class RuleAccuracy(Base):
    """Track accuracy of fraud detection rules for continuous learning"""

    __tablename__ = "rule_accuracy"

    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False, index=True)
    industry = Column(String(50), default="lending", nullable=False, index=True)  # NEW: per-vertical tracking

    # Performance metrics
    triggered_count = Column(Integer, default=0)
    correct_predictions = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)

    # Calculated metrics
    accuracy = Column(Numeric(5, 4), default=0)  # 0.0000 to 1.0000
    precision = Column(Numeric(5, 4), default=0)
    recall = Column(Numeric(5, 4), default=0)

    # Weight adjustment (for ML)
    current_weight = Column(Numeric(5, 2), default=1.0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Composite unique constraint for rule + industry combo
    __table_args__ = (
        Index('idx_rule_industry', 'rule_name', 'industry', unique=True),
    )


class VelocityCheck(Base):
    """Track user velocity for fraud detection (e.g., multiple transactions in short time)"""

    __tablename__ = "velocity_checks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, index=True)
    client_id = Column(String(255), nullable=False)

    # Velocity metrics
    transaction_count_1min = Column(Integer, default=0)
    transaction_count_10min = Column(Integer, default=0)
    transaction_count_1hour = Column(Integer, default=0)
    transaction_count_24hour = Column(Integer, default=0)

    # Amount velocity
    total_amount_1hour = Column(Numeric(15, 2), default=0)
    total_amount_24hour = Column(Numeric(15, 2), default=0)

    # Timestamps
    last_transaction_at = Column(TIMESTAMP, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_user_client', 'user_id', 'client_id'),
        Index('idx_last_transaction', 'last_transaction_at'),
    )
