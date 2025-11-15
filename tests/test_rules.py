"""Test fraud detection rules"""

import pytest
from app.services.rules import (
    FraudRulesEngine,
    NewAccountLargeAmountRule,
    LoanStackingRule,
    SIMSwapPatternRule
)
from app.models.schemas import TransactionCheckRequest


def test_new_account_large_amount_rule():
    """Test new account large amount rule"""
    rule = NewAccountLargeAmountRule()

    # Should trigger: 3 days old + ₦150k
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=150000,
        account_age_days=3
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "new_account_large_amount"
    assert result.score == 30

    # Should NOT trigger: 30 days old + ₦150k
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_002",
        amount=150000,
        account_age_days=30
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None


def test_loan_stacking_rule():
    """Test loan stacking rule"""
    rule = LoanStackingRule()

    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000
    )

    # Should trigger: 3 other lenders
    context = {
        "consortium": {
            "client_count": 3,
            "lenders": ["Lender A", "Lender B", "Lender C"]
        }
    }

    result = rule.check(transaction, context)
    assert result is not None
    assert result.type == "loan_stacking"
    assert result.score == 40
    assert result.severity == "critical"

    # Should NOT trigger: only 1 other lender
    context2 = {
        "consortium": {
            "client_count": 1,
            "lenders": ["Lender A"]
        }
    }

    result2 = rule.check(transaction, context2)
    assert result2 is None


def test_sim_swap_pattern_rule():
    """Test SIM swap pattern rule"""
    rule = SIMSwapPatternRule()

    # Should trigger: phone changed + new device + withdrawal
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        transaction_type="withdrawal",
        phone_changed_recently=True
    )

    context = {
        "new_device": True
    }

    result = rule.check(transaction, context)
    assert result is not None
    assert result.type == "sim_swap_pattern"
    assert result.score == 45
    assert result.severity == "critical"

    # Should NOT trigger: phone not changed
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_002",
        amount=100000,
        transaction_type="withdrawal",
        phone_changed_recently=False
    )

    result2 = rule.check(transaction2, context)
    assert result2 is None


def test_fraud_rules_engine():
    """Test fraud rules engine integration"""
    engine = FraudRulesEngine()

    # High risk transaction
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=250000,
        account_age_days=2,
        phone_changed_recently=True,
        transaction_type="loan_disbursement"
    )

    context = {
        "new_device": True,
        "consortium": {
            "client_count": 3,
            "lenders": ["A", "B", "C"]
        }
    }

    risk_score, risk_level, decision, flags = engine.evaluate(transaction, context)

    assert risk_score > 70  # Should be high risk
    assert risk_level == "high"
    assert decision == "decline"
    assert len(flags) >= 2  # Multiple flags should be triggered


def test_get_all_rules():
    """Test getting all rule names"""
    engine = FraudRulesEngine()
    rule_names = engine.get_all_rule_names()

    assert len(rule_names) == 15  # We have 15 rules
    assert "new_account_large_amount" in rule_names
    assert "loan_stacking" in rule_names
    assert "sim_swap_pattern" in rule_names
