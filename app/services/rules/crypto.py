"""
Fraud detection rules specific to the CRYPTO vertical

Rules for:
- Cryptocurrency exchanges
- DeFi platforms
- Crypto trading platforms
- Wallet services
"""

from typing import Dict, Any, Optional
from .base import FraudRule
from app.models.schemas import FraudFlag, TransactionCheckRequest


class SuspiciousWalletRule(FraudRule):
    """Wallet appears on sanctions list or high-risk database"""

    def __init__(self):
        super().__init__(
            name="suspicious_wallet",
            description="Wallet on sanctions/high-risk list",
            base_score=50,
            severity="critical",
            verticals=["crypto"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.wallet_address:
            # In production, check against OFAC sanctions list, Chainalysis, etc.
            sanctioned_wallets = context.get("sanctioned_wallets", [])

            if transaction.wallet_address in sanctioned_wallets:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Wallet {transaction.wallet_address[:10]}... on sanctions list",
                    score=self.base_score,
                    confidence=0.99
                )
        return None


class NewWalletHighValueRule(FraudRule):
    """New wallet (<30 days) with high-value transaction"""

    def __init__(self):
        super().__init__(
            name="new_wallet_high_value",
            description="New wallet with large transaction",
            base_score=35,
            severity="high",
            verticals=["crypto"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.wallet_age_days is not None and transaction.wallet_age_days < 30:
            if transaction.amount > 1000000:  # ₦1M or equivalent
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Wallet only {transaction.wallet_age_days} days old, transaction ₦{transaction.amount:,.0f}",
                    score=self.base_score,
                    confidence=0.82
                )
        return None


# Add more crypto rules here...
# - KYCVerificationRule
# - CryptoPumpDumpRule
# - MixerServiceRule
# etc.


# Export all crypto rules
CRYPTO_RULES = [
    SuspiciousWalletRule(),
    NewWalletHighValueRule(),
    # Add more as they're migrated...
]
