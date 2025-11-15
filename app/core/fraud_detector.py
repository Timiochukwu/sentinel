"""Core fraud detection engine that integrates all components"""

import time
from typing import Dict, Any
from sqlalchemy.orm import Session
from app.models.schemas import TransactionCheckRequest, TransactionCheckResponse, FraudFlag
from app.models.database import Transaction, Client
from app.services.rules import FraudRulesEngine
from app.services.consortium import ConsortiumService
from app.core.security import hash_device_id, hash_bvn, hash_phone, hash_email
from app.core.config import settings


class FraudDetector:
    """
    Main fraud detection engine

    Coordinates:
    - Fraud detection rules
    - Consortium intelligence
    - Context building (velocity, device history, etc.)
    - Risk scoring
    """

    def __init__(self, db: Session, client_id: str):
        self.db = db
        self.client_id = client_id
        self.rules_engine = FraudRulesEngine()
        self.consortium = ConsortiumService(db, client_id)

    def check_transaction(
        self,
        transaction: TransactionCheckRequest
    ) -> TransactionCheckResponse:
        """
        Main fraud detection method

        Args:
            transaction: Transaction data to check

        Returns:
            TransactionCheckResponse with risk score, flags, and recommendation
        """
        start_time = time.time()

        # Build context for fraud detection
        context = self._build_context(transaction)

        # Run fraud detection rules
        risk_score, risk_level, decision, flags = self.rules_engine.evaluate(
            transaction, context
        )

        # Get consortium intelligence
        consortium_data = context.get("consortium", {})
        consortium_alerts = consortium_data.get("alerts", [])

        # Generate recommendation
        recommendation = self._generate_recommendation(
            risk_level, decision, flags, consortium_alerts
        )

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Store transaction in database
        self._store_transaction(
            transaction=transaction,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            flags=flags,
            processing_time_ms=processing_time_ms
        )

        # Build response
        response = TransactionCheckResponse(
            transaction_id=transaction.transaction_id,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            flags=flags,
            recommendation=recommendation,
            processing_time_ms=processing_time_ms,
            consortium_alerts=consortium_alerts if consortium_alerts else None
        )

        return response

    def _build_context(self, transaction: TransactionCheckRequest) -> Dict[str, Any]:
        """
        Build context for fraud detection

        Context includes:
        - Consortium intelligence
        - Velocity data
        - Device history
        - Location history
        """
        context = {}

        # Consortium intelligence (if enabled)
        if settings.ENABLE_CONSORTIUM:
            consortium_data = self.consortium.check_fraud_patterns(transaction)
            context["consortium"] = consortium_data

            # Also check loan stacking specifically
            stacking_data = self.consortium.check_loan_stacking(transaction)
            context["consortium"]["client_count"] = max(
                consortium_data.get("client_count", 0),
                stacking_data.get("client_count", 0)
            )
            context["consortium"]["lenders"] = stacking_data.get("lenders", [])

        # Check if device is new (simplified - would use Redis in production)
        context["new_device"] = self._is_new_device(transaction)

        # Velocity data (simplified - would use Redis in production)
        context["velocity"] = self._get_velocity_data(transaction)

        # Device usage (how many accounts use this device)
        context["device_usage"] = self._get_device_usage(transaction)

        # Last location (for impossible travel detection)
        context["last_location"] = self._get_last_location(transaction)

        # VPN detection (simplified)
        context["is_vpn"] = self._is_vpn(transaction)

        # Max loan amount (from client config)
        context["max_loan_amount"] = self._get_max_loan_amount()

        return context

    def _is_new_device(self, transaction: TransactionCheckRequest) -> bool:
        """Check if this is a new device for the user"""
        if not transaction.device_id:
            return False

        device_hash = hash_device_id(transaction.device_id)

        # Check if we've seen this device for this user before
        existing = self.db.query(Transaction).filter(
            Transaction.client_id == self.client_id,
            Transaction.user_id == transaction.user_id,
            Transaction.device_id == device_hash
        ).first()

        return existing is None

    def _get_velocity_data(self, transaction: TransactionCheckRequest) -> Dict:
        """Get transaction velocity for the user (simplified)"""
        # In production, this would query Redis for real-time velocity
        # For now, return mock data
        return {
            "transaction_count_10min": 1,
            "transaction_count_1hour": 2,
            "transaction_count_24hour": 5
        }

    def _get_device_usage(self, transaction: TransactionCheckRequest) -> Dict:
        """Get device usage statistics"""
        if not transaction.device_id:
            return {"account_count": 0}

        device_hash = hash_device_id(transaction.device_id)

        # Count unique users with this device
        from sqlalchemy import func
        count = self.db.query(func.count(func.distinct(Transaction.user_id))).filter(
            Transaction.client_id == self.client_id,
            Transaction.device_id == device_hash
        ).scalar()

        return {"account_count": count or 0}

    def _get_last_location(self, transaction: TransactionCheckRequest) -> Dict:
        """Get user's last known location"""
        last_txn = self.db.query(Transaction).filter(
            Transaction.client_id == self.client_id,
            Transaction.user_id == transaction.user_id,
            Transaction.latitude.isnot(None),
            Transaction.longitude.isnot(None)
        ).order_by(Transaction.created_at.desc()).first()

        if not last_txn:
            return {}

        # Calculate time difference
        from datetime import datetime
        time_diff = datetime.utcnow() - last_txn.created_at
        time_diff_hours = time_diff.total_seconds() / 3600

        return {
            "latitude": float(last_txn.latitude),
            "longitude": float(last_txn.longitude),
            "time_diff_hours": time_diff_hours
        }

    def _is_vpn(self, transaction: TransactionCheckRequest) -> bool:
        """Check if IP is from a VPN (simplified)"""
        # In production, use a service like IPHub, IPQualityScore, etc.
        if not transaction.ip_address:
            return False

        # Simple check for private IPs
        vpn_indicators = ["10.", "172.", "192.168."]
        return any(transaction.ip_address.startswith(indicator) for indicator in vpn_indicators)

    def _get_max_loan_amount(self) -> float:
        """Get maximum loan amount from client configuration"""
        client = self.db.query(Client).filter(
            Client.client_id == self.client_id
        ).first()

        # Default to 500k if not configured
        return 500000

    def _generate_recommendation(
        self,
        risk_level: str,
        decision: str,
        flags: list,
        consortium_alerts: list
    ) -> str:
        """Generate human-readable recommendation"""

        if risk_level == "high":
            if any(flag.type == "sim_swap_pattern" for flag in flags):
                return "DECLINE - High risk of SIM swap attack. Request video verification if needed."
            elif any(flag.type == "loan_stacking" for flag in flags):
                return "DECLINE - Loan stacking detected across multiple lenders."
            else:
                return "DECLINE - High fraud risk. Manual review required."

        elif risk_level == "medium":
            return "REVIEW - Moderate fraud risk. Request additional verification (ID, video call, or bank statement)."

        else:
            return "APPROVE - Low fraud risk. Transaction appears legitimate."

    def _store_transaction(
        self,
        transaction: TransactionCheckRequest,
        risk_score: int,
        risk_level: str,
        decision: str,
        flags: list,
        processing_time_ms: int
    ) -> None:
        """Store transaction in database"""

        # Hash sensitive identifiers before storage
        device_hash = hash_device_id(transaction.device_id) if transaction.device_id else None
        bvn_hash = hash_bvn(transaction.bvn) if transaction.bvn else None
        phone_hash = hash_phone(transaction.phone) if transaction.phone else None
        email_hash = hash_email(transaction.email) if transaction.email else None

        # Convert flags to JSON-serializable format
        flags_json = [
            {
                "type": flag.type,
                "severity": flag.severity,
                "message": flag.message,
                "score": flag.score,
                "confidence": flag.confidence,
                "metadata": flag.metadata
            }
            for flag in flags
        ]

        # Create transaction record
        db_transaction = Transaction(
            transaction_id=transaction.transaction_id,
            client_id=self.client_id,
            user_id=transaction.user_id,
            amount=transaction.amount,
            transaction_type=transaction.transaction_type,
            device_id=device_hash,
            ip_address=transaction.ip_address,
            account_age_days=transaction.account_age_days,
            transaction_count=transaction.transaction_count,
            phone_changed_recently=transaction.phone_changed_recently,
            email_changed_recently=transaction.email_changed_recently,
            bvn=bvn_hash,
            phone=phone_hash,
            email=email_hash,
            latitude=transaction.latitude,
            longitude=transaction.longitude,
            city=transaction.city,
            country=transaction.country,
            risk_score=risk_score,
            risk_level=risk_level,
            decision=decision,
            flags=flags_json,
            processing_time_ms=processing_time_ms
        )

        self.db.add(db_transaction)
        self.db.commit()

        # Update client statistics
        client = self.db.query(Client).filter(
            Client.client_id == self.client_id
        ).first()

        if client:
            client.total_checks += 1
            self.db.commit()
