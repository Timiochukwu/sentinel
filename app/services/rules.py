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
