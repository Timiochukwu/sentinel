"""
Universal fraud detection rules that apply to multiple verticals

These rules are fundamental fraud indicators that work across
multiple industries. Some apply to all verticals, others to 4+ verticals.
"""

from typing import Dict, Any, Optional
from datetime import datetime, time
from .base import FraudRule
from app.schemas import FraudFlag, TransactionCheckRequest


class DuplicateTransactionRule(FraudRule):
    """Duplicate transaction detected"""

    def __init__(self):
        super().__init__(
            name="duplicate_transaction",
            description="Same transaction duplicated",
            base_score=26,
            severity="high",
            verticals=["ecommerce", "payments", "betting", "crypto"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        is_duplicate = context.get("is_duplicate_transaction", False)
        if is_duplicate:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.95,
                message="Duplicate transaction detected"
            )
        return None


class RefundAbusePatternRule(FraudRule):
    """Rule 53: Refund Abuse Pattern"""

    def __init__(self):
        super().__init__(
            name="refund_abuse_pattern",
            description="Pattern of refunds",
            base_score=28,
            severity="high",
            verticals=["ecommerce", "fintech", "payments", "marketplace"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.refund_history_count and transaction.refund_history_count > 5:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.84,
                message=f"{transaction.refund_history_count} refunds on record"
            )
        return None


class RefundAbuseSerialRule(FraudRule):
    """Rule 76: Serial Refund Abuser"""

    def __init__(self):
        super().__init__(
            name="refund_abuse_serial",
            description="Serial refund abuse pattern",
            base_score=35,
            severity="high",
            verticals=["ecommerce", "fintech", "payments", "marketplace"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.refund_abuse_pattern:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.88,
                message="Serial refund abuse pattern detected"
            )
        return None


class ChargebackAbuseSerialRule(FraudRule):
    """Rule 77: Serial Chargeback Abuser"""

    def __init__(self):
        super().__init__(
            name="chargeback_abuse_serial",
            description="Serial chargeback abuse pattern",
            base_score=38,
            severity="critical",
            verticals=["ecommerce", "fintech", "payments", "marketplace"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.chargeback_abuse_pattern:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.90,
                message="Serial chargeback abuse pattern"
            )
        return None


# Export all universal/cross-cutting rules
UNIVERSAL_RULES = [
    DuplicateTransactionRule(),
    RefundAbusePatternRule(),
    RefundAbuseSerialRule(),
    ChargebackAbuseSerialRule(),
]
