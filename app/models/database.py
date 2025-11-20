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
