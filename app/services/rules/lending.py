"""
Fraud detection rules specific to the LENDING vertical

Rules for:
- Banks
- Loan providers
- Credit card companies
- Personal loan platforms
- Buy-now-pay-later (BNPL)
"""

from typing import Dict, Any, Optional
from .base import FraudRule
from app.models.schemas import FraudFlag, TransactionCheckRequest


class LoanStackingRule(FraudRule):
    """Detects multiple concurrent loan applications across lenders"""

    def __init__(self):
        super().__init__(
            name="loan_stacking",
            description="Applied to multiple lenders recently",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments"]
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


class MaximumFirstTransactionRule(FraudRule):
    """First loan amount exceeds reasonable threshold"""

    def __init__(self):
        super().__init__(
            name="maximum_first_transaction",
            description="First transaction amount too high",
            base_score=35,
            severity="high",
            verticals=["lending"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_count == 1:  # First transaction
            if transaction.amount > 500000:  # ₦500k
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"First loan of ₦{transaction.amount:,.0f} is unusually high",
                    score=self.base_score,
                    confidence=0.81
                )
        return None


# Add more lending rules here...
# - SequentialApplicationsRule
# - IncomeVerificationFailureRule
# - EmploymentFraudRule
# - CreditHistoryInconsistencyRule
# etc.


# Export all lending rules
LENDING_RULES = [
    LoanStackingRule(),
    MaximumFirstTransactionRule(),
    # Add more as they're migrated...
]
