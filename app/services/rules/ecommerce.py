"""
E-commerce-specific fraud detection rules

This module contains fraud detection rules specific to e-commerce transactions,
including card fraud, shipping/billing mismatches, digital goods, and merchant abuse.

Rules for:
- Online retail
- Shopping platforms
- Digital marketplaces
- Subscription services
"""

from typing import Optional, Dict, Any
from app.schemas import TransactionCheckRequest, FraudFlag
from .base import FraudRule


class CardBINFraudRule(FraudRule):
    """Rule 16: Card BIN Fraud - High-risk card BINs"""

    def __init__(self):
        super().__init__(
            name="card_bin_fraud",
            description="Card from high-risk BIN",
            base_score=35,
            severity="high",
            verticals=["ecommerce", "fintech", "payments"]
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


class ShippingMismatchRule(FraudRule):
    """Rule 18: Shipping/Billing Mismatch - Different addresses"""

    def __init__(self):
        super().__init__(
            name="shipping_mismatch",
            description="Shipping and billing addresses don't match",
            base_score=25,
            severity="medium",
            verticals=["ecommerce"]
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
            verticals=["ecommerce"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.product_type in ["digital_goods", "gift_card", "gaming_credits"]:
            if transaction.amount > 50000:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Digital goods purchase: ₦{transaction.amount:,.0f}",
                    score=self.base_score,
                    confidence=0.68
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
            verticals=["marketplace", "ecommerce"]
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.72,
                    message="High-risk merchant category"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.65,
                    message=f"Merchant chargeback rate: {rate:.1%}"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.68,
                    message=f"Merchant refund rate: {rate:.1%}"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.63,
                    message=f"Card ({card_country}) != user country ({user_country})"
                )
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.78,
                message="Card expired or expiring"
            )
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.70,
                message=f"High-value digital goods: ₦{transaction.amount:,.0f}"
            )
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.72,
                message=f"Bulk digital goods: {quantity} items"
            )
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.60,
                message="Card used for first time"
            )
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.80,
                message=f"Amount mismatch: ₦{transaction.amount:,.0f} vs ₦{expected_amount:,.0f}"
            )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.88,
                    message="BIN attack pattern detected"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.84,
                    message="Small fails then large success pattern"
                )
        return None


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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.80,
                    message="Refund abuse pattern detected"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.75,
                    message="Cashback abuse pattern detected"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.82,
                    message="Fake merchant transactions detected"
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.70,
                message=f"Shipping {transaction.shipping_distance_km}km from billing"
            )
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.82,
                message="Dropshipping fraud indicator"
            )
        return None


# Export all ecommerce rules
ECOMMERCE_RULES = [
    CardBINFraudRule(),
    ShippingMismatchRule(),
    DigitalGoodsHighValueRule(),
    HighRiskCategoryRule(),
    MerchantHighRiskCategoryRule(),
    MerchantChargebackRateRule(),
    MerchantRefundRateRule(),
    CardBINMismatchRule(),
    ExpiredCardRule(),
    DigitalGoodsHighAmountRule(),
    BulkDigitalGoodsRule(),
    FirstTimeCardRule(),
    TransactionAmountMismatchRule(),
    BINAttackPatternRule(),
    SmallFailsLargeSuccessRule(),
    RefundAbuseDetectedRule(),
    CashbackAbuseDetectedRule(),
    FakeMerchantTransactionsRule(),
    CardBINReputationRule(),
    ShippingBillingDistanceRule(),
    EcommerceDropshippingRule(),
]
