"""
Account Takeover (ATO) fraud detection rules

This module contains fraud detection rules specific to account takeover attacks,
including credential stuffing, password reset abuse, and suspicious login patterns.

Rules for:
- Failed login velocity and patterns
- Password reset abuse
- Biometric authentication failures
- Credential stuffing detection
"""

from typing import Optional, Dict, Any
from app.schemas import TransactionCheckRequest, FraudFlag
from .base import FraudRule


class LoginFailureAccelerationRule(FraudRule):
    """Failed login attempts accelerating"""
    def __init__(self):
        super().__init__(
            name="login_failure_acceleration",
            description="Failed login attempts accelerating",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.login:
            attempts = transaction.behavioral_features.login.failed_login_attempts_24h
            velocity = transaction.behavioral_features.login.failed_login_velocity
            if attempts and velocity and velocity > 5:  # High velocity
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.83, message=f"Failed login velocity: {velocity} attempts/min")
        return None

class PasswordResetWithdrawalRule(FraudRule):
    """Password reset immediately followed by withdrawal"""
    def __init__(self):
        super().__init__(
            name="password_reset_withdrawal",
            description="Password reset → transaction within hours",
            base_score=38,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.login:
            gap = transaction.behavioral_features.login.password_reset_txn_time_gap
            if gap and gap < 2:  # Within 2 hours
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.91, message=f"Password reset {gap}h before txn")
        return None

class BiometricAuthFailureRule(FraudRule):
    """Biometric authentication fails, password used instead"""
    def __init__(self):
        super().__init__(
            name="biometric_auth_failure",
            description="Biometric auth failed, fallback to password",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        biometric_available = context.get("biometric_available", False)
        if transaction.behavioral_features and transaction.behavioral_features.login:
            biometric_used = transaction.behavioral_features.login.biometric_auth
            if biometric_available and not biometric_used:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Biometric auth skipped, password used")
        return None

class ExcessiveFailedLoginsRule(FraudRule):
    """Rule 32: Excessive Failed Logins - Account takeover indicator"""

    def __init__(self):
        super().__init__(
            name="excessive_failed_logins",
            description="Too many failed login attempts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.failed_login_count_24h and transaction.failed_login_count_24h >= 5:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"{transaction.failed_login_count_24h} failed logins in 24h - possible account takeover",
                score=self.base_score,
                confidence=0.92
            )
        if transaction.failed_login_count_7d and transaction.failed_login_count_7d >= 10:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"{transaction.failed_login_count_7d} failed logins in 7 days",
                score=self.base_score - 10,  # Slightly lower for 7-day pattern
                confidence=0.85
            )
        return None

class ATOPasswordResetRule(FraudRule):
    """Rule: ATO - Password reset pattern"""
    def __init__(self):
        super().__init__(
            name="ato_password_reset",
            description="Account takeover: password reset",
            base_score=36,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ato_signals and transaction.ato_signals.classic_patterns:
            if transaction.ato_signals.classic_patterns.password_reset_txn:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message="Account takeover: password reset detected")
        return None

# Export all ATO rules
ATO_RULES = [
    LoginFailureAccelerationRule(),
    PasswordResetWithdrawalRule(),
    BiometricAuthFailureRule(),
    ExcessiveFailedLoginsRule(),
    ATOPasswordResetRule(),
]
