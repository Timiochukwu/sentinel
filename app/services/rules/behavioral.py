"""
Behavioral analysis fraud detection rules

This module contains fraud detection rules based on user behavioral patterns,
including mouse movements, typing patterns, session behavior, and bot detection.

Rules for:
- Mouse movement analysis
- Typing speed and keystroke dynamics
- Session duration and activity patterns
- Bot and automation detection
"""

from typing import Optional, Dict, Any
from app.schemas import TransactionCheckRequest, FraudFlag
from .base import FraudRule


class MouseMovementSuspiciousRule(FraudRule):
    """Mouse movement pattern is too perfect/robotic"""
    def __init__(self):
        super().__init__(
            name="mouse_movement_suspicious",
            description="Mouse movement pattern is robotic",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            score = transaction.behavioral_features.session.mouse_movement_score
            if score is not None and score > 95:  # Too perfect = likely bot
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"Mouse pattern too perfect: {score}")
        return None

class TypingSpeedConstantRule(FraudRule):
    """Typing speed is unnaturally constant"""
    def __init__(self):
        super().__init__(
            name="typing_speed_constant",
            description="Typing speed unnaturally consistent",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        typing_variance = context.get("typing_speed_variance", 0)
        if typing_variance < 0.1:  # Very low variance = bot
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"Typing speed variance too low: {typing_variance}")
        return None

class KeystrokeDynamicsFailureRule(FraudRule):
    """Keystroke dynamics fails to match user profile"""
    def __init__(self):
        super().__init__(
            name="keystroke_dynamics_failure",
            description="Keystroke pattern differs from user profile",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            current_score = transaction.behavioral_features.session.keystroke_dynamics_score
            user_baseline = context.get("user_keystroke_baseline", 75)
            if current_score and abs(current_score - user_baseline) > 20:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message=f"Keystroke pattern deviation: {current_score} vs {user_baseline}")
        return None

class SessionDurationAnomalyRule(FraudRule):
    """Session duration is unusually short or long"""
    def __init__(self):
        super().__init__(
            name="session_duration_anomaly",
            description="Session duration is anomalous",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            duration = transaction.behavioral_features.session.session_duration_seconds
            if duration and (duration < 5 or duration > 3600):  # Too fast or too slow
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message=f"Anomalous session: {duration}s")
        return None

class WindowResizeActivityRule(FraudRule):
    """Window resizing indicates testing/automation"""
    def __init__(self):
        super().__init__(
            name="window_resize_activity",
            description="Window resized during session",
            base_score=16,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            resized = transaction.behavioral_features.session.window_resized
            if resized:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.55, message="Window resized during session")
        return None

class TypingPatternDeviationRule(FraudRule):
    """Typing pattern deviates from user baseline"""
    def __init__(self):
        super().__init__(
            name="typing_pattern_deviation",
            description="Typing pattern deviates from baseline",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ato_signals and transaction.ato_signals.behavioral_deviation:
            if transaction.ato_signals.behavioral_deviation.typing_pattern_deviation:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message="Typing pattern deviates from baseline")
        return None

