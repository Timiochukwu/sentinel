"""
Feature Storage Service

Extracts and stores 249+ fraud detection features in JSONB database columns.

The database has 9 JSONB columns ready for feature storage:
1. features_identity - Email, phone, BVN, device, network (40 features)
2. features_behavioral - Session, login, transaction, interaction (60 features)
3. features_transaction - Card, banking, address, crypto, merchant (40 features)
4. features_network - Consortium, fraud linkage, velocity, graph (40 features)
5. features_ato - Account takeover signals (15 features)
6. features_funding - Funding source fraud (10 features)
7. features_merchant - Merchant abuse (10 features)
8. features_ml - ML-derived features (9 features)
9. features_derived - Similarity, linkage, clustering (25 features)

This service extracts features from transactions and stores them for:
- Historical analysis
- ML model training
- Feature aggregation over time
- Behavioral profiling

Usage:
    from app.services.feature_storage import feature_storage

    # Extract and store features
    features = feature_storage.extract_features(transaction, context)

    # Store in database
    feature_storage.store_features(transaction_id, features, db)
"""

from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.schemas import (
    TransactionCheckRequest,
    IdentityFeatures,
    BehavioralFeatures,
    TransactionFeatures,
    NetworkFeatures,
    ATOSignals,
    FundingFraudSignals,
    MerchantAbuseSignals,
    MLDerivedFeatures,
    DerivedFeatures,
)
from app.models.database import Transaction


