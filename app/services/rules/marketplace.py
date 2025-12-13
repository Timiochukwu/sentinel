"""
Marketplace-specific fraud detection rules

This module contains fraud detection rules specific to marketplace platforms,
including seller reputation, collusion detection, and high-risk listings.

Rules for:
- Peer-to-peer marketplaces
- C2C platforms
- Multi-seller platforms
- Classified ads platforms
"""

from typing import Optional, Dict, Any
from app.schemas import TransactionCheckRequest, FraudFlag
from .base import FraudRule


class NewSellerHighValueRule(FraudRule):
    """Rule 27: New Seller High Value - New seller with expensive items"""

    def __init__(self):
        super().__init__(
            name="new_seller_high_value",
            description="New seller listing high-value items",
            base_score=35,
            severity="high",
            verticals=["marketplace"]
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
            verticals=["marketplace"]
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.87,
                message="Seller collusion indicators detected"
            )
        return None


# Export all marketplace rules
MARKETPLACE_RULES = [
    NewSellerHighValueRule(),
    LowRatedSellerRule(),
    MarketplaceCollusionRule(),
]