class MouseMovementDeviationRule(FraudRule):
    """Mouse movement pattern deviates"""
    def __init__(self):
        super().__init__(
            name="mouse_movement_deviation",
            description="Mouse movement deviates from baseline",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ato_signals and transaction.ato_signals.behavioral_deviation:
            if transaction.ato_signals.behavioral_deviation.mouse_movement_deviation:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Mouse movement deviates from baseline")
        return None

class RobotSessionDetectionRule(FraudRule):
    """Rule 43: Robot Session Detection"""
    def __init__(self):
        super().__init__(
            name="robot_session_detection",
            description="Likely bot session",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.session_duration_seconds and transaction.session_duration_seconds < 5:
            if transaction.mouse_movement_score and transaction.mouse_movement_score < 20:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.89, message="Bot-like behavior detected")
        return None

class SuspiciousTypingPatternRule(FraudRule):
    """Rule 44: Suspicious Typing Pattern"""
    def __init__(self):
        super().__init__(
            name="suspicious_typing_pattern",
            description="Abnormal typing speed",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.typing_speed_wpm and (transaction.typing_speed_wpm < 10 or transaction.typing_speed_wpm > 150):
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Unusual typing speed")
        return None

class KeystrokeDynamicsRule(FraudRule):
    """Rule 56: Keystroke Dynamics"""
    def __init__(self):
        super().__init__(
            name="keystroke_dynamics",
            description="Unusual keystroke dynamics",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.keystroke_dynamics_score and transaction.keystroke_dynamics_score < 30:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message="Keystroke dynamics anomaly")
        return None

class LowBehavioralConsistencyRule(FraudRule):
    """Rule 92: Low Behavioral Consistency"""
    def __init__(self):
        super().__init__(
            name="low_behavioral_consistency",
            description="Low behavioral consistency",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_consistency_score and transaction.behavioral_consistency_score < 30:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.84, message="Low behavioral consistency")
        return None

class BehavioralMouseMovementRule(FraudRule):
    """Rule: Unnatural mouse movement"""
    def __init__(self):
        super().__init__(
            name="mouse_movement_unnatural",
            description="Suspicious mouse movement pattern",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            if transaction.behavioral_features.session.mouse_movement_score and transaction.behavioral_features.session.mouse_movement_score < 20:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Unnatural mouse movement pattern")
        return None

class BehavioralTypingSpeedRule(FraudRule):
    """Rule: Extreme typing speed"""
    def __init__(self):
        super().__init__(
            name="typing_speed_extreme",
            description="Extreme typing speed (bot-like)",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            if transaction.behavioral_features.session.typing_speed_wpm:
                wpm = transaction.behavioral_features.session.typing_speed_wpm
                if wpm < 10 or wpm > 150:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"Extreme typing speed: {wpm} WPM")
        return None

class BehavioralKeystrokeDynamicsRule(FraudRule):
    """Rule: Poor keystroke dynamics"""
    def __init__(self):
        super().__init__(
            name="keystroke_dynamics_poor",
            description="Poor keystroke dynamics",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            if transaction.behavioral_features.session.keystroke_dynamics_score and transaction.behavioral_features.session.keystroke_dynamics_score < 25:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Poor keystroke dynamics")
        return None

class BehavioralCopyPasteRule(FraudRule):
    """Rule: Excessive copy/paste"""
    def __init__(self):
        super().__init__(
            name="copy_paste_excessive",
            description="Excessive copy/paste activity",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            if transaction.behavioral_features.session.copy_paste_count and transaction.behavioral_features.session.copy_paste_count > 8:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message=f"Excessive copy/paste: {transaction.behavioral_features.session.copy_paste_count} times")
        return None

class BehavioralSessionDurationRule(FraudRule):
    """Rule: Suspiciously short session"""
    def __init__(self):
        super().__init__(
            name="session_duration_short",
            description="Very short session duration",
            base_score=18,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            if transaction.behavioral_features.session.session_duration_seconds and transaction.behavioral_features.session.session_duration_seconds < 5:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message="Suspiciously short session (<5 seconds)")
        return None

class BehavioralLoginFrequencyRule(FraudRule):
    """Rule: Unusual login frequency"""
    def __init__(self):
        super().__init__(
            name="login_frequency_unusual",
            description="Unusual login frequency",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.login:
            if transaction.behavioral_features.login.login_frequency and transaction.behavioral_features.login.login_frequency > 20:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message=f"High login frequency: {transaction.behavioral_features.login.login_frequency} times")
        return None

class BehavioralFailedLoginVelocityRule(FraudRule):
    """Rule: Failed login velocity"""
    def __init__(self):
        super().__init__(
            name="failed_login_velocity_high",
            description="High failed login velocity",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.login:
            if transaction.behavioral_features.login.failed_login_velocity and transaction.behavioral_features.login.failed_login_velocity > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message="Account takeover attempt: failed logins then success")
        return None

class BehavioralPasswordResetRule(FraudRule):
    """Rule: Password reset before transaction"""
    def __init__(self):
        super().__init__(
            name="password_reset_txn",
            description="Password reset then transaction",
            base_score=38,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.login:
            if transaction.behavioral_features.login.password_reset_requests and transaction.behavioral_features.login.password_reset_requests > 0:
                if transaction.behavioral_features.login.password_reset_txn_time_gap and transaction.behavioral_features.login.password_reset_txn_time_gap < 10:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message="Account takeover: password reset + transaction")
        return None

class BehavioralTransactionVelocityRule(FraudRule):
    """Rule: High transaction velocity"""
    def __init__(self):
        super().__init__(
            name="txn_velocity_high",
            description="High transaction velocity",
            base_score=25,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.transaction:
            vel_hour = transaction.behavioral_features.transaction.velocity_last_hour or 0
            vel_day = transaction.behavioral_features.transaction.velocity_last_day or 0
            vel_week = transaction.behavioral_features.transaction.velocity_last_week or 0
            if vel_hour > 5 or vel_day > 30 or vel_week > 100:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"High velocity: {vel_hour}h, {vel_day}d, {vel_week}w")
        return None

class BehavioralFirstTransactionAmountRule(FraudRule):
    """Rule: First transaction unusually large"""
    def __init__(self):
        super().__init__(
            name="first_txn_amount_large",
            description="First transaction much larger than average",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.transaction:
            first = transaction.behavioral_features.transaction.first_transaction_amount or 0
            avg = transaction.behavioral_features.transaction.avg_transaction_amount or 0
            if avg > 0 and first > avg * 5:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="First transaction 5x+ larger than average")
        return None

class BehavioralUnusualTimeRule(FraudRule):
    """Rule: Transaction at unusual time"""
    def __init__(self):
        super().__init__(
            name="txn_unusual_time",
            description="Transaction at unusual time",
            base_score=18,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.transaction:
            hour = transaction.behavioral_features.transaction.txn_time_hour
            if hour is not None:
                if hour < 6 or hour > 22:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message=f"Transaction at unusual hour: {hour}")
        return None

class BehavioralWeekendTransactionRule(FraudRule):
    """Rule: Large transaction on weekend"""
    def __init__(self):
        super().__init__(
            name="weekend_large_txn",
            description="Large transaction on weekend",
            base_score=16,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.transaction:
            if transaction.behavioral_features.transaction.weekend_transaction and transaction.amount and transaction.amount > 500000:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message="Large transaction on weekend")
        return None

# PHASE 6: TRANSACTION FEATURES (40+ rules)

# Export all behavioral rules
BEHAVIORAL_RULES = [
    MouseMovementSuspiciousRule(),
    TypingSpeedConstantRule(),
    KeystrokeDynamicsFailureRule(),
    SessionDurationAnomalyRule(),
    WindowResizeActivityRule(),
    TypingPatternDeviationRule(),
    MouseMovementDeviationRule(),
    RobotSessionDetectionRule(),
    SuspiciousTypingPatternRule(),
    KeystrokeDynamicsRule(),
    LowBehavioralConsistencyRule(),
    BehavioralMouseMovementRule(),
    BehavioralTypingSpeedRule(),
    BehavioralKeystrokeDynamicsRule(),
    BehavioralCopyPasteRule(),
    BehavioralSessionDurationRule(),
    BehavioralLoginFrequencyRule(),
    BehavioralFailedLoginVelocityRule(),
    BehavioralPasswordResetRule(),
    BehavioralTransactionVelocityRule(),
    BehavioralFirstTransactionAmountRule(),
    BehavioralUnusualTimeRule(),
    BehavioralWeekendTransactionRule(),
]
