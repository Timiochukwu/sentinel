"""
Cryptocurrency-specific fraud detection rules

This module contains fraud detection rules specific to cryptocurrency transactions,
including wallet analysis, P2P trading patterns, and crypto-specific fraud schemes.

Rules for:
- Cryptocurrency exchanges
- DeFi platforms
- Crypto trading platforms
- Wallet services
"""

from typing import Optional, Dict, Any
from app.schemas import TransactionCheckRequest, FraudFlag
from .base import FraudRule


class NewWalletHighValueRule(FraudRule):
    """Rule 24: New Wallet High Value - New wallet with large transaction"""

    def __init__(self):
        super().__init__(
            name="new_wallet_high_value",
            description="New crypto wallet with high-value transaction",
            base_score=35,
            severity="high",
            verticals=["crypto"]
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
            verticals=["crypto"]
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
            verticals=["crypto"]
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.80,
                    message=f"New wallet ({age}d) with large transaction"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.88,
                    message="Withdrawal after deposit (coin tumbling)"
                )
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
            return FraudFlag(
                type=self.name,
                severity=self.severity,
                score=self.base_score,
                confidence=0.88,
                message="Pump & dump pattern detected"
            )
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
            wallet_age = transaction.transaction_features.crypto.wallet_age_days
            if wallet_age and wallet_age < 1:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.78,
                    message="Crypto wallet <1 day old"
                )
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
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    score=self.base_score,
                    confidence=0.85,
                    message="Large withdrawal from new crypto wallet"
                )
        return None


# Export all crypto rules
CRYPTO_RULES = [
    NewWalletHighValueRule(),
    SuspiciousWalletRule(),
    P2PVelocityRule(),
    CryptoNewWalletHighValueRule(),
    CryptoWithdrawalAfterDepositRule(),
    CryptoPumpDumpRule(),
    TransactionCryptoNewWalletRule(),
    TransactionCryptoHighValueWithdrawalRule(),
]
