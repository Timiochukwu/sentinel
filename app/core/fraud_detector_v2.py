"""Enhanced fraud detection engine with ML, Redis, and webhooks"""

import time
import asyncio
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.schemas import TransactionCheckRequest, TransactionCheckResponse, FraudFlag
from app.models.database import Transaction, Client
from app.services.rules import FraudRulesEngine
from app.services.consortium import ConsortiumService
from app.services.redis_service import get_redis_service
from app.services.ml_detector import get_ml_detector
from app.services.webhook import send_webhook_async
from app.core.security import hash_device_id, hash_bvn, hash_phone, hash_email
from app.core.config import settings
from app.core.monitoring import track_performance, log_fraud_check, get_metrics_collector
from app.core.logging_config import get_logger

logger = get_logger("fraud_detector")
metrics = get_metrics_collector()


class EnhancedFraudDetector:
    """
    Enhanced fraud detection engine with:
    - Rule-based detection
    - ML predictions
    - Redis velocity tracking
    - Consortium intelligence
    - Webhook notifications
    - Comprehensive monitoring
    """

    def __init__(self, db: Session, client_id: str):
        self.db = db
        self.client_id = client_id
        self.rules_engine = FraudRulesEngine()
        self.consortium = ConsortiumService(db, client_id)
        self.redis = get_redis_service()
        self.ml_detector = get_ml_detector()

        # Get client configuration
        self.client = db.query(Client).filter(Client.client_id == client_id).first()

    @track_performance("fraud_detection")
    async def check_transaction(
        self,
        transaction: TransactionCheckRequest
    ) -> TransactionCheckResponse:
        """
        Main fraud detection method with ML and enhanced features

        Args:
            transaction: Transaction data to check

        Returns:
            TransactionCheckResponse with risk score, flags, and recommendation
        """
        start_time = time.time()

        logger.info(
            "Starting fraud detection",
            extra={
                "transaction_id": transaction.transaction_id,
                "amount": transaction.amount,
                "user_id": transaction.user_id
            }
        )

        # Build context for fraud detection
        context = await self._build_context(transaction)

        # Run fraud detection rules
        rule_risk_score, _, _, rule_flags = self.rules_engine.evaluate(
            transaction, context
        )

        # Run ML prediction (if enabled for client)
        ml_result = None
        if self.client and self.client.ml_enabled:
            try:
                ml_result = self.ml_detector.predict(transaction, context)
                logger.debug(
                    "ML prediction completed",
                    extra={
                        "ml_risk_score": ml_result.get("ml_risk_score"),
                        "fraud_probability": ml_result.get("fraud_probability")
                    }
                )
            except Exception as e:
                logger.error(f"ML prediction failed: {e}")
                ml_result = None

        # Combine ML and rules
        if ml_result and self.client and self.client.ml_enabled:
            # Use ML detector's combine method
            combined = self.ml_detector.combine_with_rules(
                ml_result, rule_risk_score, rule_flags
            )
            risk_score = combined["combined_risk_score"]
            risk_level = combined["risk_level"]
            decision = combined["decision"]
            flags = combined["rule_flags"]

            # Add ML info to response
            ml_info = {
                "ml_enabled": True,
                "ml_risk_score": combined["ml_risk_score"],
                "ml_confidence": combined["ml_confidence"],
                "fraud_probability": combined["fraud_probability"]
            }
        else:
            # Use rules only
            risk_score = rule_risk_score
            flags = rule_flags

            # Determine risk level and decision from rules
            if risk_score >= (self.client.risk_threshold_high if self.client else 70):
                risk_level = "high"
                decision = "decline"
            elif risk_score >= (self.client.risk_threshold_medium if self.client else 40):
                risk_level = "medium"
                decision = "review"
            else:
                risk_level = "low"
                decision = "approve"

            ml_info = {"ml_enabled": False}

        # Get consortium alerts
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
            processing_time_ms=processing_time_ms,
            ml_info=ml_info
        )

        # Log metrics
        log_fraud_check(
            transaction_id=transaction.transaction_id,
            risk_score=risk_score,
            decision=decision,
            processing_time_ms=processing_time_ms,
            client_id=self.client_id
        )

        # Send webhook if configured (async, don't block)
        if self.client and self.client.webhook_url and risk_level in ["high", "medium"]:
            asyncio.create_task(
                self._send_webhook_notification(transaction, risk_score, risk_level, decision, flags, consortium_alerts)
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

        logger.info(
            "Fraud detection completed",
            extra={
                "transaction_id": transaction.transaction_id,
                "risk_score": risk_score,
                "decision": decision,
                "processing_time_ms": processing_time_ms
            }
        )

        return response

    async def _build_context(self, transaction: TransactionCheckRequest) -> Dict[str, Any]:
        """
        Build context for fraud detection using Redis

        Context includes:
        - Consortium intelligence
        - Velocity data from Redis
        - Device history
        - Location history
        """
        context = {}

        try:
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

            # Track velocity in Redis
            if transaction.user_id:
                velocity_data = self.redis.track_transaction_velocity(
                    user_id=transaction.user_id,
                    client_id=self.client_id,
                    amount=transaction.amount
                )
                context["velocity"] = velocity_data

            # Check if device is new
            context["new_device"] = self._is_new_device(transaction)

            # Track device usage in Redis
            if transaction.device_id:
                user_count = self.redis.track_device_usage(
                    device_id=hash_device_id(transaction.device_id),
                    user_id=transaction.user_id,
                    client_id=self.client_id
                )
                context["device_usage"] = {"account_count": user_count}

            # Last location (for impossible travel detection)
            context["last_location"] = self._get_last_location(transaction)

            # VPN detection (simplified)
            context["is_vpn"] = self._is_vpn(transaction)

            # Max loan amount (from client config)
            context["max_loan_amount"] = self._get_max_loan_amount()

        except Exception as e:
            logger.error(f"Error building context: {e}")
            # Return partial context rather than failing

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
        # In production, use a service like IPHub
        if not transaction.ip_address:
            return False

        # Simple check for private IPs
        vpn_indicators = ["10.", "172.", "192.168."]
        return any(transaction.ip_address.startswith(indicator) for indicator in vpn_indicators)

    def _get_max_loan_amount(self) -> float:
        """Get maximum loan amount from client configuration"""
        return 500000  # Default

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
        processing_time_ms: int,
        ml_info: Dict[str, Any]
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

        # Add ML info to flags if available
        if ml_info.get("ml_enabled"):
            flags_json.append({
                "type": "ml_prediction",
                "severity": "info",
                "message": f"ML fraud probability: {ml_info.get('fraud_probability', 0):.2%}",
                "score": ml_info.get("ml_risk_score", 0),
                "confidence": ml_info.get("ml_confidence", 0),
                "metadata": ml_info
            })

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
        if self.client:
            self.client.total_checks += 1
            self.db.commit()

    async def _send_webhook_notification(
        self,
        transaction: TransactionCheckRequest,
        risk_score: int,
        risk_level: str,
        decision: str,
        flags: list,
        consortium_alerts: list
    ):
        """Send webhook notification for high/medium risk transactions"""
        try:
            transaction_data = {
                "transaction_id": transaction.transaction_id,
                "user_id": transaction.user_id,
                "amount": transaction.amount,
                "risk_score": risk_score,
                "risk_level": risk_level,
                "decision": decision,
                "flags": [
                    {
                        "type": flag.type,
                        "severity": flag.severity,
                        "message": flag.message
                    }
                    for flag in flags
                ],
                "consortium_alerts": consortium_alerts
            }

            event_type = "transaction.declined" if decision == "decline" else "transaction.high_risk"

            await send_webhook_async(self.client, transaction_data, event_type)

        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")


# Factory function
def get_fraud_detector(db: Session, client_id: str) -> EnhancedFraudDetector:
    """Get fraud detector instance"""
    return EnhancedFraudDetector(db, client_id)
