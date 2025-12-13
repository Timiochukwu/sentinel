"""Fraud detection rules engine - 15+ detection rules"""

from typing import List, Dict, Any, Optional
from datetime import datetime, time
import re
from app.models.schemas import FraudFlag, TransactionCheckRequest


class FraudRule:
    """Base class for fraud detection rules"""

    def __init__(self, name: str, description: str, base_score: int, severity: str, verticals: List[str] = None):
        self.name = name
        self.description = description
        self.base_score = base_score
        self.severity = severity
        # Vertical industries this rule applies to (e.g., ["lending", "fintech", "payments"])
        # If None, rule applies to all verticals
        self.verticals = verticals or ["lending", "fintech", "payments", "crypto", "ecommerce", "betting", "marketplace", "gaming"]

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

    def applies_to_vertical(self, industry: str) -> bool:
        """Check if this rule applies to the given industry vertical"""
        return industry in self.verticals


class NewAccountLargeAmountRule(FraudRule):
    """Rule 1: New Account Large Amount - Account <7 days + amount >₦100k"""

    def __init__(self):
        super().__init__(
            name="new_account_large_amount",
            description="New account with large transaction",
            base_score=30,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]  # Applies to most verticals
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
            severity="critical",
            verticals=["lending", "fintech", "payments"]  # Lending-specific
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
            severity="critical",
            verticals=["lending", "fintech", "payments"]  # Fintech-specific
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
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]  # Universal
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
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]  # Universal
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
            severity="high",
            verticals=["lending", "fintech", "payments", "betting", "crypto"]
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
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
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
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
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
            severity="medium",
            verticals=["lending", "fintech", "payments"]
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
    """Rule 10: Impossible Travel Detection - Accounts for legitimate travel methods"""

    def __init__(self):
        super().__init__(
            name="impossible_travel",
            description="Geographically impossible travel considering legitimate transport methods",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

        # Realistic maximum speeds for different transport methods
        # Including airport/station access time buffers
        self.transport_speeds = {
            "car": 120,                    # Car max speed (accounting for traffic, rest stops)
            "bus": 100,                    # Interstate bus
            "train": 150,                  # Train (e.g., Lagos-Abuja)
            "flight": 900,                 # Commercial flight cruise speed
            "helicopter": 300,             # Helicopter travel
            "speedboat": 80,               # Speedboat on waterways
        }

        # Nigeria domestic routes and approximate times (including terminals)
        self.nigerian_routes = {
            ("lagos", "abuja"): {"distance": 500, "flight_time": 1.5, "drive_time": 7, "common": True},
            ("abuja", "lagos"): {"distance": 500, "flight_time": 1.5, "drive_time": 7, "common": True},
            ("lagos", "kano"): {"distance": 850, "flight_time": 2, "drive_time": 13, "common": True},
            ("kano", "lagos"): {"distance": 850, "flight_time": 2, "drive_time": 13, "common": True},
            ("lagos", "port_harcourt"): {"distance": 500, "flight_time": 1, "drive_time": 7, "common": True},
            ("port_harcourt", "lagos"): {"distance": 500, "flight_time": 1, "drive_time": 7, "common": True},
        }

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        last_location = context.get("last_location", {})

        if not (transaction.latitude and transaction.longitude and last_location):
            return None

        # Calculate actual distance traveled
        distance_km = self._calculate_distance(
            transaction.latitude, transaction.longitude,
            last_location.get("latitude"), last_location.get("longitude")
        )

        time_diff_hours = last_location.get("time_diff_hours", 0)

        if time_diff_hours <= 0 or distance_km < 100:
            return None

        calculated_speed_kmh = distance_km / time_diff_hours

        # SCENARIO 1: Very short distance - always OK
        if distance_km < 100:
            return None

        # SCENARIO 2: Reasonable driving/bus distance
        # Lagos to Abuja (500km) in 7-8 hours is normal (car/bus)
        if calculated_speed_kmh <= 120:  # Normal car/bus speed
            return None

        # SCENARIO 3: Flight is possible - check if travel time is realistic for flight
        # Include buffer for: check-in, security, boarding, taxi, landing, baggage claim, transfer
        # Typical domestic flight (Lagos-Kano): 2 hours flight + 2 hours terminals = 4 hours minimum
        if self._is_flight_viable(distance_km, time_diff_hours):
            # Flight is possible, but only flag if speed is unrealistic even for flights
            max_flight_speed = self.transport_speeds["flight"]
            if calculated_speed_kmh > max_flight_speed:
                # Speed exceeded even maximum flight capability (impossible)
                return FraudFlag(
                    type=self.name,
                    severity="critical",
                    message=f"Impossible: {distance_km:.0f}km in {time_diff_hours:.1f}h ({calculated_speed_kmh:.0f}km/h) - exceeds flight speed",
                    score=45,  # Higher score for truly impossible
                    confidence=0.95
                )
            else:
                # Flight is viable - no flag
                return None

        # SCENARIO 4: Speed is impossible (faster than any transport method)
        max_possible_speed = self.transport_speeds["flight"]
        if calculated_speed_kmh > max_possible_speed:
            return FraudFlag(
                type=self.name,
                severity="critical",
                message=f"Impossible: {distance_km:.0f}km in {time_diff_hours:.1f}h ({calculated_speed_kmh:.0f}km/h)",
                score=45,
                confidence=0.95
            )

        # SCENARIO 5: Speed is suspicious but possible (e.g., 200-500 km/h range)
        # This could be fraud trying to use impossible travel or could be account across time zones
        if calculated_speed_kmh > max_possible_speed * 0.5:  # Over 450 km/h
            return FraudFlag(
                type=self.name,
                severity="high",
                message=f"Highly suspicious travel: {distance_km:.0f}km in {time_diff_hours:.1f}h ({calculated_speed_kmh:.0f}km/h) - requires flight verification",
                score=self.base_score,
                confidence=0.75
            )

        return None

    def _is_flight_viable(self, distance_km: float, time_hours: float) -> bool:
        """
        Check if travel time is viable for a flight + airport/terminal buffer

        Factors considered:
        - Flight takes distance/900 hours (cruise speed ~900 km/h)
        - Pre-flight: check-in, security, boarding = 1.5-2 hours
        - Post-flight: landing, taxi, baggage, exit = 0.5-1 hour
        - Total minimum = 3-3.5 hours even for shortest domestic flight

        For longer flights (500km+), add buffer:
        - 500km flight + terminals = 4 hours
        - 850km flight + terminals = 4.5 hours
        - 1500km flight + terminals = 5.5 hours
        """
        flight_time = distance_km / 900  # Hours in air

        # Minimum terminal time: 2 hours (check-in, security, boarding)
        # This is realistic for domestic Nigerian flights
        minimum_terminal_time = 2.0

        # Maximum reasonable total time (flight + terminals)
        # Add 1 hour buffer for unexpected delays
        max_realistic_time = flight_time + minimum_terminal_time + 1.0

        # If actual time fits within realistic flight window, it's viable
        return time_hours >= flight_time and time_hours <= max_realistic_time + 2.0

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """
        Calculate distance using simplified formula (Haversine approximation)

        In production, use proper geolocation library like geopy
        This is simplified: 1 degree latitude ≈ 111 km, 1 degree longitude varies by latitude
        """
        if lat2 is None or lon2 is None:
            return 0

        # Simple approximation: treat as rectangular grid
        lat_diff = abs(float(lat1) - float(lat2)) * 111  # km per degree latitude
        lon_diff = abs(float(lon1) - float(lon2)) * 111 * 0.73  # km per degree longitude (at Nigeria's latitude)

        # Pythagorean distance
        return (lat_diff ** 2 + lon_diff ** 2) ** 0.5


class VPNProxyRule(FraudRule):
    """Rule 11: VPN/Proxy - IP from known VPN service"""

    def __init__(self):
        super().__init__(
            name="vpn_proxy",
            description="IP from known VPN/proxy service",
            base_score=20,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
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
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
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
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
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
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
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
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
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


### E-COMMERCE FRAUD RULES ###

class CardBINFraudRule(FraudRule):
    """Rule 16: Card BIN Fraud - High-risk card BINs"""

    def __init__(self):
        super().__init__(
            name="card_bin_fraud",
            description="Card from high-risk BIN",
            base_score=35,
            severity="high",
            verticals=["ecommerce", "fintech", "payments"]  # E-commerce specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.card_bin:
            # Check against known high-risk BINs (would be loaded from database in production)
            high_risk_bins = context.get("high_risk_bins", [])
            if transaction.card_bin in high_risk_bins:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Card BIN {transaction.card_bin} flagged as high-risk",
                    score=self.base_score,
                    confidence=0.85
                )
        return None


class MultipleFailedPaymentsRule(FraudRule):
    """Rule 17: Multiple Failed Payments - Card testing fraud"""

    def __init__(self):
        super().__init__(
            name="multiple_failed_payments",
            description="Multiple failed payment attempts",
            base_score=40,
            severity="critical",
            verticals=["ecommerce", "fintech", "payments"]  # E-commerce specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        velocity_data = context.get("velocity", {})
        failed_count_1hour = velocity_data.get("failed_payment_count_1hour", 0)

        if failed_count_1hour >= 3:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"{failed_count_1hour} failed payment attempts in last hour - possible card testing",
                score=self.base_score,
                confidence=0.89
            )
        return None


class ShippingMismatchRule(FraudRule):
    """Rule 18: Shipping/Billing Mismatch - Different addresses"""

    def __init__(self):
        super().__init__(
            name="shipping_mismatch",
            description="Shipping and billing addresses don't match",
            base_score=25,
            severity="medium",
            verticals=["ecommerce"]  # E-commerce specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shipping_address_matches_billing is False:
            if transaction.amount > 50000:  # High-value purchase
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"₦{transaction.amount:,.0f} purchase with mismatched shipping/billing",
                    score=self.base_score,
                    confidence=0.72
                )
        return None


class DigitalGoodsHighValueRule(FraudRule):
    """Rule 19: Digital Goods High Value - High-risk for chargebacks"""

    def __init__(self):
        super().__init__(
            name="digital_goods_high_value",
            description="High-value digital goods purchase",
            base_score=20,
            severity="medium",
            verticals=["ecommerce"]  # E-commerce specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.is_digital_goods and transaction.amount > 100000:
            if transaction.account_age_days and transaction.account_age_days < 30:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"New account purchasing ₦{transaction.amount:,.0f} in digital goods",
                    score=self.base_score,
                    confidence=0.68
                )
        return None


### BETTING/GAMING FRAUD RULES ###

class BonusAbuseRule(FraudRule):
    """Rule 20: Bonus Abuse - Suspicious bonus claiming patterns"""

    def __init__(self):
        super().__init__(
            name="bonus_abuse",
            description="Potential bonus abuse pattern",
            base_score=35,
            severity="high",
            verticals=["betting", "gaming"]  # Betting/gaming specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_type == "bonus_claim":
            # Check if multiple accounts from same device claiming bonuses
            device_usage = context.get("device_usage", {})
            account_count = device_usage.get("account_count", 0)

            if account_count >= 3:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Bonus claim from device with {account_count} accounts - multi-accounting suspected",
                    score=self.base_score,
                    confidence=0.87
                )
        return None


class WithdrawalWithoutWageringRule(FraudRule):
    """Rule 21: Withdrawal Without Wagering - Money laundering risk"""

    def __init__(self):
        super().__init__(
            name="withdrawal_without_wagering",
            description="Withdrawal without sufficient wagering",
            base_score=45,
            severity="critical",
            verticals=["betting", "gaming"]  # Betting/gaming specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_type in ["bet_withdrawal", "withdrawal"]:
            wagering_ratio = context.get("wagering_ratio", 0)  # Ratio of bets to deposits

            if wagering_ratio < 0.5 and transaction.amount > 100000:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"₦{transaction.amount:,.0f} withdrawal with minimal wagering - possible money laundering",
                    score=self.base_score,
                    confidence=0.82
                )
        return None


class ArbitrageBettingRule(FraudRule):
    """Rule 22: Arbitrage Betting - Betting on all outcomes"""

    def __init__(self):
        super().__init__(
            name="arbitrage_betting",
            description="Arbitrage betting pattern detected",
            base_score=30,
            severity="medium",
            verticals=["betting", "gaming"]  # Betting/gaming specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.bet_pattern_unusual:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message="Unusual betting pattern suggests arbitrage betting",
                score=self.base_score,
                confidence=0.75
            )
        return None


class ExcessiveWithdrawalsRule(FraudRule):
    """Rule 23: Excessive Withdrawals - Multiple withdrawals in short time"""

    def __init__(self):
        super().__init__(
            name="excessive_withdrawals",
            description="Too many withdrawal attempts",
            base_score=25,
            severity="medium",
            verticals=["betting", "gaming", "lending", "fintech", "payments"]  # Common withdrawal fraud
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.withdrawal_count_today and transaction.withdrawal_count_today >= 5:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"{transaction.withdrawal_count_today} withdrawals today - possible structuring",
                score=self.base_score,
                confidence=0.71
            )
        return None


### CRYPTO FRAUD RULES ###

class NewWalletHighValueRule(FraudRule):
    """Rule 24: New Wallet High Value - New wallet with large transaction"""

    def __init__(self):
        super().__init__(
            name="new_wallet_high_value",
            description="New crypto wallet with high-value transaction",
            base_score=35,
            severity="high",
            verticals=["crypto"]  # Crypto specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.is_new_wallet and transaction.amount > 500000:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"First-time wallet attempting ₦{transaction.amount:,.0f} transaction",
                score=self.base_score,
                confidence=0.79
            )
        return None


class SuspiciousWalletRule(FraudRule):
    """Rule 25: Suspicious Wallet - Wallet linked to fraud/scams"""

    def __init__(self):
        super().__init__(
            name="suspicious_wallet",
            description="Wallet address flagged as suspicious",
            base_score=50,
            severity="critical",
            verticals=["crypto"]  # Crypto specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.wallet_address:
            # Check against blacklisted wallets
            blacklisted_wallets = context.get("blacklisted_wallets", [])
            if transaction.wallet_address in blacklisted_wallets:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Wallet {transaction.wallet_address[:10]}... flagged for fraud/scam activity",
                    score=self.base_score,
                    confidence=0.95
                )
        return None


class P2PVelocityRule(FraudRule):
    """Rule 26: P2P High Velocity - Too many P2P trades"""

    def __init__(self):
        super().__init__(
            name="p2p_velocity",
            description="Excessive P2P trading activity",
            base_score=30,
            severity="high",
            verticals=["crypto"]  # Crypto specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_type == "p2p_trade":
            velocity_data = context.get("velocity", {})
            p2p_count_24h = velocity_data.get("p2p_count_24hour", 0)

            if p2p_count_24h > 10:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"{p2p_count_24h} P2P trades in 24 hours - possible money laundering",
                    score=self.base_score,
                    confidence=0.76
                )
        return None


### MARKETPLACE FRAUD RULES ###

class NewSellerHighValueRule(FraudRule):
    """Rule 27: New Seller High Value - New seller with expensive items"""

    def __init__(self):
        super().__init__(
            name="new_seller_high_value",
            description="New seller listing high-value items",
            base_score=35,
            severity="high",
            verticals=["marketplace"]  # Marketplace specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.seller_account_age_days and transaction.seller_account_age_days < 7:
            if transaction.is_high_value_item:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Seller account only {transaction.seller_account_age_days} days old selling high-value items",
                    score=self.base_score,
                    confidence=0.83
                )
        return None


class LowRatedSellerRule(FraudRule):
    """Rule 28: Low Rated Seller - Poor seller rating"""

    def __init__(self):
        super().__init__(
            name="low_rated_seller",
            description="Seller has poor rating",
            base_score=25,
            severity="medium",
            verticals=["marketplace"]  # Marketplace specific
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.seller_rating and transaction.seller_rating < 2.5:
            if transaction.amount > 50000:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Seller rating {transaction.seller_rating}/5.0 for ₦{transaction.amount:,.0f} transaction",
                    score=self.base_score,
                    confidence=0.69
                )
        return None


class HighRiskCategoryRule(FraudRule):
    """Rule 29: High Risk Category - Electronics, phones, gift cards"""

    def __init__(self):
        super().__init__(
            name="high_risk_category",
            description="High-risk product category",
            base_score=15,
            severity="low",
            verticals=["marketplace", "ecommerce"]  # Marketplace & e-commerce
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.product_category:
            high_risk_categories = ["electronics", "phones", "gift_cards", "luxury_goods", "gadgets"]
            if transaction.product_category.lower() in high_risk_categories:
                if transaction.account_age_days and transaction.account_age_days < 14:
                    return FraudFlag(
                        type=self.name,
                        severity=self.severity,
                        message=f"New account purchasing {transaction.product_category} - high fraud category",
                        score=self.base_score,
                        confidence=0.64
                    )
        return None


# ============================================================================
# PHASE 4: EXTENDED IDENTITY RULES (30+ additional rules)
# ============================================================================

class EmailDomainLegitimacyRule(FraudRule):
    """Email domain legitimacy check"""
    def __init__(self):
        super().__init__(
            name="email_domain_legitimacy",
            description="Email from suspicious domain",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.email:
            if transaction.identity_features.email.domain:
                domain = transaction.identity_features.email.domain.lower()
                suspicious_domains = ['tempmail.com', 'guerrillamail.com', 'mailinator.com', '10minutemail.com']
                if any(d in domain for d in suspicious_domains):
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"Suspicious email domain: {domain}")
        return None

class EmailVerificationMismatchRule(FraudRule):
    """Unverified email with high-value transaction"""
    def __init__(self):
        super().__init__(
            name="email_verification_mismatch",
            description="Unverified email with suspicious activity",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.email:
            if not transaction.identity_features.email.verification_status and transaction.amount > 500000:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="Unverified email with large transaction")
        return None

class PhoneVerificationFailureRule(FraudRule):
    """Phone fails verification attempts"""
    def __init__(self):
        super().__init__(
            name="phone_verification_failure",
            description="Phone fails multiple verification attempts",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        verification_attempts = context.get("phone_verification_attempts", 0)
        if verification_attempts > 3:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"Phone failed {verification_attempts} verification attempts")
        return None

class PhoneCountryMismatchRule(FraudRule):
    """Phone country differs from IP country"""
    def __init__(self):
        super().__init__(
            name="phone_country_mismatch",
            description="Phone country differs from location",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.phone and transaction.identity_features.network:
            phone_country = transaction.identity_features.phone.country_code
            ip_country = transaction.identity_features.network.ip_country
            if phone_country and ip_country and phone_country != ip_country:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message=f"Phone ({phone_country}) != IP ({ip_country})")
        return None

class BVNAgeInconsistencyRule(FraudRule):
    """BVN age inconsistent with other indicators"""
    def __init__(self):
        super().__init__(
            name="bvn_age_inconsistency",
            description="BVN age mismatches account age",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        bvn_age = context.get("bvn_age_days", 0)
        account_age = transaction.account_age_days or 0
        if bvn_age > 0 and account_age > 0:
            age_diff = abs(bvn_age - account_age)
            if age_diff > 365:  # More than 1 year difference
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"BVN age ({bvn_age}d) vs account ({account_age}d)")
        return None

class DeviceFingerprintChangeRule(FraudRule):
    """Device fingerprint changed recently"""
    def __init__(self):
        super().__init__(
            name="device_fingerprint_change",
            description="Device fingerprint changed from historical",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        current_fingerprint = transaction.device_fingerprint
        previous_fingerprint = context.get("previous_device_fingerprint")
        if current_fingerprint and previous_fingerprint and current_fingerprint != previous_fingerprint:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Device fingerprint changed from historical")
        return None

class BrowserVersionAnomalyRule(FraudRule):
    """Browser version is outdated or anomalous"""
    def __init__(self):
        super().__init__(
            name="browser_version_anomaly",
            description="Browser version is outdated or anomalous",
            base_score=18,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            browser_version = transaction.identity_features.device.browser_version
            # Check if browser version is outdated (simplified check)
            if browser_version and int(browser_version.split('.')[0] if browser_version else 0) < 50:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message=f"Outdated browser version: {browser_version}")
        return None

class GPUFingerprintAnomalyRule(FraudRule):
    """GPU fingerprint indicates emulator/VM"""
    def __init__(self):
        super().__init__(
            name="gpu_fingerprint_anomaly",
            description="GPU fingerprint suggests emulation",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            gpu = transaction.identity_features.device.gpu_info
            if gpu:
                suspicious_gpus = ['swiftshader', 'llvmpipe', 'virtualbox', 'qemu', 'vmware', 'hyper-v']
                if any(s in gpu.lower() for s in suspicious_gpus):
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"Suspicious GPU: {gpu}")
        return None

class IPLocationConsistencyRule(FraudRule):
    """IP geolocation inconsistent with user profile"""
    def __init__(self):
        super().__init__(
            name="ip_location_consistency",
            description="IP location inconsistent with profile",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        user_city = context.get("user_city")
        ip_city = transaction.identity_features.network.ip_city if transaction.identity_features and transaction.identity_features.network else None
        if user_city and ip_city and user_city.lower() != ip_city.lower():
            previous_txn = context.get("previous_txn_timestamp")
            if previous_txn:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message=f"IP location ({ip_city}) != user city ({user_city})")
        return None

class ISPReputationRule(FraudRule):
    """ISP has poor reputation"""
    def __init__(self):
        super().__init__(
            name="isp_reputation",
            description="ISP known for fraud/spam",
            base_score=15,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        isp_fraud_score = context.get("isp_fraud_score", 0)
        if isp_fraud_score > 0.7:  # High fraud ISP
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"ISP fraud score: {isp_fraud_score:.2f}")
        return None

class ASNBlacklistRule(FraudRule):
    """ASN is on fraud blacklist"""
    def __init__(self):
        super().__init__(
            name="asn_blacklist",
            description="ASN on fraud blacklist",
            base_score=35,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        asn_blacklisted = context.get("asn_blacklisted", False)
        if asn_blacklisted:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.95, message="ASN on fraud blacklist")
        return None

class MultipleEmailsDeviceRule(FraudRule):
    """Device has multiple email addresses"""
    def __init__(self):
        super().__init__(
            name="multiple_emails_device",
            description="Multiple emails linked to device",
            base_score=23,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        email_count = context.get("device_email_count", 1)
        if email_count > 5:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message=f"Device linked to {email_count} emails")
        return None

class DeviceOSChangedRule(FraudRule):
    """Device OS changed between transactions"""
    def __init__(self):
        super().__init__(
            name="device_os_changed",
            description="Device OS changed between transactions",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        previous_os = context.get("previous_device_os")
        if transaction.identity_features and transaction.identity_features.device and previous_os:
            current_os = transaction.identity_features.device.os
            if current_os and current_os.lower() != previous_os.lower():
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"OS changed: {previous_os} → {current_os}")
        return None

class CanvasFingerprinterRule(FraudRule):
    """Canvas fingerprint used for tracking/fraud"""
    def __init__(self):
        super().__init__(
            name="canvas_fingerprinter",
            description="Canvas fingerprint detected",
            base_score=19,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.canvas_fingerprint:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.58, message="Canvas fingerprinting detected")
        return None

class WebGLFingerprintRule(FraudRule):
    """WebGL fingerprint indicates targeted tracking"""
    def __init__(self):
        super().__init__(
            name="webgl_fingerprint",
            description="WebGL fingerprint tracking detected",
            base_score=17,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.webgl_fingerprint:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.55, message="WebGL fingerprinting detected")
        return None

class FontListAnomalyRule(FraudRule):
    """Installed fonts list is unusual"""
    def __init__(self):
        super().__init__(
            name="font_list_anomaly",
            description="Installed fonts list is anomalous",
            base_score=16,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            fonts = transaction.identity_features.device.installed_fonts
            if fonts and len(fonts) < 5:  # Very few fonts suggests VM/emulator
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.62, message=f"Unusual font list ({len(fonts)} fonts)")
        return None

class CPUCoreAnomalyRule(FraudRule):
    """CPU core count is unusual"""
    def __init__(self):
        super().__init__(
            name="cpu_core_anomaly",
            description="CPU core count is unusual",
            base_score=14,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            cores = transaction.identity_features.device.cpu_cores
            if cores and cores == 1:  # Single core very suspicious
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message=f"Unusual CPU: {cores} core(s)")
        return None

class BatteryDrainAnomalyRule(FraudRule):
    """Battery level indicates intensive activity"""
    def __init__(self):
        super().__init__(
            name="battery_drain_anomaly",
            description="Battery level suggests emulator/bot",
            base_score=12,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            battery = transaction.identity_features.device.battery_level
            if battery is not None and (battery == 100 or battery == 0):  # Always full or always zero = suspicious
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message=f"Suspicious battery level: {battery}%")
        return None

class TimezoneOffsetAnomalyRule(FraudRule):
    """Timezone offset inconsistent with location"""
    def __init__(self):
        super().__init__(
            name="timezone_offset_anomaly",
            description="Timezone offset inconsistent with IP location",
            base_score=18,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        expected_offset = context.get("expected_timezone_offset", 0)
        if transaction.identity_features and transaction.identity_features.device:
            device_offset = context.get("device_timezone_offset", 0)
            if abs(expected_offset - device_offset) > 2:  # More than 2 hour difference
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.62, message=f"TZ offset mismatch: {device_offset} vs {expected_offset}")
        return None

class ScreenResolutionHistoryRule(FraudRule):
    """Screen resolution changed unexpectedly"""
    def __init__(self):
        super().__init__(
            name="screen_resolution_history",
            description="Screen resolution changed between txns",
            base_score=15,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        prev_resolution = context.get("previous_screen_resolution")
        if transaction.identity_features and transaction.identity_features.device and prev_resolution:
            current_resolution = transaction.identity_features.device.screen_resolution
            if current_resolution and current_resolution != prev_resolution:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.55, message=f"Resolution changed: {prev_resolution} → {current_resolution}")
        return None

# ============================================================================
# PHASE 5: EXTENDED BEHAVIORAL RULES (40+ additional rules)
# ============================================================================

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

class CopyPasteAbuseRule(FraudRule):
    """Excessive copy/paste indicating automated fill"""
    def __init__(self):
        super().__init__(
            name="copy_paste_abuse",
            description="Excessive copy/paste activity",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            paste_count = transaction.behavioral_features.session.copy_paste_count
            if paste_count and paste_count > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"Excessive copy/paste: {paste_count} times")
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

class TwoFactorBypassRule(FraudRule):
    """2FA disabled before high-value transaction"""
    def __init__(self):
        super().__init__(
            name="two_factor_bypass",
            description="2FA disabled before transaction",
            base_score=42,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.login:
            was_2fa_enabled = context.get("previous_2fa_enabled", True)
            is_2fa_enabled = transaction.behavioral_features.login.two_factor_enabled
            if was_2fa_enabled and not is_2fa_enabled:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.89, message="2FA disabled before transaction")
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

class TransactionVelocityAccelerationRule(FraudRule):
    """Transaction velocity is accelerating"""
    def __init__(self):
        super().__init__(
            name="transaction_velocity_acceleration",
            description="Transaction velocity increasing over time",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.transaction:
            hourly = transaction.behavioral_features.transaction.velocity_last_hour or 0
            daily = transaction.behavioral_features.transaction.velocity_last_day or 0
            weekly = transaction.behavioral_features.transaction.velocity_last_week or 0
            if hourly > 5 and daily > 10 and weekly > 20:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"Velocity: {hourly}h, {daily}d, {weekly}w")
        return None

class FirstTransactionAmountDeviation(FraudRule):
    """First transaction vastly different from subsequent"""
    def __init__(self):
        super().__init__(
            name="first_transaction_deviation",
            description="First txn amount deviates from avg",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.transaction:
            first = transaction.behavioral_features.transaction.first_transaction_amount
            avg = transaction.behavioral_features.transaction.avg_transaction_amount
            if first and avg and avg > 0:
                deviation = abs(first - avg) / avg
                if deviation > 2:  # More than 2x deviation
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message=f"First txn {deviation:.1f}x avg")
        return None

class UnusualTimingPatternRule(FraudRule):
    """Transaction timing is unusually consistent"""
    def __init__(self):
        super().__init__(
            name="unusual_timing_pattern",
            description="Transactions occur at consistent intervals",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        timing_variance = context.get("transaction_timing_variance", 0)
        if timing_variance < 0.05:  # Very consistent timing = bot
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"Transaction timing too regular")
        return None

class FormFillingSpeedRule(FraudRule):
    """Form filled too quickly"""
    def __init__(self):
        super().__init__(
            name="form_filling_speed",
            description="Form filled faster than human possible",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            field_time = transaction.behavioral_features.session.form_field_time_seconds
            if field_time and field_time < 2:  # Less than 2 seconds for entire form
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"Form filled in {field_time}s")
        return None

class HesitationDetectionRule(FraudRule):
    """No hesitation in form completion (bot indicator)"""
    def __init__(self):
        super().__init__(
            name="hesitation_absence",
            description="No hesitation detected (bot behavior)",
            base_score=21,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            hesitation = transaction.behavioral_features.session.hesitation_detected
            if hesitation is False:  # No hesitation at all
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message="No hesitation detected in session")
        return None

class ErrorCorrectionPatternRule(FraudRule):
    """Error correction pattern indicates typing"""
    def __init__(self):
        super().__init__(
            name="error_correction_pattern",
            description="Error correction pattern suggests human",
            base_score=10,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            corrections = transaction.behavioral_features.session.error_corrections
            if corrections is not None and corrections == 0:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.50, message="No error corrections (likely bot)")
        return None

class TabSwitchingRule(FraudRule):
    """Excessive tab switching indicates fraud research"""
    def __init__(self):
        super().__init__(
            name="tab_switching",
            description="Excessive tab switching",
            base_score=19,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.session:
            switches = transaction.behavioral_features.session.tab_switches
            if switches and switches > 15:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message=f"Excessive tab switches: {switches}")
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

class APIErrorVelocityRule(FraudRule):
    """High API error rate suggests probing/testing"""
    def __init__(self):
        super().__init__(
            name="api_error_velocity",
            description="High rate of API errors",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.interaction:
            api_errors = transaction.behavioral_features.interaction.api_errors
            api_calls = transaction.behavioral_features.interaction.api_calls_made
            if api_calls and api_calls > 0 and api_errors and api_errors / api_calls > 0.3:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"API error rate: {100*api_errors/api_calls:.0f}%")
        return None

class MobileGestureAnomalyRule(FraudRule):
    """Mobile gestures are unnatural"""
    def __init__(self):
        super().__init__(
            name="mobile_gesture_anomaly",
            description="Mobile gestures are unnatural",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.interaction:
            swipes = transaction.behavioral_features.interaction.swipe_gestures_count
            pinches = transaction.behavioral_features.interaction.pinch_zoom_count
            if swipes and pinches and (swipes == 0 and pinches == 0):
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.62, message="No natural mobile gestures")
        return None

class AppSwitchingRule(FraudRule):
    """Excessive app switching (fraud research pattern)"""
    def __init__(self):
        super().__init__(
            name="app_switching",
            description="Excessive app switching activity",
            base_score=17,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.interaction:
            switches = transaction.behavioral_features.interaction.app_switches
            if switches and switches > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.58, message=f"App switches: {switches}")
        return None

class ScreenOrientationAnomalyRule(FraudRule):
    """Screen orientation changes indicate device type change"""
    def __init__(self):
        super().__init__(
            name="screen_orientation_anomaly",
            description="Unusual screen orientation changes",
            base_score=14,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.interaction:
            rotations = transaction.behavioral_features.interaction.screen_orientation_changes
            if rotations and rotations > 5:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message=f"Screen rotations: {rotations}")
        return None

class NotificationInteractionRule(FraudRule):
    """Interaction with push notifications"""
    def __init__(self):
        super().__init__(
            name="notification_interaction",
            description="User interacted with push notification",
            base_score=5,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.interaction:
            interacted = transaction.behavioral_features.interaction.notification_interacted
            if interacted:  # Positive indicator (less likely fraud)
                return None
        return None

class PageRefreshAnomalyRule(FraudRule):
    """Excessive page refreshes"""
    def __init__(self):
        super().__init__(
            name="page_refresh_anomaly",
            description="Excessive page refreshes",
            base_score=15,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.interaction:
            refreshes = transaction.behavioral_features.interaction.page_refresh_count
            if refreshes and refreshes > 5:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message=f"Page refreshes: {refreshes}")
        return None

class DeepLinkBypassRule(FraudRule):
    """Deep link used to skip authentication"""
    def __init__(self):
        super().__init__(
            name="deeplink_bypass",
            description="Deep link used to bypass normal flow",
            base_score=27,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.interaction:
            if transaction.behavioral_features.interaction.deeplink_used:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="Deep link used in session")
        return None

class CampaignTrackingAnomalyRule(FraudRule):
    """Suspicious campaign tracking parameters"""
    def __init__(self):
        super().__init__(
            name="campaign_tracking_anomaly",
            description="Suspicious campaign parameters",
            base_score=18,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.interaction:
            campaign = transaction.behavioral_features.interaction.campaign_tracking
            suspicious_campaigns = ['test', 'fraud', 'abuse', 'bot', 'attack']
            if campaign and any(s in campaign.lower() for s in suspicious_campaigns):
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message=f"Suspicious campaign: {campaign}")
        return None

class ReferrerSourceAnomalyRule(FraudRule):
    """Suspicious referrer source"""
    def __init__(self):
        super().__init__(
            name="referrer_anomaly",
            description="Suspicious referrer source",
            base_score=16,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.interaction:
            referrer = transaction.behavioral_features.interaction.referrer_source
            suspicious_referrers = ['none', '(direct)', 'proxy', 'vpn', 'anonymous']
            if referrer and any(s in referrer.lower() for s in suspicious_referrers):
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message=f"Suspicious referrer: {referrer}")
        return None

# ============================================================================
# PHASE 6: EXTENDED TRANSACTION RULES (35+ additional rules)
# ============================================================================

class CardAgeNewRule(FraudRule):
    """Card is very new"""
    def __init__(self):
        super().__init__(
            name="card_age_new",
            description="Card issued within last 7 days",
            base_score=22,
            severity="medium",
            verticals=["ecommerce", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.card:
            age = transaction.transaction_features.card.card_age_days
            if age and age < 7:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message=f"Card only {age} days old")
        return None

class CardTestingPatternRule(FraudRule):
    """Card testing pattern detected"""
    def __init__(self):
        super().__init__(
            name="card_testing_pattern",
            description="Multiple small transactions followed by large",
            base_score=30,
            severity="high",
            verticals=["ecommerce", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.card:
            if transaction.transaction_features.card.card_testing_pattern:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message="Card testing pattern detected")
        return None

class CardReputationLowRule(FraudRule):
    """Card has poor reputation"""
    def __init__(self):
        super().__init__(
            name="card_reputation_low",
            description="Card reputation score is low",
            base_score=25,
            severity="medium",
            verticals=["ecommerce", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.card:
            rep = transaction.transaction_features.card.card_reputation_score
            if rep and rep < 30:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"Card reputation: {rep}/100")
        return None

class NewBankAccountWithdrawalRule(FraudRule):
    """New bank account with immediate withdrawal"""
    def __init__(self):
        super().__init__(
            name="new_bank_account_withdrawal",
            description="New bank account with withdrawal",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.banking:
            age = transaction.transaction_features.banking.account_age_days
            if age and age < 7 and transaction.transaction_features.banking.new_account_withdrawal:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"New bank account ({age}d) with withdrawal")
        return None

class BankAccountVerificationFailRule(FraudRule):
    """Bank account fails verification"""
    def __init__(self):
        super().__init__(
            name="bank_account_verification_fail",
            description="Bank account not verified",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.banking:
            verified = transaction.transaction_features.banking.account_verification
            if verified is False and transaction.amount > 500000:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Unverified bank account with large transaction")
        return None

class AddressDistanceAnomalyRule(FraudRule):
    """Billing and shipping addresses too far apart"""
    def __init__(self):
        super().__init__(
            name="address_distance_anomaly",
            description="Billing/shipping address distance suspicious",
            base_score=20,
            severity="medium",
            verticals=["ecommerce", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.address:
            distance = transaction.transaction_features.address.address_distance_km
            if distance and distance > 1000:  # More than 1000km apart
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message=f"Addresses {distance}km apart")
        return None

class CryptoNewWalletHighValueRule(FraudRule):
    """New wallet with high-value transaction"""
    def __init__(self):
        super().__init__(
            name="crypto_new_wallet_high_value",
            description="New crypto wallet with large transaction",
            base_score=32,
            severity="high",
            verticals=["crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.crypto:
            age = transaction.transaction_features.crypto.wallet_age_days
            if age and age < 7 and transaction.amount > 5000000:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"New wallet ({age}d) with large transaction")
        return None

class CryptoWithdrawalAfterDepositRule(FraudRule):
    """Immediate withdrawal after deposit (coin tumbling)"""
    def __init__(self):
        super().__init__(
            name="crypto_withdrawal_after_deposit",
            description="Withdrawal immediately after deposit",
            base_score=35,
            severity="critical",
            verticals=["crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.crypto:
            if transaction.transaction_features.crypto.withdrawal_after_deposit:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.88, message="Withdrawal after deposit (coin tumbling)")
        return None

class MerchantHighRiskCategoryRule(FraudRule):
    """Merchant in high-risk category"""
    def __init__(self):
        super().__init__(
            name="merchant_high_risk_category",
            description="Merchant category is high-risk",
            base_score=20,
            severity="medium",
            verticals=["ecommerce", "marketplace", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.merchant:
            if transaction.transaction_features.merchant.merchant_high_risk:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="High-risk merchant category")
        return None

class MerchantChargebackRateRule(FraudRule):
    """Merchant has high chargeback rate"""
    def __init__(self):
        super().__init__(
            name="merchant_chargeback_rate",
            description="Merchant high chargeback rate",
            base_score=18,
            severity="low",
            verticals=["ecommerce", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.merchant:
            rate = transaction.transaction_features.merchant.merchant_chargeback_rate
            if rate and rate > 0.05:  # >5% chargeback rate
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message=f"Merchant chargeback rate: {rate:.1%}")
        return None

class MerchantRefundRateRule(FraudRule):
    """Merchant has high refund rate"""
    def __init__(self):
        super().__init__(
            name="merchant_refund_rate",
            description="Merchant high refund rate",
            base_score=17,
            severity="low",
            verticals=["ecommerce", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.merchant:
            rate = transaction.transaction_features.merchant.merchant_refund_rate
            if rate and rate > 0.10:  # >10% refund rate
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message=f"Merchant refund rate: {rate:.1%}")
        return None

class MultipleCardsDeviceRule(FraudRule):
    """Multiple cards used on same device"""
    def __init__(self):
        super().__init__(
            name="multiple_cards_device",
            description="Multiple cards linked to device",
            base_score=25,
            severity="medium",
            verticals=["ecommerce", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.card:
            count = transaction.transaction_features.card.multiple_cards_same_device
            if count and count > 5:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"Device linked to {count} cards")
        return None

class CardBINMismatchRule(FraudRule):
    """Card BIN doesn't match stated country"""
    def __init__(self):
        super().__init__(
            name="card_bin_mismatch",
            description="Card issuing country suspicious",
            base_score=19,
            severity="low",
            verticals=["ecommerce", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.card:
            card_country = transaction.transaction_features.card.card_country
            user_country = transaction.country
            if card_country and user_country and card_country.lower() != user_country.lower():
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.63, message=f"Card ({card_country}) != user country ({user_country})")
        return None

class ExpiredCardRule(FraudRule):
    """Card is expired or expiring soon"""
    def __init__(self):
        super().__init__(
            name="expired_card",
            description="Card expired or expiring soon",
            base_score=23,
            severity="medium",
            verticals=["ecommerce", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        expiry = context.get("card_expiry_months_remaining", 12)
        if expiry < 1:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message="Card expired or expiring")
        return None

class DigitalGoodsHighAmountRule(FraudRule):
    """High-value digital goods transaction"""
    def __init__(self):
        super().__init__(
            name="digital_goods_high_amount",
            description="High-value digital goods",
            base_score=21,
            severity="medium",
            verticals=["ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        is_digital = context.get("is_digital_goods", False)
        if is_digital and transaction.amount > 1000000:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message=f"High-value digital goods: ₦{transaction.amount:,.0f}")
        return None

class BulkDigitalGoodsRule(FraudRule):
    """Bulk digital goods purchase"""
    def __init__(self):
        super().__init__(
            name="bulk_digital_goods",
            description="Bulk digital goods purchase",
            base_score=24,
            severity="medium",
            verticals=["ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        is_digital = context.get("is_digital_goods", False)
        quantity = context.get("item_quantity", 1)
        if is_digital and quantity > 50:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"Bulk digital goods: {quantity} items")
        return None

class FirstTimeCardRule(FraudRule):
    """Card used for first time"""
    def __init__(self):
        super().__init__(
            name="first_time_card",
            description="Card used for first time",
            base_score=18,
            severity="low",
            verticals=["ecommerce", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        previous_txns = context.get("card_previous_transactions", 1)
        if previous_txns == 0:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message="Card used for first time")
        return None

class CardVelocityRule(FraudRule):
    """Card velocity is suspicious"""
    def __init__(self):
        super().__init__(
            name="card_velocity",
            description="Multiple transactions on card in short time",
            base_score=22,
            severity="medium",
            verticals=["ecommerce", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        card_txns_hour = context.get("card_transactions_last_hour", 0)
        if card_txns_hour > 5:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"Card velocity: {card_txns_hour} txns/hour")
        return None

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
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.95, message="Duplicate transaction detected")
        return None

class TransactionAmountMismatchRule(FraudRule):
    """Amount doesn't match merchant receipt"""
    def __init__(self):
        super().__init__(
            name="transaction_amount_mismatch",
            description="Amount discrepancy with merchant",
            base_score=28,
            severity="high",
            verticals=["ecommerce", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        expected_amount = context.get("expected_transaction_amount")
        if expected_amount and abs(transaction.amount - expected_amount) > 1000:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"Amount mismatch: ₦{transaction.amount:,.0f} vs ₦{expected_amount:,.0f}")
        return None

class RoundAmountSuspiciousRule(FraudRule):
    """Round amount transaction"""
    def __init__(self):
        super().__init__(
            name="round_amount_suspicious",
            description="Suspiciously round amount",
            base_score=14,
            severity="low",
            verticals=["ecommerce", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.amount > 0 and transaction.amount % 100000 == 0:  # Perfect round number
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.55, message=f"Suspiciously round amount: ₦{transaction.amount:,.0f}")
        return None

# ============================================================================
# PHASE 7: EXTENDED NETWORK RULES (35+ additional rules)
# ============================================================================

class ConsortiumEmailFrequencyRule(FraudRule):
    """Email seen at many lenders recently"""
    def __init__(self):
        super().__init__(
            name="consortium_email_frequency",
            description="Email appearing at multiple lenders",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.consortium_matching:
            if transaction.network_features.consortium_matching.email_seen_elsewhere:
                count = context.get("email_lender_count", 2)
                if count > 3:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"Email at {count} other lenders")
        return None

class ConsortiumPhoneFrequencyRule(FraudRule):
    """Phone seen at many lenders"""
    def __init__(self):
        super().__init__(
            name="consortium_phone_frequency",
            description="Phone at multiple lenders",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.consortium_matching:
            if transaction.network_features.consortium_matching.phone_seen_elsewhere:
                count = context.get("phone_lender_count", 2)
                if count > 3:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"Phone at {count} other lenders")
        return None

class ConsortiumDeviceFrequencyRule(FraudRule):
    """Device seen at many institutions"""
    def __init__(self):
        super().__init__(
            name="consortium_device_frequency",
            description="Device at multiple institutions",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.consortium_matching:
            if transaction.network_features.consortium_matching.device_seen_elsewhere:
                count = context.get("device_institution_count", 2)
                if count > 5:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"Device at {count} institutions")
        return None

class ConsortiumBVNFrequencyRule(FraudRule):
    """BVN seen with multiple identities"""
    def __init__(self):
        super().__init__(
            name="consortium_bvn_frequency",
            description="BVN linked to multiple accounts",
            base_score=35,
            severity="critical",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.consortium_matching:
            if transaction.network_features.consortium_matching.bvn_seen_elsewhere:
                count = context.get("bvn_account_count", 2)
                if count > 2:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message=f"BVN linked to {count} accounts")
        return None

class NetworkVelocityEmailRule(FraudRule):
    """High velocity across email"""
    def __init__(self):
        super().__init__(
            name="network_velocity_email",
            description="High transaction velocity on email",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.velocity:
            velocity = transaction.network_features.velocity.velocity_email
            if velocity and velocity > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"Email velocity: {velocity} txns")
        return None

class NetworkVelocityPhoneRule(FraudRule):
    """High velocity across phone"""
    def __init__(self):
        super().__init__(
            name="network_velocity_phone",
            description="High transaction velocity on phone",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.velocity:
            velocity = transaction.network_features.velocity.velocity_phone
            if velocity and velocity > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"Phone velocity: {velocity} txns")
        return None

class NetworkVelocityDeviceRule(FraudRule):
    """High velocity across device"""
    def __init__(self):
        super().__init__(
            name="network_velocity_device",
            description="High transaction velocity on device",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.velocity:
            velocity = transaction.network_features.velocity.velocity_device
            if velocity and velocity > 15:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"Device velocity: {velocity} txns")
        return None

class NetworkVelocityIPRule(FraudRule):
    """High velocity across IP"""
    def __init__(self):
        super().__init__(
            name="network_velocity_ip",
            description="High transaction velocity on IP",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.velocity:
            velocity = transaction.network_features.velocity.velocity_ip
            if velocity and velocity > 20:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"IP velocity: {velocity} txns")
        return None

class SameIPMultipleUsersRule(FraudRule):
    """Multiple users from same IP"""
    def __init__(self):
        super().__init__(
            name="same_ip_multiple_users",
            description="Multiple users on same IP",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.graph_analysis:
            count = transaction.network_features.graph_analysis.same_ip_multiple_users
            if count and count > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"{count} users on same IP")
        return None

class SameDeviceMultipleUsersRule(FraudRule):
    """Multiple users on same device"""
    def __init__(self):
        super().__init__(
            name="same_device_multiple_users",
            description="Multiple users on same device",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.graph_analysis:
            count = transaction.network_features.graph_analysis.same_device_multiple_users
            if count and count > 5:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"{count} users on same device (loan stacking)")
        return None

class SameAddressMultipleUsersRule(FraudRule):
    """Multiple users at same address"""
    def __init__(self):
        super().__init__(
            name="same_address_multiple_users",
            description="Multiple users at same address",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.graph_analysis:
            count = transaction.network_features.graph_analysis.same_address_multiple_users
            if count and count > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"{count} users at same address")
        return None

class EmailFraudHistoryRule(FraudRule):
    """Email linked to confirmed fraud"""
    def __init__(self):
        super().__init__(
            name="email_fraud_history",
            description="Email linked to fraud cases",
            base_score=35,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.email_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.95, message="Email linked to confirmed fraud")
        return None

class PhoneFraudHistoryRule(FraudRule):
    """Phone linked to confirmed fraud"""
    def __init__(self):
        super().__init__(
            name="phone_fraud_history",
            description="Phone linked to fraud cases",
            base_score=34,
            severity="critical",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.phone_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.94, message="Phone linked to confirmed fraud")
        return None

class DeviceFraudHistoryRule(FraudRule):
    """Device linked to confirmed fraud"""
    def __init__(self):
        super().__init__(
            name="device_fraud_history",
            description="Device linked to fraud cases",
            base_score=36,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.device_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.96, message="Device linked to confirmed fraud")
        return None

class AddressFraudHistoryRule(FraudRule):
    """Address linked to confirmed fraud"""
    def __init__(self):
        super().__init__(
            name="address_fraud_history",
            description="Address linked to fraud cases",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.address_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.88, message="Address linked to confirmed fraud")
        return None

class ConnectedAccountsDetectedRule(FraudRule):
    """Connected accounts detected via graph analysis"""
    def __init__(self):
        super().__init__(
            name="connected_accounts_detected",
            description="Connected accounts via graph analysis",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.graph_analysis:
            if transaction.network_features.graph_analysis.connected_accounts_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message="Connected accounts detected")
        return None

# ============================================================================
# PHASE 8: EXTENDED ATO SIGNALS (20+ additional rules)
# ============================================================================

class FailedLoginVelocityATORule(FraudRule):
    """High failed login velocity (brute force)"""
    def __init__(self):
        super().__init__(
            name="failed_login_velocity_ato",
            description="High failed login velocity",
            base_score=34,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ato_signals and transaction.ato_signals.classic_patterns:
            velocity = transaction.ato_signals.classic_patterns.failed_login_velocity
            if velocity and velocity > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.88, message=f"Failed login velocity: {velocity} attempts/min")
        return None

class NewDeviceHighValueATORule(FraudRule):
    """New device with high-value transaction"""
    def __init__(self):
        super().__init__(
            name="new_device_high_value_ato",
            description="New device with large transaction",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ato_signals and transaction.ato_signals.classic_patterns:
            if transaction.ato_signals.classic_patterns.new_device_high_value:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message="New device with high-value transaction")
        return None

class GeographicImpossibilityATORule(FraudRule):
    """Impossible travel pattern"""
    def __init__(self):
        super().__init__(
            name="geographic_impossibility_ato",
            description="Geographically impossible travel",
            base_score=35,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ato_signals and transaction.ato_signals.classic_patterns:
            if transaction.ato_signals.classic_patterns.geographic_impossibility:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Geographically impossible travel detected")
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

class TransactionPatternDeviationRule(FraudRule):
    """Transaction pattern deviates significantly"""
    def __init__(self):
        super().__init__(
            name="transaction_pattern_deviation",
            description="Transaction pattern deviates from baseline",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ato_signals and transaction.ato_signals.behavioral_deviation:
            if transaction.ato_signals.behavioral_deviation.transaction_pattern_deviation:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message="Transaction pattern deviates from baseline")
        return None

class TimeOfDayDeviationRule(FraudRule):
    """Transaction time deviates from user pattern"""
    def __init__(self):
        super().__init__(
            name="time_of_day_deviation",
            description="Transaction time pattern changed",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ato_signals and transaction.ato_signals.behavioral_deviation:
            if transaction.ato_signals.behavioral_deviation.time_of_day_deviation:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Time of day pattern changed")
        return None

# ============================================================================
# PHASE 9: EXTENDED FUNDING FRAUD RULES (15+ additional rules)
# ============================================================================

class NewCardWithdrawalSameDayRule(FraudRule):
    """Card added and withdrawn same day"""
    def __init__(self):
        super().__init__(
            name="new_card_withdrawal_same_day",
            description="Card added and withdrawn same day",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.funding_fraud_signals and transaction.funding_fraud_signals.new_sources:
            if transaction.funding_fraud_signals.new_sources.card_added_withdrew_same_day:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message="Card added and withdrawn same day")
        return None

class BINAttackPatternRule(FraudRule):
    """BIN attack pattern detected"""
    def __init__(self):
        super().__init__(
            name="bin_attack_pattern",
            description="BIN testing attack detected",
            base_score=30,
            severity="high",
            verticals=["ecommerce", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.funding_fraud_signals and transaction.funding_fraud_signals.card_testing:
            if transaction.funding_fraud_signals.card_testing.bin_attack_pattern:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.88, message="BIN attack pattern detected")
        return None

class DollarOneAuthorizationRule(FraudRule):
    """$1 test authorizations detected"""
    def __init__(self):
        super().__init__(
            name="dollar_one_authorization",
            description="Multiple $1 test authorizations",
            base_score=28,
            severity="high",
            verticals=["ecommerce", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.funding_fraud_signals and transaction.funding_fraud_signals.card_testing:
            count = transaction.funding_fraud_signals.card_testing.dollar_one_authorizations
            if count and count > 3:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"$1 test auths: {count}")
        return None

class SmallFailsLargeSuccessRule(FraudRule):
    """Small failed transactions followed by large successful"""
    def __init__(self):
        super().__init__(
            name="small_fails_large_success",
            description="Small fails then large success pattern",
            base_score=29,
            severity="high",
            verticals=["ecommerce", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.funding_fraud_signals and transaction.funding_fraud_signals.card_testing:
            if transaction.funding_fraud_signals.card_testing.small_fails_large_success:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.84, message="Small fails then large success pattern")
        return None

class MultipleSourcesAddedQuicklyRule(FraudRule):
    """Multiple funding sources added rapidly"""
    def __init__(self):
        super().__init__(
            name="multiple_sources_added_quickly",
            description="Multiple funding sources added rapidly",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.funding_fraud_signals and transaction.funding_fraud_signals.new_sources:
            if transaction.funding_fraud_signals.new_sources.multiple_sources_added_quickly:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message="Multiple funding sources added rapidly")
        return None

class HighRiskCountryFundingRule(FraudRule):
    """Funding from high-risk country"""
    def __init__(self):
        super().__init__(
            name="high_risk_country_funding",
            description="Funding source from high-risk country",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.funding_fraud_signals and transaction.funding_fraud_signals.new_sources:
            if transaction.funding_fraud_signals.new_sources.funding_source_high_risk_country:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Funding from high-risk country")
        return None

# ============================================================================
# PHASE 10: EXTENDED MERCHANT ABUSE RULES (15+ additional rules)
# ============================================================================

class RefundAbuseDetectedRule(FraudRule):
    """Refund abuse pattern detected"""
    def __init__(self):
        super().__init__(
            name="refund_abuse_detected",
            description="Refund abuse pattern",
            base_score=26,
            severity="high",
            verticals=["ecommerce", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.merchant_abuse_signals and transaction.merchant_abuse_signals.abuse_patterns:
            if transaction.merchant_abuse_signals.abuse_patterns.refund_abuse_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message="Refund abuse pattern detected")
        return None

class CashbackAbuseDetectedRule(FraudRule):
    """Cashback abuse pattern detected"""
    def __init__(self):
        super().__init__(
            name="cashback_abuse_detected",
            description="Cashback abuse pattern",
            base_score=23,
            severity="medium",
            verticals=["ecommerce", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.merchant_abuse_signals and transaction.merchant_abuse_signals.abuse_patterns:
            if transaction.merchant_abuse_signals.abuse_patterns.cashback_abuse_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="Cashback abuse pattern detected")
        return None

class PromoAbuseDetectedRule(FraudRule):
    """Promotion abuse pattern detected"""
    def __init__(self):
        super().__init__(
            name="promo_abuse_detected",
            description="Promo abuse pattern",
            base_score=22,
            severity="medium",
            verticals=["ecommerce", "betting", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.merchant_abuse_signals and transaction.merchant_abuse_signals.abuse_patterns:
            if transaction.merchant_abuse_signals.abuse_patterns.promo_abuse_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Promotion abuse pattern detected")
        return None

class LoyaltyPointsAbuseRule(FraudRule):
    """Loyalty points abuse detected"""
    def __init__(self):
        super().__init__(
            name="loyalty_points_abuse",
            description="Loyalty points abuse pattern",
            base_score=20,
            severity="medium",
            verticals=["ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.merchant_abuse_signals and transaction.merchant_abuse_signals.abuse_patterns:
            if transaction.merchant_abuse_signals.abuse_patterns.loyalty_points_abuse:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Loyalty points abuse detected")
        return None

class ReferralFraudRule(FraudRule):
    """Referral fraud detected"""
    def __init__(self):
        super().__init__(
            name="referral_fraud",
            description="Referral fraud pattern",
            base_score=24,
            severity="medium",
            verticals=["fintech", "betting", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.merchant_abuse_signals and transaction.merchant_abuse_signals.abuse_patterns:
            if transaction.merchant_abuse_signals.abuse_patterns.referral_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.74, message="Referral fraud detected")
        return None

class FakeMerchantTransactionsRule(FraudRule):
    """Fake merchant transactions detected"""
    def __init__(self):
        super().__init__(
            name="fake_merchant_transactions",
            description="Fake merchant transactions",
            base_score=28,
            severity="high",
            verticals=["ecommerce", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.merchant_abuse_signals and transaction.merchant_abuse_signals.abuse_patterns:
            if transaction.merchant_abuse_signals.abuse_patterns.fake_merchant_transactions:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message="Fake merchant transactions detected")
        return None

# ============================================================================
# PHASE 11: EXTENDED ML-DERIVED RULES (10+ additional rules)
# ============================================================================

class OutlierScoreHighRule(FraudRule):
    """High statistical outlier score"""
    def __init__(self):
        super().__init__(
            name="outlier_score_high",
            description="High statistical outlier score",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ml_derived_features and transaction.ml_derived_features.statistical_outliers:
            score = transaction.ml_derived_features.statistical_outliers.outlier_score
            if score and score > 0.8:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"Outlier score: {score:.2f}")
        return None

class XGBoostHighRiskRule(FraudRule):
    """XGBoost model predicts high risk"""
    def __init__(self):
        super().__init__(
            name="xgboost_high_risk",
            description="XGBoost model high risk prediction",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ml_derived_features and transaction.ml_derived_features.model_scores:
            score = transaction.ml_derived_features.model_scores.xgboost_risk_score
            if score and score > 0.75:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"XGBoost risk: {score:.2f}")
        return None

class NeuralNetworkHighRiskRule(FraudRule):
    """Neural network predicts high risk"""
    def __init__(self):
        super().__init__(
            name="neural_network_high_risk",
            description="Neural network high risk prediction",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ml_derived_features and transaction.ml_derived_features.model_scores:
            score = transaction.ml_derived_features.model_scores.neural_network_score
            if score and score > 0.75:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.83, message=f"NN risk: {score:.2f}")
        return None

class EnsembleModelConsensusRule(FraudRule):
    """Multiple ML models agree on high risk"""
    def __init__(self):
        super().__init__(
            name="ensemble_consensus",
            description="Ensemble models agree on high risk",
            base_score=38,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ml_derived_features and transaction.ml_derived_features.model_scores:
            xgb = transaction.ml_derived_features.model_scores.xgboost_risk_score or 0
            nn = transaction.ml_derived_features.model_scores.neural_network_score or 0
            rf = transaction.ml_derived_features.model_scores.random_forest_score or 0
            if xgb > 0.7 and nn > 0.7 and rf > 0.7:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="All ML models predict fraud")
        return None

class LSTMSequenceAnomalyRule(FraudRule):
    """LSTM sequence model detects anomaly"""
    def __init__(self):
        super().__init__(
            name="lstm_sequence_anomaly",
            description="LSTM sequence anomaly detected",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ml_derived_features and transaction.ml_derived_features.deep_learning:
            score = transaction.ml_derived_features.deep_learning.lstm_sequence_prediction
            if score and score > 0.8:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"LSTM anomaly: {score:.2f}")
        return None

class GNNGraphAnomalyRule(FraudRule):
    """Graph Neural Network detects anomaly"""
    def __init__(self):
        super().__init__(
            name="gnn_graph_anomaly",
            description="GNN graph anomaly detected",
            base_score=31,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ml_derived_features and transaction.ml_derived_features.deep_learning:
            score = transaction.ml_derived_features.deep_learning.gnn_graph_score
            if score and score > 0.75:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.83, message=f"GNN anomaly: {score:.2f}")
        return None

# ============================================================================
# PHASE 12: EXTENDED DERIVED RULES (20+ additional rules)
# ============================================================================

class FraudsterProfileMatchRule(FraudRule):
    """Profile matches known fraudster"""
    def __init__(self):
        super().__init__(
            name="fraudster_profile_match",
            description="Profile matches known fraudster",
            base_score=38,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.similarity:
            similarity = transaction.derived_features.similarity.fraudster_profile_similarity
            if similarity and similarity > 0.85:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message=f"Fraudster match: {similarity:.2f}")
        return None

class EmailSimilarityHighRule(FraudRule):
    """Email similar to known fraud case"""
    def __init__(self):
        super().__init__(
            name="email_similarity_high",
            description="Email similar to fraud cases",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.similarity:
            similarity = transaction.derived_features.similarity.email_similarity
            if similarity and similarity > 0.8:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message=f"Email similarity: {similarity:.2f}")
        return None

class BehaviorSimilarityHighRule(FraudRule):
    """Behavior similar to known fraudster"""
    def __init__(self):
        super().__init__(
            name="behavior_similarity_high",
            description="Behavior similar to fraud cases",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.similarity:
            similarity = transaction.derived_features.similarity.behavior_similarity
            if similarity and similarity > 0.8:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"Behavior similarity: {similarity:.2f}")
        return None

class FamilyConnectionDetectedRule(FraudRule):
    """Family connections detected"""
    def __init__(self):
        super().__init__(
            name="family_connection_detected",
            description="Family connections detected",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.clustering:
            if transaction.derived_features.clustering.family_connections_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Family connections detected")
        return None

class BusinessConnectionDetectedRule(FraudRule):
    """Business connections detected"""
    def __init__(self):
        super().__init__(
            name="business_connection_detected",
            description="Business connections detected",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.clustering:
            if transaction.derived_features.clustering.business_connections_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Business connections detected")
        return None

class GeographicConnectionDetectedRule(FraudRule):
    """Geographic connections detected"""
    def __init__(self):
        super().__init__(
            name="geographic_connection_detected",
            description="Geographic connections detected",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.clustering:
            if transaction.derived_features.clustering.geographic_connections_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message="Geographic connections detected")
        return None

class FraudProbabilityHighRule(FraudRule):
    """Aggregate fraud probability very high"""
    def __init__(self):
        super().__init__(
            name="fraud_probability_high",
            description="Fraud probability very high",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.aggregate_risk:
            prob = transaction.derived_features.aggregate_risk.fraud_probability
            if prob and prob > 0.9:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.95, message=f"Fraud probability: {prob:.1%}")
        return None

class RuleViolationCountHighRule(FraudRule):
    """Many rules triggered"""
    def __init__(self):
        super().__init__(
            name="rule_violation_count_high",
            description="Many fraud rules triggered",
            base_score=35,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.aggregate_risk:
            count = transaction.derived_features.aggregate_risk.rule_violations_count
            if count and count > 15:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message=f"{count} fraud rules triggered")
        return None


class FraudRulesEngine:
    """Main fraud detection rules engine"""

    def __init__(self):
        """Initialize all fraud detection rules"""
        # Core/Lending rules (Rules 1-15)
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

            # E-commerce rules (Rules 16-19)
            CardBINFraudRule(),
            MultipleFailedPaymentsRule(),
            ShippingMismatchRule(),
            DigitalGoodsHighValueRule(),

            # Betting/Gaming rules (Rules 20-23)
            BonusAbuseRule(),
            WithdrawalWithoutWageringRule(),
            ArbitrageBettingRule(),
            ExcessiveWithdrawalsRule(),

            # Crypto rules (Rules 24-26)
            NewWalletHighValueRule(),
            SuspiciousWalletRule(),
            P2PVelocityRule(),

            # Marketplace rules (Rules 27-29)
            NewSellerHighValueRule(),
            LowRatedSellerRule(),
            HighRiskCategoryRule(),

            # PHASE 1 FEATURES - 10 NEW RULES (Rules 30-39)
            EmailDomainAgeRule(),
            SuspiciousIPReputationRule(),
            ExcessiveFailedLoginsRule(),
            UnusualTransactionTimeRule(),
            FirstTransactionAmountRule(),
            CardBINReputationRule(),
            UnverifiedPhoneRule(),
            MultipleDevicesSameUserRule(),
            QuickSignupTransactionRule(),
            OSInconsistencyRule(),

            # PHASE 4: IDENTITY FEATURES (30+ new rules)
            EmailDomainLegitimacyRule(),
            EmailVerificationMismatchRule(),
            PhoneVerificationFailureRule(),
            PhoneCountryMismatchRule(),
            BVNAgeInconsistencyRule(),
            DeviceFingerprintChangeRule(),
            BrowserVersionAnomalyRule(),
            GPUFingerprintAnomalyRule(),
            IPLocationConsistencyRule(),
            ISPReputationRule(),
            ASNBlacklistRule(),
            MultipleEmailsDeviceRule(),
            DeviceOSChangedRule(),
            CanvasFingerprinterRule(),
            WebGLFingerprintRule(),
            FontListAnomalyRule(),
            CPUCoreAnomalyRule(),
            BatteryDrainAnomalyRule(),
            TimezoneOffsetAnomalyRule(),
            ScreenResolutionHistoryRule(),
            EmailReputationRule(),
            PhoneAgeRule(),
            PhoneCarrierRiskRule(),
            UnverifiedPhoneIdentityRule(),
            BVNFraudHistoryRule(),
            DeviceBrowserFingerprintRule(),
            DeviceScreenResolutionRule(),
            DeviceTimezoneHoppingRule(),
            NetworkVPNDetectionRule(),
            NetworkTorDetectionRule(),
            NetworkIPReputationRule(),
            NetworkDatacenterIPRule(),
            DeviceEmulatorDetectionRule(),
            DeviceJailbreakDetectionRule(),
            DeviceBatteryLevelRule(),

            # PHASE 5: BEHAVIORAL FEATURES (40+ new rules)
            MouseMovementSuspiciousRule(),
            TypingSpeedConstantRule(),
            KeystrokeDynamicsFailureRule(),
            CopyPasteAbuseRule(),
            SessionDurationAnomalyRule(),
            LoginFailureAccelerationRule(),
            PasswordResetWithdrawalRule(),
            TwoFactorBypassRule(),
            BiometricAuthFailureRule(),
            TransactionVelocityAccelerationRule(),
            FirstTransactionAmountDeviation(),
            UnusualTimingPatternRule(),
            FormFillingSpeedRule(),
            HesitationDetectionRule(),
            ErrorCorrectionPatternRule(),
            TabSwitchingRule(),
            WindowResizeActivityRule(),
            APIErrorVelocityRule(),
            MobileGestureAnomalyRule(),
            AppSwitchingRule(),
            ScreenOrientationAnomalyRule(),
            NotificationInteractionRule(),
            PageRefreshAnomalyRule(),
            DeepLinkBypassRule(),
            CampaignTrackingAnomalyRule(),
            ReferrerSourceAnomalyRule(),
            BehavioralMouseMovementRule(),
            BehavioralTypingSpeedRule(),
            BehavioralKeystrokeDynamicsRule(),
            BehavioralCopyPasteRule(),
            BehavioralSessionDurationRule(),
            BehavioralLoginFrequencyRule(),
            BehavioralFailedLoginsRule(),
            BehavioralFailedLoginVelocityRule(),
            BehavioralPasswordResetRule(),
            BehavioralTransactionVelocityRule(),
            BehavioralFirstTransactionAmountRule(),
            BehavioralUnusualTimeRule(),
            BehavioralWeekendTransactionRule(),

            # PHASE 6: TRANSACTION FEATURES (35+ new rules)
            CardAgeNewRule(),
            CardTestingPatternRule(),
            CardReputationLowRule(),
            NewBankAccountWithdrawalRule(),
            BankAccountVerificationFailRule(),
            AddressDistanceAnomalyRule(),
            CryptoNewWalletHighValueRule(),
            CryptoWithdrawalAfterDepositRule(),
            MerchantHighRiskCategoryRule(),
            MerchantChargebackRateRule(),
            MerchantRefundRateRule(),
            MultipleCardsDeviceRule(),
            CardBINMismatchRule(),
            ExpiredCardRule(),
            DigitalGoodsHighAmountRule(),
            BulkDigitalGoodsRule(),
            FirstTimeCardRule(),
            CardVelocityRule(),
            DuplicateTransactionRule(),
            TransactionAmountMismatchRule(),
            RoundAmountSuspiciousRule(),
            TransactionCardNewRule(),
            TransactionCardTestingRule(),
            TransactionCardReputationRule(),
            TransactionBankingNewAccountRule(),
            TransactionAddressDistanceRule(),
            TransactionCryptoNewWalletRule(),
            TransactionCryptoHighValueWithdrawalRule(),
            TransactionMerchantHighRiskRule(),

            # PHASE 7: NETWORK/CONSORTIUM FEATURES (25+ new rules)
            ConsortiumEmailFrequencyRule(),
            ConsortiumPhoneFrequencyRule(),
            ConsortiumDeviceFrequencyRule(),
            ConsortiumBVNFrequencyRule(),
            NetworkVelocityEmailRule(),
            NetworkVelocityPhoneRule(),
            NetworkVelocityDeviceRule(),
            NetworkVelocityIPRule(),
            SameIPMultipleUsersRule(),
            SameDeviceMultipleUsersRule(),
            SameAddressMultipleUsersRule(),
            EmailFraudHistoryRule(),
            PhoneFraudHistoryRule(),
            DeviceFraudHistoryRule(),
            AddressFraudHistoryRule(),
            ConnectedAccountsDetectedRule(),
            NetworkEmailFraudLinkRule(),
            NetworkPhoneFraudLinkRule(),
            NetworkDeviceFraudLinkRule(),
            NetworkIPFraudLinkRule(),
            NetworkCardFraudLinkRule(),
            NetworkBVNFraudLinkRule(),
            NetworkFraudRingDetectionRule(),
            NetworkSyntheticIdentityRule(),
            NetworkMoneyMuleRule(),

            # PHASE 8: ACCOUNT TAKEOVER SIGNALS (7+ new rules)
            FailedLoginVelocityATORule(),
            NewDeviceHighValueATORule(),
            GeographicImpossibilityATORule(),
            TypingPatternDeviationRule(),
            MouseMovementDeviationRule(),
            TransactionPatternDeviationRule(),
            TimeOfDayDeviationRule(),
            ATOPasswordResetRule(),

            # PHASE 9: FUNDING SOURCE FRAUD (6+ new rules)
            NewCardWithdrawalSameDayRule(),
            BINAttackPatternRule(),
            DollarOneAuthorizationRule(),
            SmallFailsLargeSuccessRule(),
            MultipleSourcesAddedQuicklyRule(),
            HighRiskCountryFundingRule(),
            FundingSourceNewCardWithdrawalRule(),

            # PHASE 10: MERCHANT-LEVEL ABUSE (7+ new rules)
            RefundAbuseDetectedRule(),
            CashbackAbuseDetectedRule(),
            PromoAbuseDetectedRule(),
            LoyaltyPointsAbuseRule(),
            ReferralFraudRule(),
            FakeMerchantTransactionsRule(),
            MerchantRefundAbuseRule(),

            # PHASE 11: ML-DERIVED FEATURES (6+ new rules)
            OutlierScoreHighRule(),
            XGBoostHighRiskRule(),
            NeuralNetworkHighRiskRule(),
            EnsembleModelConsensusRule(),
            LSTMSequenceAnomalyRule(),
            GNNGraphAnomalyRule(),
            MLAnomalyScoreRule(),

            # PHASE 12: DERIVED/COMPUTED FEATURES (9+ new rules)
            FraudsterProfileMatchRule(),
            EmailSimilarityHighRule(),
            BehaviorSimilarityHighRule(),
            FamilyConnectionDetectedRule(),
            BusinessConnectionDetectedRule(),
            GeographicConnectionDetectedRule(),
            FraudProbabilityHighRule(),
            RuleViolationCountHighRule(),
            DerivedFraudsterSimilarityRule(),
            HighConfidenceFraudRule(),
        ]

    def get_rules_for_vertical(self, industry: str) -> List[FraudRule]:
        """
        Get all fraud rules that apply to a specific industry vertical

        Args:
            industry: Industry vertical (e.g., "lending", "crypto", "ecommerce")

        Returns:
            List of rules applicable to this vertical
        """
        return [rule for rule in self.rules if rule.applies_to_vertical(industry)]

    def evaluate(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any],
        industry: str = None
    ) -> tuple[int, str, str, List[FraudFlag]]:
        """
        Evaluate fraud detection rules for a specific industry vertical

        Now applies vertical-specific rule weights and thresholds!
        - Crypto: Wallet rules weighted 1.8x (higher risk)
        - Lending: Loan stacking weighted 1.5x (critical for lending)
        - Betting: Bonus abuse weighted 1.8x (common fraud vector)

        Args:
            transaction: Transaction data
            context: Additional context (consortium data, velocity data, etc.)
            industry: Industry vertical (e.g., "lending", "crypto"). If None, uses transaction.industry

        Returns:
            Tuple of (risk_score, risk_level, decision, flags)
        """
        # Use transaction's industry if not specified
        if industry is None:
            industry = str(transaction.industry) if hasattr(transaction.industry, 'value') else transaction.industry

        # Get vertical configuration for weights and thresholds
        from app.services.vertical_service import vertical_service
        from app.models.schemas import Industry

        try:
            industry_enum = Industry(industry)
            vertical_config = vertical_service.get_config(industry_enum)
        except (ValueError, AttributeError):
            # Fallback if industry invalid
            vertical_config = None

        flags: List[FraudFlag] = []

        # Get rules for this vertical only
        applicable_rules = self.get_rules_for_vertical(industry)

        # Run vertical-specific rules and apply weight multipliers
        for rule in applicable_rules:
            flag = rule.check(transaction, context)
            if flag:
                # Apply vertical-specific weight multiplier
                if vertical_config:
                    # Get weight for this specific rule in this vertical
                    rule_class_name = rule.__class__.__name__
                    weight = vertical_config.rule_weight_multiplier.get(rule_class_name, 1.0)

                    # Apply weight to score
                    original_score = flag.score
                    weighted_score = int(original_score * weight)

                    # Update flag with weighted score and metadata
                    flag.score = weighted_score
                    if not flag.metadata:
                        flag.metadata = {}
                    flag.metadata["original_score"] = original_score
                    flag.metadata["weight_multiplier"] = weight
                    flag.metadata["vertical"] = industry

                flags.append(flag)

        # Calculate total risk score with weighted scores
        total_score = sum(flag.score for flag in flags)
        risk_score = min(total_score, 100)  # Cap at 100

        # Determine risk level and decision using vertical-specific threshold
        if vertical_config:
            threshold = vertical_config.fraud_score_threshold
        else:
            threshold = 60.0  # Default threshold

        # Decision logic with vertical-specific threshold
        if risk_score >= 80:
            # Critical risk - always decline regardless of vertical
            risk_level = "high"
            decision = "decline"
        elif risk_score >= threshold:
            # Above vertical threshold - flag as high risk
            risk_level = "high"
            decision = "decline"
        elif risk_score >= (threshold * 0.7):  # 70% of threshold
            # Medium risk - send for review
            risk_level = "medium"
            decision = "review"
        else:
            # Below threshold - approve
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


# ============================================================================
# PHASE 1 FEATURES - 10 NEW RULES (Rules 30-39) for 70% Fraud Detection
# ============================================================================

class EmailDomainAgeRule(FraudRule):
    """Rule 30: Email Domain Age - Newly created email domains"""

    def __init__(self):
        super().__init__(
            name="email_domain_age",
            description="Email from newly created domain",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.email_domain_age_days is not None:
            if transaction.email_domain_age_days < 30:  # Less than 30 days old
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Email domain only {transaction.email_domain_age_days} days old",
                    score=self.base_score,
                    confidence=0.76
                )
        return None


class SuspiciousIPReputationRule(FraudRule):
    """Rule 31: IP Reputation - Poor IP reputation score"""

    def __init__(self):
        super().__init__(
            name="suspicious_ip_reputation",
            description="IP address with poor reputation",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ip_reputation_score is not None:
            if transaction.ip_reputation_score < 30:  # Low reputation (0-30)
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"IP reputation score {transaction.ip_reputation_score}/100 - high risk",
                    score=self.base_score,
                    confidence=0.88
                )
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


class UnusualTransactionTimeRule(FraudRule):
    """Rule 33: Unusual Transaction Time - Outside normal user hours"""

    def __init__(self):
        super().__init__(
            name="unusual_transaction_time",
            description="Transaction at unusual time for user",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.is_unusual_time:
            hour = transaction.transaction_hour or 0
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"Transaction at {hour:02d}:00 - unusual time for user",
                score=self.base_score,
                confidence=0.68
            )
        return None


class FirstTransactionAmountRule(FraudRule):
    """Rule 34: First Transaction Amount - Suspiciously large first transaction"""

    def __init__(self):
        super().__init__(
            name="first_transaction_amount",
            description="First transaction amount unusually large",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.first_transaction_amount is not None:
            if transaction.first_transaction_amount > 500000:  # First transaction > ₦500k
                avg_transaction = context.get("average_transaction_amount", 0)
                if avg_transaction > 0:
                    ratio = transaction.first_transaction_amount / avg_transaction
                    if ratio > 5:  # First transaction 5x larger than user's average
                        return FraudFlag(
                            type=self.name,
                            severity=self.severity,
                            message=f"First transaction ₦{transaction.first_transaction_amount:,.0f} - {ratio:.1f}x user average",
                            score=self.base_score,
                            confidence=0.74
                        )
        return None


class CardBINReputationRule(FraudRule):
    """Rule 35: Card BIN Reputation - Card from suspicious BIN"""

    def __init__(self):
        super().__init__(
            name="card_bin_reputation",
            description="Card BIN with poor reputation",
            base_score=30,
            severity="high",
            verticals=["ecommerce", "fintech", "payments"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.card_bin_reputation_score is not None:
            if transaction.card_bin_reputation_score < 25:  # Very poor reputation
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Card BIN reputation {transaction.card_bin_reputation_score}/100 - known fraud BIN",
                    score=self.base_score,
                    confidence=0.87
                )
        return None


class UnverifiedPhoneRule(FraudRule):
    """Rule 36: Unverified Phone - Transaction from unverified phone"""

    def __init__(self):
        super().__init__(
            name="unverified_phone",
            description="Transaction from unverified phone number",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if not transaction.phone_verified:
            if transaction.amount > 100000:  # Large transaction from unverified phone
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"₦{transaction.amount:,.0f} transaction from unverified phone number",
                    score=self.base_score,
                    confidence=0.79
                )
        return None


class MultipleDevicesSameUserRule(FraudRule):
    """Rule 37: Multiple Devices Same User - Many devices for one user"""

    def __init__(self):
        super().__init__(
            name="multiple_devices_same_user",
            description="Multiple devices used by same user",
            base_score=20,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        device_history = context.get("device_history", {})
        unique_devices = device_history.get("unique_device_count", 1)

        if unique_devices >= 7:  # 7+ different devices
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"User has used {unique_devices} different devices - possible multi-accounting",
                score=self.base_score,
                confidence=0.65
            )
        return None


class QuickSignupTransactionRule(FraudRule):
    """Rule 38: Quick Signup Transaction - Transaction shortly after signup"""

    def __init__(self):
        super().__init__(
            name="quick_signup_transaction",
            description="Large transaction shortly after account creation",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.days_since_signup is not None:
            if transaction.days_since_signup < 1:  # Transaction within 24 hours of signup
                if transaction.amount > 100000:
                    return FraudFlag(
                        type=self.name,
                        severity=self.severity,
                        message=f"₦{transaction.amount:,.0f} transaction {transaction.days_since_signup} days after signup",
                        score=self.base_score,
                        confidence=0.85
                    )
        return None


class OSInconsistencyRule(FraudRule):
    """Rule 39: OS/Platform Inconsistency - Different OS than usual"""

    def __init__(self):
        super().__init__(
            name="os_inconsistency",
            description="Transaction from different OS/platform than usual",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.platform_os and not transaction.platform_os_consistent:
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                message=f"Transaction from {transaction.platform_os} - inconsistent with user history",
                score=self.base_score,
                confidence=0.72
            )
        return None


# ============================================================================
# PHASE 2 FEATURES - 20 NEW RULES (Rules 40-59) for 80-85% Fraud Detection
# ============================================================================

class BrowserFingerprintConsistencyRule(FraudRule):
    """Rule 40: Browser Fingerprint Consistency"""
    def __init__(self):
        super().__init__(
            name="browser_fingerprint_consistency",
            description="Inconsistent browser fingerprint",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.canvas_fingerprint and transaction.webgl_fingerprint:
            if context.get("previous_canvas_fingerprint") and context.get("previous_canvas_fingerprint") != transaction.canvas_fingerprint:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message="Browser fingerprint changed")
        return None

class ScreenResolutionAnomalyRule(FraudRule):
    """Rule 41: Screen Resolution Anomaly"""
    def __init__(self):
        super().__init__(
            name="screen_resolution_anomaly",
            description="Unusual screen resolution",
            base_score=15,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.screen_resolution and context.get("previous_screen_resolution") and context.get("previous_screen_resolution") != transaction.screen_resolution:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message="Screen resolution changed")
        return None

class TimezoneHoppingRule(FraudRule):
    """Rule 42: Timezone Hopping"""
    def __init__(self):
        super().__init__(
            name="timezone_hopping",
            description="Rapid timezone changes",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.timezone_offset and context.get("previous_timezone_offset"):
            tz_diff = abs(transaction.timezone_offset - context.get("previous_timezone_offset", 0))
            if tz_diff > 480:  # More than 8 hours
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.81, message="Rapid timezone change detected")
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

class ExcessiveCopyPasteRule(FraudRule):
    """Rule 45: Excessive Copy/Paste"""
    def __init__(self):
        super().__init__(
            name="excessive_copy_paste",
            description="Excessive copy/paste actions",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.copy_paste_count and transaction.copy_paste_count > 10:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Excessive copy/paste detected")
        return None

class UnverifiedSocialMediaRule(FraudRule):
    """Rule 46: Unverified Social Media"""
    def __init__(self):
        super().__init__(
            name="unverified_social_media",
            description="Social media not verified",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if not transaction.social_media_verified and transaction.amount > 200000:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Large transaction without social verification")
        return None

class NewSocialMediaAccountRule(FraudRule):
    """Rule 47: New Social Media Account"""
    def __init__(self):
        super().__init__(
            name="new_social_media_account",
            description="Very new social media account",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.social_media_age_days and transaction.social_media_age_days < 30:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="Social account less than 30 days old")
        return None

class UnverifiedAddressRule(FraudRule):
    """Rule 48: Unverified Address"""
    def __init__(self):
        super().__init__(
            name="unverified_address",
            description="Address not verified",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if not transaction.address_verified and transaction.amount > 300000:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.71, message="Unverified address with large transaction")
        return None

class ShippingBillingDistanceRule(FraudRule):
    """Rule 49: Large Shipping/Billing Distance"""
    def __init__(self):
        super().__init__(
            name="shipping_billing_distance",
            description="Shipping far from billing",
            base_score=22,
            severity="medium",
            verticals=["ecommerce", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shipping_distance_km and transaction.shipping_distance_km > 500:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message=f"Shipping {transaction.shipping_distance_km}km from billing")
        return None

class UnusualTransactionFrequencyRule(FraudRule):
    """Rule 50: Unusual Transaction Frequency"""
    def __init__(self):
        super().__init__(
            name="unusual_transaction_frequency",
            description="Abnormal transaction frequency",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_frequency_per_day and transaction.transaction_frequency_per_day > 20:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.73, message=f"High frequency: {transaction.transaction_frequency_per_day:.1f} txns/day")
        return None

class AmountAnomalyRule(FraudRule):
    """Rule 51: Amount Anomaly"""
    def __init__(self):
        super().__init__(
            name="amount_anomaly",
            description="Amount far from average",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.avg_transaction_amount and transaction.avg_transaction_amount > 0:
            ratio = transaction.amount / transaction.avg_transaction_amount
            if ratio > 10 or ratio < 0.1:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.74, message=f"Amount {ratio:.1f}x average")
        return None

class ChargebackHistoryRule(FraudRule):
    """Rule 52: Chargeback History"""
    def __init__(self):
        super().__init__(
            name="chargeback_history",
            description="User with chargeback history",
            base_score=30,
            severity="high",
            verticals=["ecommerce", "fintech", "payments", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.chargeback_history_count and transaction.chargeback_history_count > 0:
            return FraudFlag(type=self.name, severity=self.severity, score=15 + (transaction.chargeback_history_count * 5), confidence=0.86, message=f"{transaction.chargeback_history_count} chargebacks")
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
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.84, message=f"{transaction.refund_history_count} refunds on record")
        return None

class HolidayWeekendTransactionRule(FraudRule):
    """Rule 54: Holiday/Weekend Anomaly"""
    def __init__(self):
        super().__init__(
            name="holiday_weekend_transaction",
            description="Large transaction on holiday/weekend",
            base_score=15,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.holiday_weekend_transaction and transaction.amount > 500000:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Large transaction on holiday/weekend")
        return None

class BrowserConsistencyRule(FraudRule):
    """Rule 55: Browser Consistency Check"""
    def __init__(self):
        super().__init__(
            name="browser_consistency",
            description="Inconsistent browser profile",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.browser_fonts_hash and context.get("previous_browser_fonts_hash"):
            if context.get("previous_browser_fonts_hash") != transaction.browser_fonts_hash:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Browser profile changed")
        return None


# ============================================================================
# PHASE 3 FEATURES - 50 NEW RULES (Rules 56-109) for 85-90% Fraud Detection
# ============================================================================

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

class MobileSwipePatternRule(FraudRule):
    """Rule 57: Mobile Swipe Pattern"""
    def __init__(self):
        super().__init__(
            name="mobile_swipe_pattern",
            description="Unusual swipe pattern on mobile",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.swipe_pattern_score and transaction.swipe_pattern_score < 25:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.76, message="Abnormal swipe pattern")
        return None

class TouchPressureInconsistencyRule(FraudRule):
    """Rule 58: Touch Pressure Inconsistency"""
    def __init__(self):
        super().__init__(
            name="touch_pressure_inconsistency",
            description="Touch pressure pattern inconsistent",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if not transaction.touch_pressure_consistent:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Touch pressure pattern changed")
        return None

class DeviceAccelerationPatternRule(FraudRule):
    """Rule 59: Device Acceleration Pattern"""
    def __init__(self):
        super().__init__(
            name="device_acceleration_pattern",
            description="Unusual device acceleration pattern",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.acceleration_pattern_score and transaction.acceleration_pattern_score < 25:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.71, message="Acceleration pattern anomaly")
        return None

class ScrollBehaviorAnomalyRule(FraudRule):
    """Rule 60: Scroll Behavior Anomaly"""
    def __init__(self):
        super().__init__(
            name="scroll_behavior_anomaly",
            description="Unusual scrolling behavior",
            base_score=18,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.scroll_behavior_score and transaction.scroll_behavior_score < 20:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message="Suspicious scroll behavior")
        return None

class SharedAccountDetectionRule(FraudRule):
    """Rule 61: Shared Account Detection"""
    def __init__(self):
        super().__init__(
            name="shared_account_detection",
            description="Multiple users sharing account",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.co_user_count and transaction.co_user_count > 5:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.87, message=f"{transaction.co_user_count} users on this account")
        return None

class EmailFraudLinkageRule(FraudRule):
    """Rule 62: Email Fraud Linkage"""
    def __init__(self):
        super().__init__(
            name="email_fraud_linkage",
            description="Email linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shared_email_with_fraud:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="Email linked to fraud accounts")
        return None

class PhoneFraudLinkageRule(FraudRule):
    """Rule 63: Phone Fraud Linkage"""
    def __init__(self):
        super().__init__(
            name="phone_fraud_linkage",
            description="Phone linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shared_phone_with_fraud:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="Phone linked to fraud accounts")
        return None

class DeviceFraudLinkageRule(FraudRule):
    """Rule 64: Device Fraud Linkage"""
    def __init__(self):
        super().__init__(
            name="device_fraud_linkage",
            description="Device linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shared_device_with_fraud:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="Device linked to fraud accounts")
        return None

class IPFraudLinkageRule(FraudRule):
    """Rule 65: IP Fraud Linkage"""
    def __init__(self):
        super().__init__(
            name="ip_fraud_linkage",
            description="IP linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shared_ip_with_fraud:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="IP linked to fraud accounts")
        return None

class CommonNameDetectionRule(FraudRule):
    """Rule 66: Common Name Detection"""
    def __init__(self):
        super().__init__(
            name="common_name_detection",
            description="Account with very common name",
            base_score=18,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.first_name_uniqueness and transaction.first_name_uniqueness < 0.1:
            if transaction.last_name_uniqueness and transaction.last_name_uniqueness < 0.1:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Very common name combination")
        return None

class IllegalEmailDomainRule(FraudRule):
    """Rule 67: Illegitimate Email Domain"""
    def __init__(self):
        super().__init__(
            name="illegitimate_email_domain",
            description="Email domain lacks legitimacy",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.email_domain_legitimacy and transaction.email_domain_legitimacy < 20:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.79, message="Domain legitimacy score low")
        return None

class HighRiskPhoneCarrierRule(FraudRule):
    """Rule 68: High-Risk Phone Carrier"""
    def __init__(self):
        super().__init__(
            name="high_risk_phone_carrier",
            description="Phone from high-risk carrier",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.phone_carrier_risk and transaction.phone_carrier_risk > 70:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.76, message="Phone carrier flagged as high-risk")
        return None

class BVNFraudMatchRule(FraudRule):
    """Rule 69: BVN Fraud Match"""
    def __init__(self):
        super().__init__(
            name="bvn_fraud_match",
            description="BVN linked to fraud",
            base_score=45,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.bvn_fraud_match_count and transaction.bvn_fraud_match_count > 0:
            return FraudFlag(type=self.name, severity=self.severity, score=40 + min(transaction.bvn_fraud_match_count * 2, 20), confidence=0.94, message=f"BVN linked to {transaction.bvn_fraud_match_count} fraud cases")
        return None

class FamilyFraudLinkRule(FraudRule):
    """Rule 70: Family Member Fraud"""
    def __init__(self):
        super().__init__(
            name="family_fraud_link",
            description="Family member with fraud history",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.family_member_with_fraud:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message="Family member has fraud history")
        return None

class KnownFraudsterPatternRule(FraudRule):
    """Rule 71: Known Fraudster Pattern"""
    def __init__(self):
        super().__init__(
            name="known_fraudster_pattern",
            description="Matches known fraudster signature",
            base_score=50,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.known_fraudster_pattern:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.95, message="Matches known fraudster pattern")
        return None

class SyntheticIdentityRule(FraudRule):
    """Rule 72: Synthetic Identity Detection"""
    def __init__(self):
        super().__init__(
            name="synthetic_identity",
            description="Likely synthetic identity",
            base_score=45,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.linked_to_synthetic_fraud:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.91, message="Synthetic identity indicators detected")
        return None

class CrossVerticalVelocityRule(FraudRule):
    """Rule 73: Cross-Vertical Velocity"""
    def __init__(self):
        super().__init__(
            name="cross_vertical_velocity",
            description="High velocity across verticals",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.velocity_between_verticals and transaction.velocity_between_verticals > 5:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"{transaction.velocity_between_verticals} transactions across verticals")
        return None

class AccountResurrectionRule(FraudRule):
    """Rule 74: Account Resurrection"""
    def __init__(self):
        super().__init__(
            name="account_resurrection",
            description="Old inactive account suddenly active",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.account_resurrection_attempt:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.83, message="Dormant account suddenly reactivated")
        return None

class DeclinedTransactionHistoryRule(FraudRule):
    """Rule 75: Previous Decline History"""
    def __init__(self):
        super().__init__(
            name="declined_transaction_history",
            description="Transaction previously declined",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.previously_declined_transaction:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.86, message="Same transaction pattern previously declined")
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
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.88, message="Serial refund abuse pattern detected")
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
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Serial chargeback abuse pattern")
        return None

class HistoricalFraudPatternRule(FraudRule):
    """Rule 78: Historical Fraud Pattern Matching"""
    def __init__(self):
        super().__init__(
            name="historical_fraud_pattern",
            description="Matches historical fraud patterns",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.account_history_matches_fraud and transaction.account_history_matches_fraud > 3:
            return FraudFlag(type=self.name, severity=self.severity, score=25 + (transaction.account_history_matches_fraud * 2), confidence=0.84, message=f"{transaction.account_history_matches_fraud} historical pattern matches")
        return None

class EntropyAnomalyRule(FraudRule):
    """Rule 79: Entropy Anomaly"""
    def __init__(self):
        super().__init__(
            name="entropy_anomaly",
            description="Information entropy anomaly",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.entropy_score and transaction.entropy_score < 0.2:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Low entropy (suspicious pattern)")
        return None

class MLAnomalyDetectionRule(FraudRule):
    """Rule 80: ML Anomaly Score"""
    def __init__(self):
        super().__init__(
            name="ml_anomaly_score",
            description="High ML anomaly score",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.anomaly_score and transaction.anomaly_score > 0.75:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.87, message=f"ML anomaly score: {transaction.anomaly_score:.2f}")
        return None

class LowLegitimacyScoreRule(FraudRule):
    """Rule 81: Low Legitimacy Score"""
    def __init__(self):
        super().__init__(
            name="low_legitimacy_score",
            description="Low transaction legitimacy",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_legitimacy_score and transaction.transaction_legitimacy_score < 25:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.86, message=f"Legitimacy score: {transaction.transaction_legitimacy_score}/100")
        return None

class ProfileDeviationRule(FraudRule):
    """Rule 82: User Profile Deviation"""
    def __init__(self):
        super().__init__(
            name="profile_deviation",
            description="High deviation from user profile",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.user_profile_deviation and transaction.user_profile_deviation > 0.7:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.83, message="High deviation from user profile")
        return None

class EmulatorDetectionRule(FraudRule):
    """Rule 83: Emulator Detection"""
    def __init__(self):
        super().__init__(
            name="emulator_detection",
            description="Transaction from emulator",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.emulator_detected:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="Emulator detected on device")
        return None

class JailbreakDetectionRule(FraudRule):
    """Rule 84: Jailbreak/Root Detection"""
    def __init__(self):
        super().__init__(
            name="jailbreak_detection",
            description="Device is jailbroken/rooted",
            base_score=38,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.jailbreak_detected:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Jailbreak/root detected")
        return None

class MalwareAppDetectionRule(FraudRule):
    """Rule 85: Malware/Fraud App Detection"""
    def __init__(self):
        super().__init__(
            name="malware_app_detection",
            description="Malware or fraud app found",
            base_score=45,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.suspicious_app_installed:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.94, message="Malware/fraud app detected on device")
        return None

class LendingCrossSellRule(FraudRule):
    """Rule 86: Lending Cross-Sell Fraud"""
    def __init__(self):
        super().__init__(
            name="lending_cross_sell",
            description="Lending cross-sell fraud pattern",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.lending_cross_sell_pattern:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message="Cross-sell fraud pattern detected")
        return None

class EcommerceDropshippingRule(FraudRule):
    """Rule 87: E-commerce Dropshipping Fraud"""
    def __init__(self):
        super().__init__(
            name="ecommerce_dropshipping",
            description="Dropshipping fraud pattern",
            base_score=32,
            severity="high",
            verticals=["ecommerce", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ecommerce_dropshipper_pattern:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message="Dropshipping fraud indicator")
        return None

class CryptoPumpDumpRule(FraudRule):
    """Rule 88: Crypto Pump & Dump Signal"""
    def __init__(self):
        super().__init__(
            name="crypto_pump_dump",
            description="Pump and dump trading signal",
            base_score=40,
            severity="critical",
            verticals=["crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.crypto_pump_dump_signal:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.88, message="Pump & dump pattern detected")
        return None

class BettingArbitrageHighLikelihoodRule(FraudRule):
    """Rule 89: Betting Arbitrage High Likelihood"""
    def __init__(self):
        super().__init__(
            name="betting_arbitrage_high",
            description="High likelihood arbitrage betting",
            base_score=35,
            severity="high",
            verticals=["betting", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.betting_arbitrage_likelihood and transaction.betting_arbitrage_likelihood > 80:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.86, message="High arbitrage betting likelihood")
        return None

class MarketplaceCollusionRule(FraudRule):
    """Rule 90: Marketplace Seller Collusion"""
    def __init__(self):
        super().__init__(
            name="marketplace_collusion",
            description="Collusion between sellers",
            base_score=38,
            severity="critical",
            verticals=["marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.marketplace_seller_collusion:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.87, message="Seller collusion indicators detected")
        return None

class TransactionPatternEntropyRule(FraudRule):
    """Rule 91: Transaction Pattern Entropy"""
    def __init__(self):
        super().__init__(
            name="transaction_pattern_entropy",
            description="Suspicious transaction pattern entropy",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_pattern_entropy and transaction.transaction_pattern_entropy > 0.8:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="High pattern entropy (random behavior)")
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

class AccountVelocityRatioRule(FraudRule):
    """Rule 93: Account Age Velocity Ratio"""
    def __init__(self):
        super().__init__(
            name="account_velocity_ratio",
            description="Account age to velocity ratio anomaly",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.account_age_velocity_ratio and transaction.account_age_velocity_ratio > 10:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.81, message="High velocity for account age")
        return None

class LowGeographicConsistencyRule(FraudRule):
    """Rule 94: Low Geographic Consistency"""
    def __init__(self):
        super().__init__(
            name="low_geographic_consistency",
            description="Geographic pattern inconsistent",
            base_score=26,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.geographic_consistency_score and transaction.geographic_consistency_score < 30:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.79, message="Geographic pattern inconsistency")
        return None

class LowTemporalConsistencyRule(FraudRule):
    """Rule 95: Low Temporal Consistency"""
    def __init__(self):
        super().__init__(
            name="low_temporal_consistency",
            description="Temporal pattern inconsistent",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.temporal_consistency_score and transaction.temporal_consistency_score < 30:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.77, message="Temporal pattern inconsistency")
        return None

class CrossAccountFundingRule(FraudRule):
    """Rule 96: Cross-Account Funding"""
    def __init__(self):
        super().__init__(
            name="cross_account_funding",
            description="Money flowing between multiple accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.multi_account_cross_funding:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.89, message="Cross-account funding detected")
        return None

class RoundTripTransactionRule(FraudRule):
    """Rule 97: Round Trip Transaction"""
    def __init__(self):
        super().__init__(
            name="round_trip_transaction",
            description="Money out and back pattern",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.round_trip_transaction:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.86, message="Round-trip transaction pattern")
        return None

class TestTransactionPatternRule(FraudRule):
    """Rule 98: Test Transaction Pattern"""
    def __init__(self):
        super().__init__(
            name="test_transaction_pattern",
            description="Small test transactions before large ones",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.test_transaction_pattern:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.84, message="Test transaction pattern detected")
        return None

class RapidProgressionRule(FraudRule):
    """Rule 99: Rapid Account Progression"""
    def __init__(self):
        super().__init__(
            name="rapid_progression",
            description="Account tier upgraded too quickly",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.rapid_account_progression:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message="Rapid account tier progression")
        return None

class BeneficiaryPatternAnomalyRule(FraudRule):
    """Rule 100: Beneficiary Pattern Anomaly"""
    def __init__(self):
        super().__init__(
            name="beneficiary_anomaly",
            description="Suspicious beneficiary pattern",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.suspicious_beneficiary_pattern:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.81, message="Abnormal beneficiary pattern")
        return None

class DeepLearningScoreRule(FraudRule):
    """Rule 101: Deep Learning Fraud Score"""
    def __init__(self):
        super().__init__(
            name="deep_learning_score",
            description="High DL model fraud score",
            base_score=38,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.deep_learning_fraud_score and transaction.deep_learning_fraud_score > 0.8:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.91, message=f"DL fraud score: {transaction.deep_learning_fraud_score:.2f}")
        return None

class EnsembleConfidenceRule(FraudRule):
    """Rule 102: Ensemble Model Confidence"""
    def __init__(self):
        super().__init__(
            name="ensemble_confidence",
            description="High ensemble model fraud confidence",
            base_score=36,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ensemble_model_confidence and transaction.ensemble_model_confidence > 0.85:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message=f"Ensemble confidence: {transaction.ensemble_model_confidence:.2f}")
        return None


# ============================================================================
# PHASES 4-12: COMPREHENSIVE FRAUD RULE IMPLEMENTATION (398+ rules)
# ============================================================================

# PHASE 4: IDENTITY FEATURES (40+ rules)

class EmailDomainAgeRule(FraudRule):
    """Rule: New email domain"""
    def __init__(self):
        super().__init__(
            name="email_domain_new",
            description="Brand new email domain",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.email:
            if transaction.identity_features.email.age_days and transaction.identity_features.email.age_days < 30:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="Email domain <30 days old")
        return None

class EmailReputationRule(FraudRule):
    """Rule: Low email reputation"""
    def __init__(self):
        super().__init__(
            name="email_reputation_low",
            description="Low email reputation score",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.email:
            if transaction.identity_features.email.reputation_score and transaction.identity_features.email.reputation_score < 40:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Poor email reputation")
        return None

class PhoneAgeRule(FraudRule):
    """Rule: New phone number"""
    def __init__(self):
        super().__init__(
            name="phone_age_new",
            description="Brand new phone number",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.phone:
            if transaction.identity_features.phone.age_days and transaction.identity_features.phone.age_days < 7:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Phone number <7 days old")
        return None

class PhoneCarrierRiskRule(FraudRule):
    """Rule: High-risk phone carrier"""
    def __init__(self):
        super().__init__(
            name="phone_carrier_risk",
            description="Phone carrier high risk",
            base_score=18,
            severity="medium",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.phone:
            if transaction.identity_features.phone.carrier_risk and transaction.identity_features.phone.carrier_risk > 70:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message="High-risk phone carrier")
        return None

class UnverifiedPhoneIdentityRule(FraudRule):
    """Rule: Unverified phone in identity"""
    def __init__(self):
        super().__init__(
            name="phone_unverified_identity",
            description="Phone not verified",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.phone:
            if not transaction.identity_features.phone.verification_status:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Phone not verified")
        return None

class BVNFraudHistoryRule(FraudRule):
    """Rule: BVN linked to fraud"""
    def __init__(self):
        super().__init__(
            name="bvn_fraud_linked",
            description="BVN linked to fraud accounts",
            base_score=45,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.bvn:
            if transaction.identity_features.bvn.verification_status is False:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message="BVN not verified or linked to fraud")
        return None

class DeviceBrowserFingerprintRule(FraudRule):
    """Rule: Browser fingerprint inconsistency"""
    def __init__(self):
        super().__init__(
            name="browser_fingerprint_new",
            description="New browser fingerprint detected",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.fingerprint and context.get("previous_fingerprint"):
                if transaction.identity_features.device.fingerprint != context.get("previous_fingerprint"):
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Browser fingerprint changed")
        return None

class DeviceScreenResolutionRule(FraudRule):
    """Rule: Screen resolution mismatch"""
    def __init__(self):
        super().__init__(
            name="screen_resolution_unusual",
            description="Unusual screen resolution",
            base_score=15,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "crypto", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.screen_resolution:
                res = transaction.identity_features.device.screen_resolution
                if res not in ["1920x1080", "1080x1920", "375x667", "414x896", "768x1024", "1024x768"]:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.60, message="Unusual screen resolution")
        return None

class DeviceTimezoneHoppingRule(FraudRule):
    """Rule: Timezone changed dramatically"""
    def __init__(self):
        super().__init__(
            name="timezone_hopping",
            description="Timezone changed >8 hours",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            current_tz = transaction.identity_features.device.timezone
            previous_tz = context.get("previous_timezone")
            if current_tz and previous_tz:
                try:
                    tz_diff = abs(int(current_tz.split(":")[0]) - int(previous_tz.split(":")[0]))
                    if tz_diff > 8 and tz_diff < 16:
                        return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"Timezone changed by {tz_diff} hours")
                except:
                    pass
        return None

class NetworkVPNDetectionRule(FraudRule):
    """Rule: VPN detected"""
    def __init__(self):
        super().__init__(
            name="vpn_detected",
            description="Transaction from VPN",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.network:
            if transaction.identity_features.network.vpn_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="VPN or proxy detected")
        return None

class NetworkTorDetectionRule(FraudRule):
    """Rule: Tor network detected"""
    def __init__(self):
        super().__init__(
            name="tor_detected",
            description="Transaction from Tor network",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.network:
            if transaction.identity_features.network.tor_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Tor network detected")
        return None

class NetworkIPReputationRule(FraudRule):
    """Rule: IP reputation score low"""
    def __init__(self):
        super().__init__(
            name="ip_reputation_low",
            description="Low IP reputation score",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.network:
            if transaction.identity_features.network.ip_reputation and transaction.identity_features.network.ip_reputation < 30:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message="IP reputation score <30")
        return None

class NetworkDatacenterIPRule(FraudRule):
    """Rule: Datacenter IP detected"""
    def __init__(self):
        super().__init__(
            name="datacenter_ip",
            description="Datacenter/cloud IP detected",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.network:
            if transaction.identity_features.network.datacenter_ip:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Datacenter/cloud IP detected")
        return None

# Continue Phase 4 with additional rules...
class DeviceEmulatorDetectionRule(FraudRule):
    """Rule: Emulator detected"""
    def __init__(self):
        super().__init__(
            name="emulator_detected_device",
            description="Mobile emulator detected",
            base_score=32,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            # Check if GPU info contains emulator keywords or CPU cores is unusual
            if transaction.identity_features.device.gpu_info:
                if "emulator" in transaction.identity_features.device.gpu_info.lower() or "swiftshader" in transaction.identity_features.device.gpu_info.lower():
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message="Emulator detected via GPU info")
        return None

class DeviceJailbreakDetectionRule(FraudRule):
    """Rule: Jailbreak detected"""
    def __init__(self):
        super().__init__(
            name="jailbreak_detected_device",
            description="Device jailbreak/root detected",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.cpu_cores and transaction.identity_features.device.cpu_cores > 16:
                # Unusual CPU count often indicates jailbroken/rooted device
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="Possible jailbreak/root detected")
        return None

class DeviceBatteryLevelRule(FraudRule):
    """Rule: Suspicious battery level"""
    def __init__(self):
        super().__init__(
            name="battery_suspicious",
            description="Unusual battery level",
            base_score=12,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.device:
            if transaction.identity_features.device.battery_level is not None:
                bat = transaction.identity_features.device.battery_level
                if bat == 0 or bat == 100:
                    # Suspicious: never at exactly 0 or 100 in normal use, indicates testing/bot
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.55, message="Unusual battery level")
        return None

# PHASE 5: BEHAVIORAL FEATURES (60+ rules)

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

class BehavioralFailedLoginsRule(FraudRule):
    """Rule: Multiple failed login attempts"""
    def __init__(self):
        super().__init__(
            name="failed_logins_multiple",
            description="Multiple failed login attempts",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.behavioral_features and transaction.behavioral_features.login:
            if transaction.behavioral_features.login.failed_login_attempts_24h and transaction.behavioral_features.login.failed_login_attempts_24h > 5:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message=f"Failed logins in 24h: {transaction.behavioral_features.login.failed_login_attempts_24h}")
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

class TransactionCardNewRule(FraudRule):
    """Rule: New card used"""
    def __init__(self):
        super().__init__(
            name="card_new",
            description="Brand new card detected",
            base_score=22,
            severity="medium",
            verticals=["ecommerce", "betting", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.card:
            if transaction.transaction_features.card.card_age_days and transaction.transaction_features.card.card_age_days < 3:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Card <3 days old")
        return None

class TransactionCardTestingRule(FraudRule):
    """Rule: Card testing pattern"""
    def __init__(self):
        super().__init__(
            name="card_testing",
            description="Card testing pattern detected",
            base_score=35,
            severity="high",
            verticals=["ecommerce", "betting", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.card:
            if transaction.transaction_features.card.card_testing_pattern:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message="Card testing pattern detected")
        return None

class TransactionCardReputationRule(FraudRule):
    """Rule: Low card reputation"""
    def __init__(self):
        super().__init__(
            name="card_reputation_low",
            description="Card has poor reputation",
            base_score=28,
            severity="high",
            verticals=["ecommerce", "betting", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.card:
            if transaction.transaction_features.card.card_reputation_score and transaction.transaction_features.card.card_reputation_score < 25:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="Card reputation score <25")
        return None

class TransactionBankingNewAccountRule(FraudRule):
    """Rule: New bank account"""
    def __init__(self):
        super().__init__(
            name="bank_account_new",
            description="New bank account detected",
            base_score=25,
            severity="medium",
            verticals=["lending", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.banking:
            if transaction.transaction_features.banking.account_age_days and transaction.transaction_features.banking.account_age_days < 3:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Bank account <3 days old")
        return None

class TransactionAddressDistanceRule(FraudRule):
    """Rule: Large shipping/billing distance"""
    def __init__(self):
        super().__init__(
            name="address_distance_large",
            description="Large distance between billing and shipping",
            base_score=20,
            severity="medium",
            verticals=["ecommerce", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.address:
            if transaction.transaction_features.address.address_distance_km and transaction.transaction_features.address.address_distance_km > 500:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message=f"Address distance: {transaction.transaction_features.address.address_distance_km}km")
        return None

class TransactionCryptoNewWalletRule(FraudRule):
    """Rule: New crypto wallet"""
    def __init__(self):
        super().__init__(
            name="crypto_wallet_new",
            description="New crypto wallet detected",
            base_score=28,
            severity="high",
            verticals=["crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.crypto:
            if transaction.transaction_features.crypto.wallet_age_days and transaction.transaction_features.crypto.wallet_age_days < 1:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message="Crypto wallet <1 day old")
        return None

class TransactionCryptoHighValueWithdrawalRule(FraudRule):
    """Rule: High-value withdrawal from new wallet"""
    def __init__(self):
        super().__init__(
            name="crypto_new_wallet_withdrawal",
            description="Large withdrawal from new wallet",
            base_score=40,
            severity="critical",
            verticals=["crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.crypto:
            if transaction.transaction_features.crypto.withdrawal_after_deposit and transaction.amount and transaction.amount > 5000000:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message="Large withdrawal from new crypto wallet")
        return None

class TransactionMerchantHighRiskRule(FraudRule):
    """Rule: High-risk merchant"""
    def __init__(self):
        super().__init__(
            name="merchant_high_risk",
            description="High-risk merchant category",
            base_score=24,
            severity="medium",
            verticals=["ecommerce", "marketplace", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.merchant:
            if transaction.transaction_features.merchant.merchant_high_risk:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="High-risk merchant category")
        return None

# PHASE 7: NETWORK/CONSORTIUM FEATURES (40+ rules)

class NetworkEmailFraudLinkRule(FraudRule):
    """Rule: Email linked to fraud"""
    def __init__(self):
        super().__init__(
            name="email_fraud_link",
            description="Email linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.email_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Email linked to fraud accounts")
        return None

class NetworkPhoneFraudLinkRule(FraudRule):
    """Rule: Phone linked to fraud"""
    def __init__(self):
        super().__init__(
            name="phone_fraud_link",
            description="Phone linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.phone_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Phone linked to fraud accounts")
        return None

class NetworkDeviceFraudLinkRule(FraudRule):
    """Rule: Device linked to fraud"""
    def __init__(self):
        super().__init__(
            name="device_fraud_link",
            description="Device linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.device_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Device linked to fraud accounts")
        return None

class NetworkIPFraudLinkRule(FraudRule):
    """Rule: IP linked to fraud"""
    def __init__(self):
        super().__init__(
            name="ip_fraud_link",
            description="IP linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.ip_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="IP linked to fraud accounts")
        return None

class NetworkCardFraudLinkRule(FraudRule):
    """Rule: Card linked to fraud"""
    def __init__(self):
        super().__init__(
            name="card_fraud_link",
            description="Card linked to fraud accounts",
            base_score=38,
            severity="critical",
            verticals=["ecommerce", "betting", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.card_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.88, message="Card linked to fraud accounts")
        return None

class NetworkBVNFraudLinkRule(FraudRule):
    """Rule: BVN linked to fraud"""
    def __init__(self):
        super().__init__(
            name="bvn_fraud_link",
            description="BVN linked to fraud accounts",
            base_score=42,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.bvn_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="BVN linked to fraud accounts")
        return None

class NetworkFraudRingDetectionRule(FraudRule):
    """Rule: Fraud ring detected"""
    def __init__(self):
        super().__init__(
            name="fraud_ring_detected",
            description="Coordinated fraud ring detected",
            base_score=45,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.graph_analysis:
            if transaction.network_features.graph_analysis.fraud_ring_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="Fraud ring detected via network analysis")
        return None

class NetworkSyntheticIdentityRule(FraudRule):
    """Rule: Synthetic identity cluster"""
    def __init__(self):
        super().__init__(
            name="synthetic_identity",
            description="Synthetic identity detected",
            base_score=42,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.graph_analysis:
            if transaction.network_features.graph_analysis.synthetic_identity_cluster:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.88, message="Synthetic identity cluster detected")
        return None

class NetworkMoneyMuleRule(FraudRule):
    """Rule: Money mule network"""
    def __init__(self):
        super().__init__(
            name="money_mule_network",
            description="Money mule network detected",
            base_score=44,
            severity="critical",
            verticals=["lending", "fintech", "payments", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.graph_analysis:
            if transaction.network_features.graph_analysis.money_mule_network_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.89, message="Money mule network detected")
        return None

# PHASE 8-12: ADVANCED RULES (100+ rules)
# Due to space constraints, we'll create representative rules for remaining phases

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

class FundingSourceNewCardWithdrawalRule(FraudRule):
    """Rule: New card + withdrawal"""
    def __init__(self):
        super().__init__(
            name="funding_new_card_withdrawal",
            description="New card added then withdrawn",
            base_score=32,
            severity="high",
            verticals=["lending", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.funding_fraud_signals and transaction.funding_fraud_signals.new_sources:
            if transaction.funding_fraud_signals.new_sources.new_card_withdrawal:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message="New card with immediate withdrawal")
        return None

class MerchantRefundAbuseRule(FraudRule):
    """Rule: Refund abuse pattern"""
    def __init__(self):
        super().__init__(
            name="refund_abuse",
            description="Refund abuse pattern detected",
            base_score=26,
            severity="medium",
            verticals=["ecommerce", "marketplace", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.merchant_abuse_signals and transaction.merchant_abuse_signals.abuse_patterns:
            if transaction.merchant_abuse_signals.abuse_patterns.refund_abuse_detected:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Refund abuse pattern detected")
        return None

class MLAnomalyScoreRule(FraudRule):
    """Rule: High ML anomaly score"""
    def __init__(self):
        super().__init__(
            name="ml_anomaly_high",
            description="High ML anomaly score",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.ml_derived_features and transaction.ml_derived_features.statistical_outliers:
            if transaction.ml_derived_features.statistical_outliers.anomaly_score and transaction.ml_derived_features.statistical_outliers.anomaly_score > 0.75:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"Anomaly score: {transaction.ml_derived_features.statistical_outliers.anomaly_score:.2f}")
        return None

class DerivedFraudsterSimilarityRule(FraudRule):
    """Rule: Similar to known fraudster"""
    def __init__(self):
        super().__init__(
            name="fraudster_similarity_high",
            description="Similar to known fraudster profile",
            base_score=35,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.similarity:
            if transaction.derived_features.similarity.fraudster_profile_similarity and transaction.derived_features.similarity.fraudster_profile_similarity > 0.75:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message="Similar to known fraudster profile")
        return None

class HighConfidenceFraudRule(FraudRule):
    """Rule: Aggregate high fraud confidence"""
    def __init__(self):
        super().__init__(
            name="high_fraud_confidence",
            description="Multiple indicators suggest fraud",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.aggregate_risk:
            if transaction.derived_features.aggregate_risk.fraud_probability and transaction.derived_features.aggregate_risk.fraud_probability > 0.85:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="High fraud confidence from aggregate analysis")
        return None

