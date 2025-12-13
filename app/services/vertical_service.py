"""
Vertical Configuration Service

Manages industry-specific fraud detection configurations across 7 verticals:
- Lending, Fintech, Ecommerce, Betting, Gaming, Crypto, Marketplace

Each vertical has:
- Custom fraud score thresholds
- Rule-specific weight multipliers
- AML risk thresholds
- Enabled/disabled status

Usage:
    from app.services.vertical_service import vertical_service

    # Get config for a vertical
    config = vertical_service.get_config(Industry.CRYPTO)

    # Get rule weight for vertical
    weight = vertical_service.get_rule_weight(Industry.LENDING, "LoanStackingRule")

    # List all verticals
    verticals = vertical_service.list_verticals()
"""

from typing import Dict, Optional, List
from app.models.schemas import Industry
from pydantic import BaseModel, Field


class VerticalConfig(BaseModel):
    """Configuration for a single industry vertical"""

    vertical: Industry
    fraud_score_threshold: float = Field(
        ...,
        ge=0,
        le=100,
        description="Fraud score threshold (0-100). Transactions above this are flagged as fraudulent."
    )
    rule_weight_multiplier: Dict[str, float] = Field(
        default_factory=dict,
        description="Rule-specific weight multipliers. Default 1.0 if not specified."
    )
    aml_risk_threshold: float = Field(
        ...,
        ge=0,
        le=100,
        description="AML (Anti-Money Laundering) risk threshold"
    )
    enabled: bool = Field(
        default=True,
        description="Whether this vertical is currently active"
    )
    description: str = Field(
        default="",
        description="Human-readable description of this vertical"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "vertical": "crypto",
                "fraud_score_threshold": 50.0,
                "rule_weight_multiplier": {
                    "SuspiciousWalletRule": 1.5,
                    "KYCVerificationRule": 2.0,
                    "NewWalletHighValueRule": 1.8
                },
                "aml_risk_threshold": 60.0,
                "enabled": True,
                "description": "Cryptocurrency exchanges and trading platforms"
            }
        }


