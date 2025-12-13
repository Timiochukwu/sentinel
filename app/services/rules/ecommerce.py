"""
Fraud detection rules specific to the ECOMMERCE vertical

Rules for:
- Online retail
- Shopping platforms
- Digital marketplaces
- Subscription services
"""

from typing import Dict, Any, Optional
from .base import FraudRule
from app.models.schemas import FraudFlag, TransactionCheckRequest


class ShippingMismatchRule(FraudRule):
    """Shipping address different from billing address"""

    def __init__(self):
        super().__init__(
            name="shipping_mismatch",
            description="Shipping and billing addresses don't match",
            base_score=25,
            severity="medium",
            verticals=["ecommerce"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shipping_address and transaction.billing_address:
            if transaction.shipping_address != transaction.billing_address:
                distance_km = transaction.shipping_distance_km or 0

                if distance_km > 100:  # More than 100km apart
                    return FraudFlag(
                        type=self.name,
                        severity=self.severity,
                        message=f"Shipping {distance_km}km from billing address",
                        score=self.base_score,
                        confidence=0.75
                    )
        return None


class DigitalGoodsHighValueRule(FraudRule):
    """High-value digital goods purchase (gift cards, gaming, etc.)"""

    def __init__(self):
        super().__init__(
            name="digital_goods_high_value",
            description="High-value digital goods purchase",
            base_score=30,
            severity="medium",
            verticals=["ecommerce", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        digital_goods = ["gift_card", "gaming_credits", "digital_currency", "subscription"]

        if transaction.product_category in digital_goods:
            if transaction.amount > 50000:  # ₦50k
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Digital goods purchase: ₦{transaction.amount:,.0f}",
                    score=self.base_score,
                    confidence=0.78
                )
        return None


# Add more ecommerce rules here...
# - CardBINFraudRule
# - MultipleFailedPaymentsRule
# - BulkDigitalGoodsRule
# etc.


# Export all ecommerce rules
ECOMMERCE_RULES = [
    ShippingMismatchRule(),
    DigitalGoodsHighValueRule(),
    # Add more as they're migrated...
]
