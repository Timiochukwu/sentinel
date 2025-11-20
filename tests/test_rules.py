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

    assert len(rule_names) == 29  # We have 29 rules total
    assert "new_account_large_amount" in rule_names
    assert "loan_stacking" in rule_names
    assert "sim_swap_pattern" in rule_names


# ============================================================================
# MULTI-VERTICAL SUPPORT TESTS (NEW)
# ============================================================================

def test_get_rules_for_vertical_lending():
    """Test that lending vertical gets lending-specific rules"""
    from app.models.schemas import Industry

    engine = FraudRulesEngine()
    lending_rules = engine.get_rules_for_vertical("lending")

    # Lending should have core rules + lending-specific rules
    rule_names = [rule.name for rule in lending_rules]

    # Should include core rules
    assert "new_account_large_amount" in rule_names
    assert "loan_stacking" in rule_names
    assert "sim_swap_pattern" in rule_names

    # Should NOT include crypto-specific rules
    assert "suspicious_wallet" not in rule_names
    assert "p2p_velocity" not in rule_names

    # Should NOT include betting-specific rules
    assert "bonus_abuse" not in rule_names

    print(f"✅ Lending rules: {len(lending_rules)} rules")


def test_get_rules_for_vertical_crypto():
    """Test that crypto vertical gets crypto-specific rules"""
    engine = FraudRulesEngine()
    crypto_rules = engine.get_rules_for_vertical("crypto")

    rule_names = [rule.name for rule in crypto_rules]

    # Should include crypto-specific rules
    assert "new_wallet_high_value" in rule_names
    assert "suspicious_wallet" in rule_names
    assert "p2p_velocity" in rule_names

    # Should include some universal rules
    assert "new_device" in rule_names

    # Should NOT include lending-specific rules
    assert "loan_stacking" not in rule_names

    print(f"✅ Crypto rules: {len(crypto_rules)} rules")


def test_get_rules_for_vertical_ecommerce():
    """Test that ecommerce vertical gets ecommerce-specific rules"""
    engine = FraudRulesEngine()
    ecommerce_rules = engine.get_rules_for_vertical("ecommerce")

    rule_names = [rule.name for rule in ecommerce_rules]

    # Should include ecommerce-specific rules
    assert "card_bin_fraud" in rule_names
    assert "shipping_mismatch" in rule_names
    assert "digital_goods_high_value" in rule_names

    # Should NOT include crypto rules
    assert "suspicious_wallet" not in rule_names

    print(f"✅ E-commerce rules: {len(ecommerce_rules)} rules")


def test_get_rules_for_vertical_betting():
    """Test that betting vertical gets betting-specific rules"""
    engine = FraudRulesEngine()
    betting_rules = engine.get_rules_for_vertical("betting")

    rule_names = [rule.name for rule in betting_rules]

    # Should include betting-specific rules
    assert "bonus_abuse" in rule_names
    assert "withdrawal_without_wagering" in rule_names
    assert "arbitrage_betting" in rule_names
    assert "excessive_withdrawals" in rule_names

    # Should NOT include marketplace rules
    assert "new_seller_high_value" not in rule_names

    print(f"✅ Betting rules: {len(betting_rules)} rules")


def test_evaluate_by_vertical_lending():
    """Test fraud detection with lending vertical"""
    engine = FraudRulesEngine()

    transaction = TransactionCheckRequest(
        transaction_id="test_lending_001",
        user_id="user_001",
        amount=250000,
        account_age_days=2,
        industry="lending",
        transaction_type="loan_disbursement"
    )

    context = {
        "consortium": {
            "client_count": 3,
            "lenders": ["A", "B", "C"]
        }
    }

    risk_score, risk_level, decision, flags = engine.evaluate(
        transaction, context, industry="lending"
    )

    # Should detect loan stacking in lending vertical
    flag_types = [flag.type for flag in flags]
    assert "loan_stacking" in flag_types
    assert risk_score >= 40

    print(f"✅ Lending evaluation: risk_score={risk_score}, flags={len(flags)}")


def test_evaluate_by_vertical_crypto():
    """Test fraud detection with crypto vertical"""
    engine = FraudRulesEngine()

    transaction = TransactionCheckRequest(
        transaction_id="test_crypto_001",
        user_id="user_001",
        amount=1000000,
        is_new_wallet=True,
        industry="crypto",
        transaction_type="crypto_withdrawal"
    )

    context = {}

    risk_score, risk_level, decision, flags = engine.evaluate(
        transaction, context, industry="crypto"
    )

    # Should detect new wallet high value in crypto vertical
    flag_types = [flag.type for flag in flags]
    assert "new_wallet_high_value" in flag_types
    assert risk_score >= 35

    print(f"✅ Crypto evaluation: risk_score={risk_score}, flags={len(flags)}")


def test_evaluate_by_vertical_marketplace():
    """Test fraud detection with marketplace vertical"""
    engine = FraudRulesEngine()

    transaction = TransactionCheckRequest(
        transaction_id="test_marketplace_001",
        user_id="user_001",
        amount=500000,
        seller_account_age_days=2,
        is_high_value_item=True,
        industry="marketplace",
        transaction_type="seller_payout"
    )

    context = {}

    risk_score, risk_level, decision, flags = engine.evaluate(
        transaction, context, industry="marketplace"
    )

    # Should detect new seller high value in marketplace vertical
    flag_types = [flag.type for flag in flags]
    assert "new_seller_high_value" in flag_types

    print(f"✅ Marketplace evaluation: risk_score={risk_score}, flags={len(flags)}")


def test_vertical_enum_conversion():
    """Test that Industry enum is properly converted"""
    from app.models.schemas import Industry

    engine = FraudRulesEngine()

    # Create transaction with Industry enum
    transaction = TransactionCheckRequest(
        transaction_id="test_enum_001",
        user_id="user_001",
        amount=100000,
        industry=Industry.CRYPTO,
        transaction_type="crypto_deposit"
    )

    # Should handle enum conversion properly
    risk_score, risk_level, decision, flags = engine.evaluate(
        transaction, {}, industry="crypto"
    )

    assert risk_score is not None
    assert risk_level is not None

    print(f"✅ Industry enum conversion works correctly")


def test_rule_applies_to_vertical():
    """Test individual rule vertical applicability"""
    from app.services.rules import (
        LoanStackingRule,
        SuspiciousWalletRule,
        BonusAbuseRule,
        NewSellerHighValueRule
    )

    # Loan stacking should only apply to lending
    loan_rule = LoanStackingRule()
    assert loan_rule.applies_to_vertical("lending") == True
    assert loan_rule.applies_to_vertical("crypto") == False
    assert loan_rule.applies_to_vertical("betting") == False

    # Suspicious wallet should only apply to crypto
    wallet_rule = SuspiciousWalletRule()
    assert wallet_rule.applies_to_vertical("crypto") == True
    assert wallet_rule.applies_to_vertical("lending") == False

    # Bonus abuse should only apply to betting
    bonus_rule = BonusAbuseRule()
    assert bonus_rule.applies_to_vertical("betting") == True
    assert bonus_rule.applies_to_vertical("crypto") == False

    # New seller rule should only apply to marketplace
    seller_rule = NewSellerHighValueRule()
    assert seller_rule.applies_to_vertical("marketplace") == True
    assert seller_rule.applies_to_vertical("ecommerce") == False

    print(f"✅ Rule vertical applicability checks pass")
