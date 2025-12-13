"""
Fraud detection rules specific to the FINTECH vertical

Rules for:
- Digital wallets
- Payment processors
- Mobile money
- P2P payment apps
- Remittance services
"""

from typing import Dict, Any, Optional
from .base import FraudRule
from app.models.schemas import FraudFlag, TransactionCheckRequest


class SIMSwapPatternRule(FraudRule):
    """Detects SIM swap attack pattern"""

    def __init__(self):
        super().__init__(
            name="sim_swap_pattern",
            description="Pattern indicating SIM swap attack",
            base_score=45,
            severity="critical",
            verticals=["lending", "fintech", "payments"]
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


class P2PVelocityRule(FraudRule):
    """P2P transaction velocity check"""

    def __init__(self):
        super().__init__(
            name="p2p_velocity",
            description="Too many P2P transfers",
            base_score=25,
            severity="medium",
            verticals=["fintech", "crypto", "marketplace"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_type == "p2p_transfer":
            velocity_data = context.get("velocity", {})
            p2p_count_24h = velocity_data.get("p2p_count_24h", 0)

            if p2p_count_24h > 10:
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"{p2p_count_24h} P2P transfers in 24h",
                    score=self.base_score,
                    confidence=0.75
                )
        return None


# Add more fintech rules here...
# - CardTestingPatternRule
# - MultipleFailedPaymentsRule
# - NewBankAccountWithdrawalRule
# etc.


# Export all fintech rules
FINTECH_RULES = [
    SIMSwapPatternRule(),
    P2PVelocityRule(),
    # Add more as they're migrated...
]