class VerticalConfigService:
    """
    Manage vertical-specific fraud detection configurations

    This service provides:
    1. Fraud score thresholds per vertical
    2. Rule weight multipliers per vertical (some rules matter more in certain industries)
    3. AML risk thresholds per vertical
    4. Enable/disable verticals

    Example:
        Crypto has a LOWER fraud threshold (50%) because fraud risk is higher.
        Lending has a HIGHER fraud threshold (65%) because false positives cost more.
    """

    def __init__(self):
        """Initialize with default configurations for all 7 verticals"""
        self.configs = self._initialize_configs()

    def _initialize_configs(self) -> Dict[str, VerticalConfig]:
        """
        Initialize default configurations for all industry verticals

        Threshold Philosophy:
        - LOWER threshold = Stricter (flag more transactions as fraud)
        - HIGHER threshold = Looser (only flag obvious fraud)

        Industry Risk Profiles:
        - Crypto/Betting: High fraud risk → Lower threshold (50-55%)
        - Gaming: Medium-high risk → Medium threshold (50%)
        - Fintech/Ecommerce/Marketplace: Medium risk → Medium threshold (60%)
        - Lending: Lower tolerance for false positives → Higher threshold (65%)
        """
        return {
            # LENDING - Banks, loan providers, credit cards
            Industry.LENDING.value: VerticalConfig(
                vertical=Industry.LENDING,
                fraud_score_threshold=65.0,  # Higher threshold - false positives expensive
                rule_weight_multiplier={
                    # Lending-specific rules get higher weight
                    "LoanStackingRule": 1.5,              # Critical for lending
                    "MaximumFirstTransactionRule": 1.8,   # New borrowers with large amounts
                    "NewAccountLargeAmountRule": 1.3,
                    "DisposableEmailRule": 1.2,           # Identity verification important
                    "SIMSwapPatternRule": 1.4,            # Account takeover detection

                    # Rules less relevant to lending get lower weight
                    "GamblingTransactionRule": 0.3,       # Not applicable
                    "BonusAbuseRule": 0.0,                # Not applicable
                    "CardBINFraudRule": 0.5,              # Less relevant for loans
                },
                aml_risk_threshold=75.0,
                description="Banks, loan providers, credit cards, personal loans"
            ),

            # FINTECH - Digital wallets, payment processors, mobile money
            Industry.FINTECH.value: VerticalConfig(
                vertical=Industry.FINTECH,
                fraud_score_threshold=60.0,  # Medium threshold
                rule_weight_multiplier={
                    "NewAccountLargeAmountRule": 1.4,
                    "VelocityCheckRule": 1.3,             # Transaction velocity important
                    "SIMSwapPatternRule": 1.5,            # Common attack vector
                    "DeviceSharingRule": 1.2,
                    "DisposableEmailRule": 1.2,
                    "ImpossibleTravelRule": 1.3,          # Location anomalies

                    # Less relevant
                    "CardBINFraudRule": 0.7,              # Some fintech doesn't use cards
                    "ShippingMismatchRule": 0.0,          # No shipping
                },
                aml_risk_threshold=70.0,
                description="Digital wallets, payment apps, payment processors, mobile money"
            ),

            # ECOMMERCE - Online retail, shopping platforms
            Industry.ECOMMERCE.value: VerticalConfig(
                vertical=Industry.ECOMMERCE,
                fraud_score_threshold=60.0,  # Medium threshold
                rule_weight_multiplier={
                    # Ecommerce-specific rules
                    "CardBINFraudRule": 1.6,              # Card fraud common
                    "ShippingMismatchRule": 1.5,          # Address mismatch critical
                    "DigitalGoodsHighValueRule": 1.4,     # Digital goods fraud
                    "MultipleFailedPaymentsRule": 1.3,    # Card testing

                    # General fraud rules
                    "DisposableEmailRule": 1.2,
                    "VelocityCheckRule": 1.2,
                    "DeviceSharingRule": 1.1,

                    # Not applicable
                    "LoanStackingRule": 0.0,
                    "BonusAbuseRule": 0.0,
                },
                aml_risk_threshold=65.0,
                description="Online retail, shopping platforms, digital marketplaces"
            ),

            # BETTING - Sports betting, gambling platforms
            Industry.BETTING.value: VerticalConfig(
                vertical=Industry.BETTING,
                fraud_score_threshold=55.0,  # Lower threshold - high fraud risk
                rule_weight_multiplier={
                    # Betting-specific rules
                    "BonusAbuseRule": 1.8,                # Critical for betting
                    "ArbitrageBettingRule": 1.6,          # Arbitrage detection
                    "ExcessiveWithdrawalsRule": 1.5,      # Bonus abuse pattern
                    "WithdrawalWithoutWageringRule": 1.7, # Bonus churning

                    # General fraud
                    "DeviceSharingRule": 1.4,             # Multi-accounting
                    "VelocityCheckRule": 1.3,
                    "NewAccountLargeAmountRule": 1.2,

                    # Not applicable
                    "CardBINFraudRule": 0.5,
                    "ShippingMismatchRule": 0.0,
                    "LoanStackingRule": 0.0,
                },
                aml_risk_threshold=60.0,
                description="Sports betting, gambling platforms, wagering services"
            ),

            # GAMING - Online gaming, esports, in-game purchases
            Industry.GAMING.value: VerticalConfig(
                vertical=Industry.GAMING,
                fraud_score_threshold=50.0,  # Lower threshold - account sharing/cheating common
                rule_weight_multiplier={
                    # Gaming-specific
                    "DeviceSharingRule": 1.6,             # Account sharing detection
                    "DormantAccountActivationRule": 1.5,  # Hacked accounts
                    "BonusAbuseRule": 1.4,                # Game bonuses

                    # General
                    "NewAccountLargeAmountRule": 1.2,
                    "VelocityCheckRule": 1.2,
                    "DisposableEmailRule": 1.1,

                    # Not applicable
                    "CardBINFraudRule": 0.6,              # Many use alternative payment
                    "ShippingMismatchRule": 0.0,
                    "LoanStackingRule": 0.0,
                },
                aml_risk_threshold=55.0,
                description="Online gaming, esports platforms, in-game purchases"
            ),

            # CRYPTO - Cryptocurrency exchanges, DeFi platforms
            Industry.CRYPTO.value: VerticalConfig(
                vertical=Industry.CRYPTO,
                fraud_score_threshold=50.0,  # LOWEST threshold - very high fraud risk
                rule_weight_multiplier={
                    # Crypto-specific rules
                    "SuspiciousWalletRule": 1.8,          # Sanctioned wallets
                    "NewWalletHighValueRule": 1.7,        # New wallet large deposit
                    "P2PVelocityRule": 1.6,               # P2P trading velocity

                    # KYC/AML critical
                    "KYCVerificationRule": 2.0,           # HIGHEST weight - AML compliance
                    "SIMSwapPatternRule": 1.5,            # Account takeover
                    "ImpossibleTravelRule": 1.4,

                    # Not applicable
                    "CardBINFraudRule": 0.0,              # Crypto doesn't use cards
                    "ShippingMismatchRule": 0.0,
                    "LoanStackingRule": 0.0,
                },
                aml_risk_threshold=60.0,  # Lower AML threshold - stricter compliance
                description="Cryptocurrency exchanges, DeFi platforms, crypto trading"
            ),

            # MARKETPLACE - P2P marketplaces, multi-sided platforms
            Industry.MARKETPLACE.value: VerticalConfig(
                vertical=Industry.MARKETPLACE,
                fraud_score_threshold=60.0,  # Medium threshold
                rule_weight_multiplier={
                    # Marketplace-specific
                    "NewSellerHighValueRule": 1.6,        # New sellers with high-value items
                    "LowRatedSellerRule": 1.5,            # Seller reputation
                    "HighRiskCategoryRule": 1.4,          # Electronics, luxury goods
                    "P2PVelocityRule": 1.3,               # P2P transaction patterns

                    # General
                    "DisposableEmailRule": 1.2,
                    "DeviceSharingRule": 1.2,
                    "VelocityCheckRule": 1.1,

                    # Not applicable
                    "LoanStackingRule": 0.0,
                    "BonusAbuseRule": 0.0,
                },
                aml_risk_threshold=65.0,
                description="P2P marketplaces, multi-sided platforms, seller networks"
            ),
        }

    def get_config(self, vertical: Industry) -> VerticalConfig:
        """
        Get configuration for a specific vertical

        Args:
            vertical: Industry vertical enum

        Returns:
            VerticalConfig with thresholds and rule weights

        Example:
            config = service.get_config(Industry.CRYPTO)
            print(config.fraud_score_threshold)  # 50.0
        """
        return self.configs.get(vertical.value)

    def get_rule_weight(self, vertical: Industry, rule_name: str) -> float:
        """
        Get weight multiplier for a specific rule in a vertical

        Args:
            vertical: Industry vertical
            rule_name: Name of the fraud rule (e.g., "LoanStackingRule")

        Returns:
            Weight multiplier (default 1.0 if not specified)

        Example:
            weight = service.get_rule_weight(Industry.CRYPTO, "SuspiciousWalletRule")
            # Returns 1.8 (crypto weighs wallet checks heavily)
        """
        config = self.get_config(vertical)
        if not config:
            return 1.0
        return config.rule_weight_multiplier.get(rule_name, 1.0)

    def list_verticals(self) -> List[str]:
        """
        List all available industry verticals

        Returns:
            List of vertical names

        Example:
            verticals = service.list_verticals()
            # ['lending', 'fintech', 'ecommerce', 'betting', 'gaming', 'crypto', 'marketplace']
        """
        return list(self.configs.keys())

    def get_all_configs(self) -> Dict[str, VerticalConfig]:
        """
        Get all vertical configurations

        Returns:
            Dictionary mapping vertical name to config
        """
        return self.configs

    def update_config(self, vertical: Industry, **kwargs) -> VerticalConfig:
        """
        Update configuration for a vertical

        Args:
            vertical: Industry vertical to update
            **kwargs: Fields to update (fraud_score_threshold, rule_weight_multiplier, etc.)

        Returns:
            Updated VerticalConfig

        Example:
            config = service.update_config(
                Industry.CRYPTO,
                fraud_score_threshold=45.0,  # Make stricter
                rule_weight_multiplier={"NewWalletHighValueRule": 2.0}
            )
        """
        config = self.get_config(vertical)
        if not config:
            raise ValueError(f"Vertical {vertical.value} not found")

        # Update fields
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)

        return config


# Singleton instance
vertical_service = VerticalConfigService()


# Convenience functions
def get_vertical_config(vertical: Industry) -> VerticalConfig:
    """Get configuration for a vertical (convenience function)"""
    return vertical_service.get_config(vertical)


def get_vertical_threshold(vertical: Industry) -> float:
    """Get fraud score threshold for a vertical (convenience function)"""
    config = vertical_service.get_config(vertical)
    return config.fraud_score_threshold if config else 60.0  # Default 60%


def get_rule_weight_for_vertical(vertical: Industry, rule_name: str) -> float:
    """Get rule weight for vertical (convenience function)"""
    return vertical_service.get_rule_weight(vertical, rule_name)
