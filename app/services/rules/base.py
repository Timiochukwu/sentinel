"""
Base fraud detection rule classes and rules engine

This module provides the foundation for all fraud detection rules:
- FraudRule: Base class that all rules inherit from
- FraudRulesEngine: Orchestrates execution of all rules
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from app.models.schemas import FraudFlag, TransactionCheckRequest, Industry


class FraudRule:
    """Base class for fraud detection rules"""

    def __init__(self, name: str, description: str, base_score: int, severity: str, verticals: List[str] = None):
        self.name = name
        self.description = description
        self.base_score = base_score
        self.severity = severity
        # Vertical industries this rule applies to (e.g., ["lending", "fintech", "payments"])
        # If None, rule applies to all verticals
        self.verticals = verticals or [
            "lending", "fintech", "payments", "crypto",
            "ecommerce", "betting", "marketplace", "gaming"
        ]

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


class FraudRulesEngine:
    """
    Orchestrates execution of all fraud detection rules

    This engine:
    1. Loads all rules from vertical-specific modules
    2. Filters rules based on industry vertical
    3. Executes applicable rules
    4. Aggregates scores and flags
    5. Returns fraud detection result
    """

    def __init__(self):
        """Initialize the rules engine with all available rules"""
        self.all_rules: List[FraudRule] = []
        self._load_rules()

    def _load_rules(self):
        """
        Load all rules from vertical modules

        Imports all fraud detection rules from organized vertical-specific modules
        """
        from .lending import LENDING_RULES
        from .ecommerce import ECOMMERCE_RULES
        from .crypto import CRYPTO_RULES
        from .betting import BETTING_RULES
        from .marketplace import MARKETPLACE_RULES
        from .universal import UNIVERSAL_RULES
        from .identity import IDENTITY_RULES
        from .device import DEVICE_RULES
        from .network import NETWORK_RULES
        from .behavioral import BEHAVIORAL_RULES
        from .ato import ATO_RULES

        self.all_rules = (
            LENDING_RULES +
            ECOMMERCE_RULES +
            CRYPTO_RULES +
            BETTING_RULES +
            MARKETPLACE_RULES +
            UNIVERSAL_RULES +
            IDENTITY_RULES +
            DEVICE_RULES +
            NETWORK_RULES +
            BEHAVIORAL_RULES +
            ATO_RULES
        )

    def get_rules_for_vertical(self, industry: str) -> List[FraudRule]:
        """Get all rules that apply to the given industry vertical"""
        return [rule for rule in self.all_rules if rule.applies_to_vertical(industry)]

    def evaluate(
        self,
        transaction: TransactionCheckRequest,
        context: Dict[str, Any],
        industry: Optional[Industry] = None
    ) -> Dict[str, Any]:
        """
        Evaluate all applicable rules for a transaction

        Args:
            transaction: Transaction to check
            context: Additional context (consortium data, velocity, etc.)
            industry: Industry vertical (if None, uses transaction.industry)

        Returns:
            Dict with fraud_score, flags, and decision
        """
        industry_str = industry.value if industry else transaction.industry.value
        applicable_rules = self.get_rules_for_vertical(industry_str)

        flags: List[FraudFlag] = []
        total_score = 0

        for rule in applicable_rules:
            try:
                flag = rule.check(transaction, context)
                if flag:
                    flags.append(flag)
                    total_score += flag.score
            except Exception as e:
                # Log error but continue with other rules
                print(f"Error evaluating rule {rule.name}: {e}")
                continue

        # Determine decision based on score and vertical threshold
        # These thresholds should come from vertical_service in production
        decision = "approve"
        if total_score >= 60:
            decision = "decline"
        elif total_score >= 30:
            decision = "review"

        return {
            "fraud_score": total_score,
            "decision": decision,
            "flags": flags,
            "rules_evaluated": len(applicable_rules),
            "rules_triggered": len(flags)
        }
