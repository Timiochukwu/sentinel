"""Fraud detection rules engine - 15+ detection rules"""

from typing import List, Dict, Any, Optional
from datetime import datetime, time
import re
from app.models.schemas import FraudFlag, TransactionCheckRequest


class FraudRule:
    """Base class for fraud detection rules"""

    def __init__(self, name: str, description: str, base_score: int, severity: str):
        self.name = name
        self.description = description
        self.base_score = base_score
        self.severity = severity

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        """
        Check if this rule is triggered

        Args:
            transaction: Transaction data
            context: Additional context (e.g., consortium data, velocity data)

        Returns:
            FraudFlag if rule is triggered, None otherwise
        """
        raise NotImplementedError


class NewAccountLargeAmountRule(FraudRule):
    """Rule 1: New Account Large Amount - Account <7 days + amount >₦100k"""

    def __init__(self):
        super().__init__(
            name="new_account_large_amount",
            description="New account with large transaction",
            base_score=30,
            severity="medium"
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


class LoanStackingRule(FraudRule):
    """Rule 2: Loan Stacking - Applied to 3+ lenders in 7 days"""

    def __init__(self):
        super().__init__(
            name="loan_stacking",
            description="Applied to multiple lenders recently",
            base_score=40,
            severity="critical"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        consortium_data = context.get("consortium", {})
        client_count = consortium_data.get("client_count", 0)

        if client_count >= 3:
            lenders = consortium_data.get("lenders", [])
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"Applied to {client_count} other lenders this week",
                score=self.base_score,
                confidence=0.92,
                metadata={"lenders": lenders, "count": client_count}
            )
        return None


class SIMSwapPatternRule(FraudRule):
    """Rule 3: SIM Swap Pattern - Phone changed + new device + withdrawal"""

    def __init__(self):
        super().__init__(
            name="sim_swap_pattern",
            description="Pattern indicating SIM swap attack",
            base_score=45,
            severity="critical"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.phone_changed_recently and context.get("new_device", False):
            if transaction.transaction_type in ["withdrawal", "loan_disbursement"]:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message="Phone changed + new device + withdrawal - classic SIM swap pattern",
                    score=self.base_score,
                    confidence=0.88
                )
        return None


class SuspiciousHoursRule(FraudRule):
    """Rule 4: Suspicious Hours - Transaction 2am-5am"""

    def __init__(self):
        super().__init__(
            name="suspicious_hours",
            description="Transaction during suspicious hours",
            base_score=15,
            severity="low"
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


class VelocityCheckRule(FraudRule):
    """Rule 5: Velocity Check - >3 transactions in 10 minutes"""

    def __init__(self):
        super().__init__(
            name="velocity_check",
            description="Too many transactions in short time",
            base_score=30,
            severity="medium"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        velocity_data = context.get("velocity", {})
        count_10min = velocity_data.get("transaction_count_10min", 0)

        if count_10min > 3:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"{count_10min} transactions in last 10 minutes",
                score=self.base_score,
                confidence=0.75
            )
        return None


class ContactChangeWithdrawalRule(FraudRule):
    """Rule 6: Contact Change + Withdrawal - Phone/email changed + withdrawal <48hrs"""

    def __init__(self):
        super().__init__(
            name="contact_change_withdrawal",
            description="Contact information changed before withdrawal",
            base_score=35,
            severity="high"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        contact_changed = transaction.phone_changed_recently or transaction.email_changed_recently

        if contact_changed and transaction.transaction_type in ["withdrawal", "loan_disbursement"]:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message="Contact info changed recently followed by withdrawal",
                score=self.base_score,
                confidence=0.82
            )
        return None


class NewDeviceRule(FraudRule):
    """Rule 7: New Device - First time device + large amount"""

    def __init__(self):
        super().__init__(
            name="new_device",
            description="First time device with large transaction",
            base_score=25,
            severity="medium"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if context.get("new_device", False) and transaction.amount > 50000:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"First time device requesting ₦{transaction.amount:,.0f}",
                score=self.base_score,
                confidence=0.71
            )
        return None


class RoundAmountRule(FraudRule):
    """Rule 8: Round Amount - Exactly ₦50k, ₦100k, ₦500k + new account"""

    def __init__(self):
        super().__init__(
            name="round_amount",
            description="Suspiciously round transaction amount",
            base_score=15,
            severity="low"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        round_amounts = [50000, 100000, 200000, 500000, 1000000]
        is_new_account = transaction.account_age_days is not None and transaction.account_age_days < 14

        if transaction.amount in round_amounts and is_new_account:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"Exact amount ₦{transaction.amount:,.0f} on new account",
                score=self.base_score,
                confidence=0.58
            )
        return None


class MaximumFirstTransactionRule(FraudRule):
    """Rule 9: Maximum First Transaction - First txn = max loan amount"""

    def __init__(self):
        super().__init__(
            name="maximum_first_transaction",
            description="First transaction at maximum amount",
            base_score=25,
            severity="medium"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.is_first_transaction:
            max_loan = context.get("max_loan_amount", 500000)
            if transaction.amount >= max_loan * 0.95:  # Within 95% of max
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"First transaction at maximum amount (₦{transaction.amount:,.0f})",
                    score=self.base_score,
                    confidence=0.79
                )
        return None


class ImpossibleTravelRule(FraudRule):
    """Rule 10: Impossible Travel - Lagos to Kano in 2 hours"""

    def __init__(self):
        super().__init__(
            name="impossible_travel",
            description="Geographically impossible travel speed",
            base_score=30,
            severity="high"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        last_location = context.get("last_location", {})

        if transaction.latitude and transaction.longitude and last_location:
            # Simple distance check (would use proper geolocation in production)
            distance_km = self._calculate_distance(
                transaction.latitude, transaction.longitude,
                last_location.get("latitude"), last_location.get("longitude")
            )

            time_diff_hours = last_location.get("time_diff_hours", 0)

            if time_diff_hours > 0 and distance_km > 100:
                speed_kmh = distance_km / time_diff_hours
                if speed_kmh > 120:  # Unrealistic travel speed
                    return FraudFlag(
                        type=self.name,
                        severity=self.severity,
                        message=f"Traveled {distance_km:.0f}km in {time_diff_hours:.1f}h ({speed_kmh:.0f}km/h)",
                        score=self.base_score,
                        confidence=0.91
                    )
        return None

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Simple distance calculation (placeholder - use proper geopy in production)"""
        # Simplified: 1 degree ≈ 111km
        if lat2 is None or lon2 is None:
            return 0
        return abs(lat1 - lat2) * 111 + abs(lon1 - lon2) * 111


class VPNProxyRule(FraudRule):
    """Rule 11: VPN/Proxy - IP from known VPN service"""

    def __init__(self):
        super().__init__(
            name="vpn_proxy",
            description="IP from known VPN/proxy service",
            base_score=20,
            severity="low"
        )
        # Known VPN IP ranges (simplified - use a proper service like IPHub in production)
        self.vpn_indicators = ["10.", "172.", "192.168."]

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ip_address:
            if context.get("is_vpn", False):
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"IP {transaction.ip_address} identified as VPN/proxy",
                    score=self.base_score,
                    confidence=0.72
                )
        return None


class DisposableEmailRule(FraudRule):
    """Rule 12: Disposable Email - Email from tempmail, guerrillamail, etc"""

    def __init__(self):
        super().__init__(
            name="disposable_email",
            description="Disposable/temporary email address",
            base_score=20,
            severity="low"
        )
        self.disposable_domains = [
            "tempmail.com", "guerrillamail.com", "10minutemail.com",
            "throwaway.email", "mailinator.com", "temp-mail.org"
        ]

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.email:
            email_lower = transaction.email.lower()
            for domain in self.disposable_domains:
                if domain in email_lower:
                    return FraudFlag(
                        type=self.name,
                        severity=self.severity,
                        message=f"Disposable email service detected: {domain}",
                        score=self.base_score,
                        confidence=0.95
                    )
        return None


class DeviceSharingRule(FraudRule):
    """Rule 13: Device Sharing - Same device used for 5+ accounts"""

    def __init__(self):
        super().__init__(
            name="device_sharing",
            description="Device used by multiple accounts",
            base_score=35,
            severity="high"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        device_usage = context.get("device_usage", {})
        account_count = device_usage.get("account_count", 0)

        if account_count >= 5:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"Device used by {account_count} different accounts",
                score=self.base_score,
                confidence=0.84
            )
        return None


class DormantAccountActivationRule(FraudRule):
    """Rule 14: Dormant Account Activation - No activity 90 days, suddenly active"""

    def __init__(self):
        super().__init__(
            name="dormant_account_activation",
            description="Long-dormant account suddenly active",
            base_score=20,
            severity="medium"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.dormant_days and transaction.dormant_days >= 90:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"Account dormant for {transaction.dormant_days} days, suddenly active",
                score=self.base_score,
                confidence=0.68
            )
        return None


class SequentialApplicationsRule(FraudRule):
    """Rule 15: Sequential Applications - Pattern like user1@, user2@, user3@"""

    def __init__(self):
        super().__init__(
            name="sequential_applications",
            description="Sequential email/user ID pattern",
            base_score=30,
            severity="high"
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.email:
            # Check for patterns like user1@, user2@, test1@, etc.
            pattern = r'(user|test|demo|temp)\d+@'
            if re.search(pattern, transaction.email.lower()):
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Sequential pattern detected in email: {transaction.email}",
                    score=self.base_score,
                    confidence=0.81
                )
        return None


class FraudRulesEngine:
    """Main fraud detection rules engine"""

    def __init__(self):
        """Initialize all fraud detection rules"""
        self.rules: List[FraudRule] = [
            NewAccountLargeAmountRule(),
            LoanStackingRule(),
            SIMSwapPatternRule(),
            SuspiciousHoursRule(),
            VelocityCheckRule(),
            ContactChangeWithdrawalRule(),
            NewDeviceRule(),
            RoundAmountRule(),
            MaximumFirstTransactionRule(),
            ImpossibleTravelRule(),
            VPNProxyRule(),
            DisposableEmailRule(),
            DeviceSharingRule(),
            DormantAccountActivationRule(),
            SequentialApplicationsRule(),
        ]

    def evaluate(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any]
    ) -> tuple[int, str, str, List[FraudFlag]]:
        """
        Evaluate all fraud detection rules

        Args:
            transaction: Transaction data
            context: Additional context (consortium data, velocity data, etc.)

        Returns:
            Tuple of (risk_score, risk_level, decision, flags)
        """
        flags: List[FraudFlag] = []

        # Run all rules
        for rule in self.rules:
            flag = rule.check(transaction, context)
            if flag:
                flags.append(flag)

        # Calculate total risk score
        total_score = sum(flag.score for flag in flags)
        risk_score = min(total_score, 100)  # Cap at 100

        # Determine risk level and decision
        if risk_score >= 70:
            risk_level = "high"
            decision = "decline"
        elif risk_score >= 40:
            risk_level = "medium"
            decision = "review"
        else:
            risk_level = "low"
            decision = "approve"

        return risk_score, risk_level, decision, flags

    def get_rule_by_name(self, name: str) -> Optional[FraudRule]:
        """Get a specific rule by name"""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None

    def get_all_rule_names(self) -> List[str]:
        """Get all rule names"""
        return [rule.name for rule in self.rules]
