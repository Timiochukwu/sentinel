"""
Feature Aggregation Service

Aggregates historical features for ML model training and behavioral profiling.

This service:
1. Queries historical transaction features from JSONB columns
2. Aggregates features over time windows (7d, 30d, 90d, lifetime)
3. Calculates derived metrics (averages, trends, anomalies)
4. Builds user behavioral profiles
5. Prepares feature vectors for ML models

Usage:
    from app.services.feature_aggregation import feature_aggregation

    # Get user behavioral profile
    profile = feature_aggregation.get_user_profile(user_id, db)

    # Calculate velocity metrics
    velocity = feature_aggregation.calculate_velocity(user_id, db)

    # Prepare ML features
    ml_features = feature_aggregation.prepare_ml_features(user_id, db)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_

from app.models.database import Transaction


class FeatureAggregationService:
    """
    Aggregate and analyze historical fraud detection features

    This service turns raw transaction features into powerful ML signals by:
    1. Temporal aggregation (how behavior changes over time)
    2. Cross-feature correlation (which features appear together)
    3. Anomaly detection (deviation from user's normal behavior)
    4. Trend analysis (increasing fraud signals over time)
    """

    def get_user_profile(
        self,
        user_id: str,
        db: Session,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Build comprehensive user behavioral profile

        Args:
            user_id: User to profile
            db: Database session
            days: Historical window (default 90 days)

        Returns:
            User profile with aggregated features:
            {
                "user_id": "...",
                "account_age_days": 45,
                "total_transactions": 127,
                "fraud_count": 2,
                "fraud_rate": 1.57,
                "avg_transaction_amount": 45000,
                "transaction_frequency": {
                    "last_7d": 5,
                    "last_30d": 23,
                    "last_90d": 127
                },
                "risk_metrics": {...},
                "behavioral_patterns": {...}
            }
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Query user transactions
        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= cutoff_date
        ).all()

        if not transactions:
            return {
                "user_id": user_id,
                "account_age_days": 0,
                "total_transactions": 0,
                "fraud_count": 0,
                "fraud_rate": 0.0,
                "avg_transaction_amount": 0.0,
                "transaction_frequency": {"last_7d": 0, "last_30d": 0, "last_90d": 0},
                "risk_metrics": {},
                "behavioral_patterns": {}
            }

        # Calculate basic metrics
        total_count = len(transactions)
        fraud_count = sum(1 for t in transactions if t.is_fraudulent)
        fraud_rate = (fraud_count / total_count * 100) if total_count > 0 else 0

        avg_amount = sum(t.amount for t in transactions) / total_count

        # Calculate velocity
        now = datetime.utcnow()
        last_7d = sum(1 for t in transactions if t.created_at >= now - timedelta(days=7))
        last_30d = sum(1 for t in transactions if t.created_at >= now - timedelta(days=30))

        # Calculate risk metrics
        avg_fraud_score = sum(t.fraud_score for t in transactions) / total_count
        max_fraud_score = max(t.fraud_score for t in transactions)

        # Analyze behavioral patterns
        hourly_dist = {}
        for txn in transactions:
            hour = txn.created_at.hour
            hourly_dist[hour] = hourly_dist.get(hour, 0) + 1

        most_active_hour = max(hourly_dist, key=hourly_dist.get) if hourly_dist else None

        return {
            "user_id": user_id,
            "account_age_days": (now - min(t.created_at for t in transactions)).days,
            "total_transactions": total_count,
            "fraud_count": fraud_count,
            "fraud_rate": round(fraud_rate, 2),
            "avg_transaction_amount": round(avg_amount, 2),
            "max_transaction_amount": max(t.amount for t in transactions),
            "min_transaction_amount": min(t.amount for t in transactions),
            "transaction_frequency": {
                "last_7d": last_7d,
                "last_30d": last_30d,
                "last_90d": total_count
            },
            "risk_metrics": {
                "avg_fraud_score": round(avg_fraud_score, 2),
                "max_fraud_score": max_fraud_score,
                "high_risk_count": sum(1 for t in transactions if t.fraud_score >= 70),
                "declined_count": sum(1 for t in transactions if t.decision == "decline"),
            },
            "behavioral_patterns": {
                "most_active_hour": most_active_hour,
                "hourly_distribution": hourly_dist,
                "verticals_used": list(set(t.vertical for t in transactions if t.vertical)),
            },
            "generated_at": now.isoformat()
        }

    def calculate_velocity(
        self,
        user_id: str,
        db: Session,
        entity_type: str = "user",  # user, device, ip, email
        entity_value: str = None
    ) -> Dict[str, int]:
        """
        Calculate transaction velocity for fraud detection

        Velocity = number of transactions in a time window.
        High velocity can indicate fraud (account takeover, loan stacking).

        Args:
            user_id: User ID
            db: Database session
            entity_type: What to track (user, device, ip, email)
            entity_value: Value of entity (e.g., IP address)

        Returns:
            {
                "last_hour": 0,
                "last_6h": 2,
                "last_24h": 5,
                "last_7d": 15,
                "last_30d": 45
            }
        """
        now = datetime.utcnow()

        # Build query based on entity type
        if entity_type == "user":
            base_query = db.query(Transaction).filter(Transaction.user_id == user_id)
        elif entity_type == "device" and entity_value:
            base_query = db.query(Transaction).filter(Transaction.device_id == entity_value)
        elif entity_type == "ip" and entity_value:
            base_query = db.query(Transaction).filter(Transaction.ip_address == entity_value)
        else:
            base_query = db.query(Transaction).filter(Transaction.user_id == user_id)

        # Count transactions in different time windows
        last_hour = base_query.filter(Transaction.created_at >= now - timedelta(hours=1)).count()
        last_6h = base_query.filter(Transaction.created_at >= now - timedelta(hours=6)).count()
        last_24h = base_query.filter(Transaction.created_at >= now - timedelta(days=1)).count()
        last_7d = base_query.filter(Transaction.created_at >= now - timedelta(days=7)).count()
        last_30d = base_query.filter(Transaction.created_at >= now - timedelta(days=30)).count()

        return {
            "last_hour": last_hour,
            "last_6h": last_6h,
            "last_24h": last_24h,
            "last_7d": last_7d,
            "last_30d": last_30d,
            "calculated_at": now.isoformat()
        }

    def detect_anomalies(
        self,
        user_id: str,
        current_transaction: Dict[str, Any],
        db: Session
    ) -> Dict[str, Any]:
        """
        Detect anomalies in current transaction vs. user history

        Anomaly detection helps catch:
        - Account takeover (different behavior after compromise)
        - Fraudster using stolen credentials
        - Sudden changes in transaction patterns

        Args:
            user_id: User to analyze
            current_transaction: Current transaction details
            db: Database session

        Returns:
            {
                "is_anomaly": True/False,
                "anomaly_score": 0.85,  # 0-1
                "anomalies_detected": ["amount", "time", "location"],
                "details": {...}
            }
        """
        profile = self.get_user_profile(user_id, db, days=30)

        if profile["total_transactions"] < 3:
            # Not enough history for anomaly detection
            return {
                "is_anomaly": False,
                "anomaly_score": 0.0,
                "anomalies_detected": [],
                "details": {"reason": "insufficient_history"}
            }

        anomalies = []
        anomaly_score = 0.0

        # Check amount anomaly
        current_amount = current_transaction.get("amount", 0)
        avg_amount = profile["avg_transaction_amount"]

        if avg_amount > 0:
            amount_deviation = abs(current_amount - avg_amount) / avg_amount
            if amount_deviation > 2.0:  # 200% deviation
                anomalies.append("amount")
                anomaly_score += 0.3

        # Check time anomaly
        current_hour = current_transaction.get("hour", datetime.utcnow().hour)
        most_active_hour = profile["behavioral_patterns"].get("most_active_hour")

        if most_active_hour and abs(current_hour - most_active_hour) > 6:
            anomalies.append("time")
            anomaly_score += 0.2

        # Check fraud score anomaly
        current_fraud_score = current_transaction.get("fraud_score", 0)
        avg_fraud_score = profile["risk_metrics"].get("avg_fraud_score", 0)

        if avg_fraud_score < 30 and current_fraud_score > 60:
            # Normally low-risk user suddenly high-risk
            anomalies.append("fraud_score")
            anomaly_score += 0.4

        # Normalize anomaly score
        anomaly_score = min(anomaly_score, 1.0)

        return {
            "is_anomaly": len(anomalies) > 0,
            "anomaly_score": round(anomaly_score, 2),
            "anomalies_detected": anomalies,
            "details": {
                "current_amount": current_amount,
                "avg_amount": avg_amount,
                "current_hour": current_hour,
                "typical_hour": most_active_hour,
                "current_fraud_score": current_fraud_score,
                "avg_fraud_score": avg_fraud_score,
            }
        }

    def prepare_ml_features(
        self,
        user_id: str,
        db: Session,
        current_transaction: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare feature vector for ML model training/prediction

        Args:
            user_id: User ID
            db: Database session
            current_transaction: Current transaction (if predicting)

        Returns:
            Feature vector suitable for ML models:
            {
                "user_features": {...},
                "behavioral_features": {...},
                "network_features": {...},
                "feature_vector": [...]  # Numerical array for model
            }
        """
        profile = self.get_user_profile(user_id, db)
        velocity = self.calculate_velocity(user_id, db)

        # Aggregate features from historical transactions
        recent_txns = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= datetime.utcnow() - timedelta(days=30)
        ).all()

        # Extract aggregated behavioral features
        behavioral_agg = {
            "avg_session_duration": 0,
            "avg_typing_speed": 0,
            "device_consistency": 0,
            "location_consistency": 0,
        }

        if recent_txns:
            # Calculate averages from JSONB features
            session_durations = []
            for txn in recent_txns:
                if txn.features_behavioral:
                    session = txn.features_behavioral.get("session", {})
                    duration = session.get("session_duration_seconds")
                    if duration:
                        session_durations.append(duration)

            if session_durations:
                behavioral_agg["avg_session_duration"] = sum(session_durations) / len(session_durations)

        # Combine all features
        return {
            "user_id": user_id,
            "user_features": {
                "account_age_days": profile["account_age_days"],
                "total_transactions": profile["total_transactions"],
                "fraud_rate": profile["fraud_rate"],
                "avg_amount": profile["avg_transaction_amount"],
            },
            "behavioral_features": behavioral_agg,
            "velocity_features": velocity,
            "risk_features": profile["risk_metrics"],
            "generated_at": datetime.utcnow().isoformat()
        }

    def get_feature_trends(
        self,
        user_id: str,
        db: Session,
        feature_name: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze trends for a specific feature over time

        Args:
            user_id: User ID
            db: Database session
            feature_name: Feature to analyze (e.g., "fraud_score", "amount")
            days: Time window

        Returns:
            {
                "feature": "fraud_score",
                "trend": "increasing",  # increasing, decreasing, stable
                "values": [10, 15, 20, 30, 45],
                "avg": 24,
                "max": 45,
                "min": 10,
                "variance": 15.2
            }
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        transactions = db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.created_at >= cutoff_date
        ).order_by(Transaction.created_at.asc()).all()

        if not transactions:
            return {
                "feature": feature_name,
                "trend": "insufficient_data",
                "values": [],
                "avg": 0,
                "max": 0,
                "min": 0,
                "variance": 0
            }

        # Extract feature values
        values = []
        for txn in transactions:
            if feature_name == "fraud_score":
                values.append(txn.fraud_score)
            elif feature_name == "amount":
                values.append(txn.amount)
            # Add more feature extractors as needed

        if not values:
            return {
                "feature": feature_name,
                "trend": "no_data",
                "values": [],
                "avg": 0,
                "max": 0,
                "min": 0,
                "variance": 0
            }

        # Calculate trend
        if len(values) >= 3:
            first_third_avg = sum(values[:len(values)//3]) / (len(values)//3)
            last_third_avg = sum(values[-len(values)//3:]) / (len(values)//3)

            if last_third_avg > first_third_avg * 1.2:
                trend = "increasing"
            elif last_third_avg < first_third_avg * 0.8:
                trend = "decreasing"
            else:
                trend = "stable"
        else:
            trend = "insufficient_data"

        # Calculate statistics
        avg = sum(values) / len(values)
        variance = sum((x - avg) ** 2 for x in values) / len(values)

        return {
            "feature": feature_name,
            "trend": trend,
            "values": values,
            "avg": round(avg, 2),
            "max": max(values),
            "min": min(values),
            "variance": round(variance, 2),
            "count": len(values),
            "analyzed_period_days": days
        }


# Singleton instance
feature_aggregation = FeatureAggregationService()
