"""
Network and IP-based fraud detection rules

This module contains fraud detection rules related to network analysis,
IP reputation, VPN/proxy detection, geographic inconsistencies, and
consortium network fraud patterns.

Rules for:
- IP reputation and geolocation
- VPN/Tor/proxy detection
- Network velocity and abuse
- Geographic impossibilities
- Consortium network fraud linkage
"""

from typing import Optional, Dict, Any
from app.schemas import TransactionCheckRequest, FraudFlag
from .base import FraudRule


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

# Export all network rules
NETWORK_RULES = [
    LoanStackingRule(),
    VPNProxyRule(),
    MultipleFailedPaymentsRule(),
    ShippingMismatchRule(),
    IPLocationConsistencyRule(),
    ISPReputationRule(),
    ASNBlacklistRule(),
    TimezoneOffsetAnomalyRule(),
    ScreenResolutionHistoryRule(),
    TwoFactorBypassRule(),
    CardTestingPatternRule(),
    AddressDistanceAnomalyRule(),
    CardVelocityRule(),
    NetworkVelocityIPRule(),
    SameIPMultipleUsersRule(),
    SameAddressMultipleUsersRule(),
    AddressFraudHistoryRule(),
    FailedLoginVelocityATORule(),
    GeographicImpossibilityATORule(),
    DollarOneAuthorizationRule(),
    MultipleSourcesAddedQuicklyRule(),
    SuspiciousIPReputationRule(),
    ShippingBillingDistanceRule(),
    ChargebackHistoryRule(),
    MobileSwipePatternRule(),
    SharedAccountDetectionRule(),
    IPFraudLinkageRule(),
    FamilyFraudLinkRule(),
    DeclinedTransactionHistoryRule(),
    HistoricalFraudPatternRule(),
    EcommerceDropshippingRule(),
    CrossAccountFundingRule(),
    RoundTripTransactionRule(),
    NetworkVPNDetectionRule(),
    NetworkTorDetectionRule(),
    NetworkIPReputationRule(),
    NetworkDatacenterIPRule(),
    BehavioralFailedLoginsRule(),
    TransactionAddressDistanceRule(),
    NetworkIPFraudLinkRule(),
    HighConfidenceFraudRule(),
]