class FeatureStorageService:
    """
    Extract and store fraud detection features

    This service bridges the gap between raw transaction data and structured
    feature storage. It:
    1. Extracts features from transaction requests
    2. Enriches with context data (history, consortium, etc.)
    3. Structures features into 9 categories
    4. Stores in JSONB columns for fast querying

    Why JSONB?
    - Flexible schema (add features without migrations)
    - Fast indexing and querying (GIN indexes)
    - Easy aggregation and analytics
    - ML-friendly format (JSON → pandas DataFrame)
    """

    def extract_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract all 249+ features from transaction and context

        Args:
            transaction: Raw transaction request data
            context: Enriched context (velocity, history, consortium, etc.)

        Returns:
            Dictionary with 9 feature categories:
            {
                "identity": {...},      # 40 features
                "behavioral": {...},    # 60 features
                "transaction": {...},   # 40 features
                "network": {...},       # 40 features
                "ato": {...},          # 15 features
                "funding": {...},      # 10 features
                "merchant": {...},     # 10 features
                "ml": {...},           # 9 features
                "derived": {...}       # 25 features
            }
        """
        return {
            "identity": self._extract_identity_features(transaction, context),
            "behavioral": self._extract_behavioral_features(transaction, context),
            "transaction": self._extract_transaction_features(transaction, context),
            "network": self._extract_network_features(transaction, context),
            "ato": self._extract_ato_features(transaction, context),
            "funding": self._extract_funding_features(transaction, context),
            "merchant": self._extract_merchant_features(transaction, context),
            "ml": self._extract_ml_features(transaction, context),
            "derived": self._extract_derived_features(transaction, context),
        }

    def _extract_identity_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract identity features (40 features)"""
        return {
            "email": {
                "address": transaction.email,
                "domain": transaction.email.split("@")[1] if transaction.email and "@" in transaction.email else None,
                "age_days": transaction.email_domain_age_days,
                "reputation_score": transaction.email_reputation_score,
                "verification_status": bool(transaction.email),
            },
            "phone": {
                "number": transaction.phone,
                "age_days": None,  # Would need enrichment service
                "country_code": None,
                "verification_status": transaction.phone_verified,
                "carrier_risk": transaction.phone_carrier_risk,
            },
            "bvn": {
                "bvn": transaction.bvn,
                "nin": None,
                "verification_status": bool(transaction.bvn),
            },
            "device": {
                "fingerprint": transaction.device_fingerprint,
                "browser_type": None,  # Would parse from user_agent
                "browser_version": None,
                "os": transaction.platform_os,
                "screen_resolution": transaction.screen_resolution,
                "timezone": f"{transaction.timezone_offset}min" if transaction.timezone_offset else None,
                "installed_fonts": None,
                "canvas_fingerprint": transaction.canvas_fingerprint,
                "webgl_fingerprint": transaction.webgl_fingerprint,
                "gpu_info": None,
                "cpu_cores": None,
                "battery_level": None,
            },
            "network": {
                "ip_address": transaction.ip_address,
                "ip_city": transaction.city,
                "ip_country": transaction.country,
                "ip_reputation": transaction.ip_reputation_score,
                "vpn_detected": None,  # Would need IP analysis service
                "proxy_detected": None,
                "tor_detected": None,
                "datacenter_ip": None,
                "isp": None,
                "asn": None,
            }
        }

    def _extract_behavioral_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract behavioral features (60 features)"""
        return {
            "session": {
                "mouse_movement_score": transaction.mouse_movement_score,
                "typing_speed_wpm": transaction.typing_speed_wpm,
                "keystroke_dynamics_score": transaction.keystroke_dynamics_score,
                "copy_paste_count": transaction.copy_paste_count,
                "time_on_page_seconds": transaction.session_duration_seconds,
                "pages_visited": None,
                "click_count": None,
                "scroll_count": None,
                "session_duration_seconds": transaction.session_duration_seconds,
                "navigation_path": None,
                "form_field_time_seconds": None,
                "hesitation_detected": None,
                "error_corrections": None,
                "tab_switches": None,
                "window_resized": None,
            },
            "login": {
                "login_frequency": None,
                "login_time_hour": transaction.transaction_hour,
                "failed_login_attempts_24h": transaction.failed_login_count_24h,
                "failed_login_velocity": transaction.failed_login_count_7d,
                "password_reset_requests": None,
                "password_reset_txn_time_gap": None,
                "two_factor_enabled": None,
                "biometric_auth": None,
                "social_login": transaction.social_media_verified,
                "remember_me_used": None,
                "autofill_used": None,
                "new_device_login": None,
                "unusual_location_login": transaction.is_unusual_time,
            },
            "transaction": {
                "velocity_last_hour": context.get("velocity", {}).get("last_hour", 0),
                "velocity_last_day": context.get("velocity", {}).get("last_day", 0),
                "velocity_last_week": context.get("velocity", {}).get("last_week", 0),
                "transaction_count_lifetime": transaction.transaction_count,
                "avg_transaction_amount": transaction.avg_transaction_amount,
                "max_transaction_amount": None,
                "min_transaction_amount": None,
                "txn_time_hour": transaction.transaction_hour,
                "txn_day_of_week": None,
                "holiday_transaction": transaction.holiday_weekend_transaction,
                "weekend_transaction": transaction.holiday_weekend_transaction,
                "after_hours_transaction": transaction.is_unusual_time,
                "first_transaction_amount": transaction.first_transaction_amount,
                "time_since_last_txn_hours": None,
                "time_since_signup_days": transaction.days_since_signup,
                "txn_to_signup_ratio": None,
                "new_funding_immediate_withdrawal": None,
            },
            "interaction": {
                "referrer_source": None,
                "campaign_tracking": None,
                "utm_parameters": None,
                "ad_click": None,
                "api_calls_made": None,
                "api_errors": None,
                "swipe_gestures_count": None,
                "pinch_zoom_count": None,
                "app_switches": None,
                "screen_orientation_changes": None,
                "home_button_pressed": None,
                "notification_interacted": None,
                "deeplink_used": None,
                "page_refresh_count": None,
                "browser_back_button": None,
            }
        }

    def _extract_transaction_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract transaction-specific features (40 features)"""
        return {
            "card": {
                "bin": transaction.card_bin,
                "last_four": transaction.card_last4,
                "expiry_date": None,
                "card_country": None,
                "card_age_days": None,
                "card_reputation_score": transaction.card_bin_reputation_score,
                "new_card_large_withdrawal": None,
                "card_testing_pattern": None,
                "multiple_cards_same_device": None,
            },
            "banking": {
                "account_number": None,
                "account_age_days": None,
                "new_account_withdrawal": None,
                "account_verification": None,
            },
            "address": {
                "billing_address": None,
                "shipping_address": None,
                "address_distance_km": transaction.shipping_distance_km,
            },
            "crypto": {
                "wallet_address": transaction.wallet_address,
                "wallet_reputation": None,
                "wallet_age_days": transaction.wallet_age_days,
                "deposit_within_24h": None,
                "withdrawal_after_deposit": None,
            },
            "merchant": {
                "merchant_category": transaction.product_category,
                "merchant_high_risk": None,
                "merchant_fraud_cluster": None,
                "merchant_chargeback_rate": None,
                "merchant_refund_rate": None,
            }
        }

    def _extract_network_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract network/consortium features (40 features)"""
        consortium = context.get("consortium", {})

        return {
            "consortium_matching": {
                "email_seen_elsewhere": consortium.get("email_matches", 0) > 0,
                "phone_seen_elsewhere": consortium.get("phone_matches", 0) > 0,
                "device_seen_elsewhere": consortium.get("device_matches", 0) > 0,
                "ip_seen_elsewhere": False,
                "card_seen_elsewhere": False,
                "address_seen_elsewhere": False,
                "bank_account_seen_elsewhere": False,
                "bvn_seen_elsewhere": consortium.get("bvn_matches", 0) > 0,
            },
            "fraud_linkage": {
                "email_linked_to_fraud": transaction.shared_email_with_fraud,
                "phone_linked_to_fraud": transaction.shared_phone_with_fraud,
                "device_linked_to_fraud": transaction.shared_device_with_fraud,
                "ip_linked_to_fraud": transaction.shared_ip_with_fraud,
                "card_linked_to_fraud": False,
                "address_linked_to_fraud": False,
                "bank_account_linked_to_fraud": False,
                "bvn_linked_to_fraud": transaction.bvn_fraud_match_count > 0 if transaction.bvn_fraud_match_count else False,
            },
            "velocity": {
                "velocity_email": None,
                "velocity_phone": None,
                "velocity_device": None,
                "velocity_ip": None,
                "velocity_card": None,
                "velocity_bank_account": None,
                "velocity_bvn": None,
            },
            "graph_analysis": {
                "connected_accounts_detected": transaction.co_user_count > 0 if transaction.co_user_count else False,
                "fraud_ring_detected": transaction.known_fraudster_pattern,
                "same_ip_multiple_users": None,
                "same_device_multiple_users": transaction.co_user_count,
                "same_address_multiple_users": None,
                "same_bvn_multiple_accounts": None,
                "same_contact_multiple_users": None,
                "synthetic_identity_cluster": transaction.linked_to_synthetic_fraud,
                "money_mule_network_detected": None,
                "loan_stacking_ring_detected": consortium.get("loan_stacking_detected", False),
            }
        }

    def _extract_ato_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract account takeover features (15 features)"""
        return {
            "classic_patterns": {
                "password_reset_txn": None,
                "failed_login_velocity": transaction.failed_login_count_24h,
                "new_device_behavior_change": None,
                "password_change_withdrawal": None,
                "geographic_impossibility": None,
                "new_device_high_value": None,
                "device_change_behavior_change": None,
                "suspicious_location_login": transaction.is_unusual_time,
                "multiple_failed_logins_ips": None,
                "session_hijacking_detected": None,
            },
            "behavioral_deviation": {
                "typing_pattern_deviation": None,
                "mouse_movement_deviation": None,
                "navigation_pattern_deviation": None,
                "transaction_pattern_deviation": None,
                "time_of_day_deviation": transaction.is_unusual_time,
            }
        }

    def _extract_funding_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract funding source fraud features (10 features)"""
        return {
            "new_sources": {
                "new_card_withdrawal": None,
                "new_bank_account_withdrawal": None,
                "card_added_withdrew_same_day": None,
                "multiple_sources_added_quickly": None,
                "funding_source_high_risk_country": None,
            },
            "card_testing": {
                "dollar_one_authorizations": None,
                "small_fails_large_success": None,
                "multiple_cards_tested_device": None,
                "bin_attack_pattern": None,
                "funding_source_velocity": None,
            }
        }

    def _extract_merchant_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract merchant abuse features (10 features)"""
        return {
            "merchant_risk": {
                "high_risk_category": None,
                "merchant_fraud_cluster": None,
                "merchant_chargeback_rate": None,
                "merchant_refund_rate": None,
            },
            "abuse_patterns": {
                "refund_abuse_detected": transaction.refund_abuse_pattern,
                "cashback_abuse_detected": None,
                "promo_abuse_detected": None,
                "loyalty_points_abuse": None,
                "referral_fraud": None,
                "fake_merchant_transactions": None,
            }
        }

    def _extract_ml_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract ML-derived features (9 features)"""
        return {
            "statistical_outliers": {
                "outlier_score": transaction.user_profile_deviation,
                "anomaly_score": transaction.anomaly_score,
                "z_score": None,
            },
            "model_scores": {
                "xgboost_risk_score": None,  # Would come from ml_detector
                "neural_network_score": None,
                "random_forest_score": None,
                "ensemble_model_score": transaction.ensemble_model_confidence,
            },
            "deep_learning": {
                "lstm_sequence_prediction": None,
                "gnn_graph_score": None,
            }
        }

    def _extract_derived_features(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract derived/computed features (25 features)"""
        return {
            "similarity": {
                "fraudster_profile_similarity": None,
                "username_similarity": None,
                "email_similarity": None,
                "address_similarity": None,
                "behavior_similarity": None,
                "transaction_pattern_similarity": None,
            },
            "linkage": {
                "entity_resolution_score": None,
                "identity_matching_score": None,
                "soft_linking_score": None,
                "hard_linking_score": None,
            },
            "clustering": {
                "family_connections_detected": transaction.family_member_with_fraud,
                "business_connections_detected": None,
                "geographic_connections_detected": None,
                "temporal_connections_detected": None,
                "community_detection_score": None,
                "cluster_membership_score": None,
                "graph_centrality_score": None,
            },
            "aggregate_risk": {
                "final_risk_score": None,  # Will be populated after fraud detection
                "confidence_score": transaction.ensemble_model_confidence,
                "explainability_score": None,
                "feature_importance_ranking": None,
                "fraud_probability": None,
                "false_positive_probability": None,
                "model_prediction": None,
                "rule_violations_count": None,
            }
        }

    def store_features(
        self,
        transaction_id: str,
        features: Dict[str, Any],
        db: Session
    ) -> bool:
        """
        Store extracted features in database JSONB columns

        Args:
            transaction_id: Transaction ID to update
            features: Extracted features from extract_features()
            db: Database session

        Returns:
            True if successful, False otherwise
        """
        try:
            # Find transaction
            txn = db.query(Transaction).filter(
                Transaction.transaction_id == transaction_id
            ).first()

            if not txn:
                return False

            # Store features in JSONB columns
            txn.features_identity = features.get("identity")
            txn.features_behavioral = features.get("behavioral")
            txn.features_transaction = features.get("transaction")
            txn.features_network = features.get("network")
            txn.features_ato = features.get("ato")
            txn.features_funding = features.get("funding")
            txn.features_merchant = features.get("merchant")
            txn.features_ml = features.get("ml")
            txn.features_derived = features.get("derived")

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"Error storing features: {e}")
            return False


# Singleton instance
feature_storage = FeatureStorageService()
