"""
Betting and gaming-specific fraud detection rules

This module contains fraud detection rules specific to betting and gaming verticals,
including bonus abuse, wagering patterns, arbitrage detection, and card-related fraud.

Rules for:
- Sports betting platforms
- Online casinos
- Gaming platforms
- Fantasy sports
"""

from typing import Optional, Dict, Any
from app.schemas import TransactionCheckRequest, FraudFlag
from .base import FraudRule


class BonusAbuseRule(FraudRule):
    """Rule 20: Bonus Abuse - Suspicious bonus claiming patterns"""

    def __init__(self):
        super().__init__(
            name="bonus_abuse",
            description="Potential bonus abuse pattern",
            base_score=35,
            severity="high",
            verticals=["betting", "gaming"]
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
            verticals=["betting", "gaming"]
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
            verticals=["betting", "gaming"]
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.86,
                message="High arbitrage betting likelihood"
            )
        return None


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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.70,
                    message=f"Card only {age} days old"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.75,
                    message=f"Card reputation: {rep}/100"
                )
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.55,
                message=f"Suspiciously round amount: ₦{transaction.amount:,.0f}"
            )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.72,
                    message="Promotion abuse pattern detected"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.70,
                    message="Loyalty points abuse detected"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.74,
                    message="Referral fraud detected"
                )
        return None


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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.70,
                    message="Card <3 days old"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.80,
                    message="Card testing pattern detected"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.75,
                    message="Card reputation score <25"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.70,
                    message="High-risk merchant category"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.88,
                    message="Card linked to fraud accounts"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.72,
                    message="Refund abuse pattern detected"
                )
        return None


# Export all betting rules
BETTING_RULES = [
    BonusAbuseRule(),
    WithdrawalWithoutWageringRule(),
    ArbitrageBettingRule(),
    BettingArbitrageHighLikelihoodRule(),
    CardAgeNewRule(),
    CardReputationLowRule(),
    RoundAmountSuspiciousRule(),
    PromoAbuseDetectedRule(),
    LoyaltyPointsAbuseRule(),
    ReferralFraudRule(),
    TransactionCardNewRule(),
    TransactionCardTestingRule(),
    TransactionCardReputationRule(),
    TransactionMerchantHighRiskRule(),
    NetworkCardFraudLinkRule(),
    MerchantRefundAbuseRule(),
]
