"""
Universal fraud detection rules that apply to ALL verticals

These rules are fundamental fraud indicators that work across
all industries: lending, fintech, ecommerce, crypto, betting, gaming, marketplace
"""

from typing import Dict, Any, Optional
from datetime import datetime, time
from .base import FraudRule
from app.models.schemas import FraudFlag, TransactionCheckRequest


class NewAccountLargeAmountRule(FraudRule):
    """New account (<7 days) with large transaction"""

    def __init__(self):
        super().__init__(
            name="new_account_large_amount",
            description="New account with large transaction",
            base_score=30,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.account_age_days is not None and transaction.account_age_days < 7:
            if transaction.amount > 100000:  # ₦100k
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Account only {transaction.account_age_days} days old requesting ₦{transaction.amount:,.0f}",
                    score=self.base_score,
                    confidence=0.87
                )
        return None


class VelocityCheckRule(FraudRule):
    """Transaction velocity - too many transactions in short time"""

    def __init__(self):
        super().__init__(
            name="velocity_check",
            description="Too many transactions in short time",
            base_score=30,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        velocity_data = context.get("velocity", {})
        count_10min = velocity_data.get("transaction_count_10min", 0)

        if count_10min > 3:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"{count_10min} transactions in 10 minutes",
                score=self.base_score,
                confidence=0.82
            )
        return None


class SuspiciousHoursRule(FraudRule):
    """Transaction during suspicious hours (2am-5am)"""

    def __init__(self):
        super().__init__(
            name="suspicious_hours",
            description="Transaction during suspicious hours",
            base_score=15,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        current_time = datetime.now().time()
        if time(2, 0) <= current_time <= time(5, 0):
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"Transaction at {current_time.strftime('%I:%M %p')} - unusual hours",
                score=self.base_score,
                confidence=0.65
            )
        return None


class DisposableEmailRule(FraudRule):
    """Detects disposable/temporary email addresses"""

    def __init__(self):
        super().__init__(
            name="disposable_email",
            description="Using disposable email service",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.email:
            disposable_domains = [
                "tempmail.com", "guerrillamail.com", "10minutemail.com",
                "mailinator.com", "throwaway.email", "temp-mail.org"
            ]
            email_domain = transaction.email.split("@")[-1].lower()

            if email_domain in disposable_domains:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Using disposable email: {email_domain}",
                    score=self.base_score,
                    confidence=0.90
                )
        return None


# Add more universal rules here...
# - RoundAmountRule
# - VPNProxyRule
# - DeviceSharingRule
# - ImpossibleTravelRule
# etc.


# Export all universal rules
UNIVERSAL_RULES = [
    NewAccountLargeAmountRule(),
    VelocityCheckRule(),
    SuspiciousHoursRule(),
    DisposableEmailRule(),
    # Add more as they're migrated...
]
