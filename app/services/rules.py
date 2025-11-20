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
    """Rule 10: Impossible Travel - Lagos to Kano in 2 hours"""

    def __init__(self):
        super().__init__(
            name="impossible_travel",
            description="Geographically impossible travel speed",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
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
            EmailDomainAgeRule(),              # Rule 30
            SuspiciousIPReputationRule(),      # Rule 31
            ExcessiveFailedLoginsRule(),       # Rule 32
            UnusualTransactionTimeRule(),      # Rule 33
            FirstTransactionAmountRule(),      # Rule 34
            CardBINReputationRule(),           # Rule 35
            UnverifiedPhoneRule(),             # Rule 36
            MultipleDevicesSameUserRule(),     # Rule 37
            QuickSignupTransactionRule(),      # Rule 38
            OSInconsistencyRule(),             # Rule 39
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

        flags: List[FraudFlag] = []

        # Get rules for this vertical only
        applicable_rules = self.get_rules_for_vertical(industry)

        # Run vertical-specific rules
        for rule in applicable_rules:
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
