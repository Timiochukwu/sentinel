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


# ============================================================================
# PHASE 1 FEATURES - 10 NEW RULES (Rules 30-39) TESTS
# ============================================================================

def test_email_domain_age_rule():
    """Test email domain age detection"""
    from app.services.rules import EmailDomainAgeRule

    rule = EmailDomainAgeRule()

    # Should trigger: brand new email domain
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        email_domain_age_days=5  # 5 days old
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "email_domain_age"
    assert result.score == 25

    # Should NOT trigger: established domain
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=100000,
        email_domain_age_days=365  # 1 year old
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    print("✅ Email domain age rule passed")


def test_suspicious_ip_reputation_rule():
    """Test IP reputation detection"""
    from app.services.rules import SuspiciousIPReputationRule

    rule = SuspiciousIPReputationRule()

    # Should trigger: bad IP reputation
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        ip_reputation_score=15  # Very poor
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "suspicious_ip_reputation"
    assert result.score == 35

    # Should NOT trigger: good reputation
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=100000,
        ip_reputation_score=95  # Excellent
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    print("✅ IP reputation rule passed")


def test_excessive_failed_logins_rule():
    """Test account takeover detection"""
    from app.services.rules import ExcessiveFailedLoginsRule

    rule = ExcessiveFailedLoginsRule()

    # Should trigger: many failed logins in 24h
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        failed_login_count_24h=8
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "excessive_failed_logins"
    assert result.score == 40

    # Should trigger: many failed logins in 7 days
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=100000,
        failed_login_count_7d=12
    )

    result2 = rule.check(transaction2, {})
    assert result2 is not None
    assert result2.score == 30  # 40 - 10

    print("✅ Failed logins rule passed")


def test_unusual_transaction_time_rule():
    """Test unusual transaction time detection"""
    from app.services.rules import UnusualTransactionTimeRule

    rule = UnusualTransactionTimeRule()

    # Should trigger: unusual time
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        transaction_hour=3,
        is_unusual_time=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "unusual_transaction_time"

    # Should NOT trigger: normal time
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=100000,
        transaction_hour=14,
        is_unusual_time=False
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    print("✅ Unusual transaction time rule passed")


def test_first_transaction_amount_rule():
    """Test first transaction amount detection"""
    from app.services.rules import FirstTransactionAmountRule

    rule = FirstTransactionAmountRule()

    # Should trigger: first transaction much larger than average
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=1000000,
        first_transaction_amount=1000000
    )

    context = {"average_transaction_amount": 100000}  # User avg is ₦100k

    result = rule.check(transaction, context)
    assert result is not None
    assert result.type == "first_transaction_amount"

    # Should NOT trigger: first transaction reasonable
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=150000,
        first_transaction_amount=150000
    )

    result2 = rule.check(transaction2, context)
    assert result2 is None

    print("✅ First transaction amount rule passed")


def test_card_bin_reputation_rule():
    """Test card BIN reputation detection"""
    from app.services.rules import CardBINReputationRule

    rule = CardBINReputationRule()

    # Should trigger: poor BIN reputation
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        card_bin_reputation_score=10  # Very poor
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "card_bin_reputation"
    assert result.score == 30

    # Should NOT trigger: good reputation
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=100000,
        card_bin_reputation_score=90  # Excellent
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    print("✅ Card BIN reputation rule passed")


def test_unverified_phone_rule():
    """Test unverified phone detection"""
    from app.services.rules import UnverifiedPhoneRule

    rule = UnverifiedPhoneRule()

    # Should trigger: large transaction from unverified phone
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=250000,
        phone_verified=False
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "unverified_phone"

    # Should NOT trigger: verified phone
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=250000,
        phone_verified=True
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    # Should NOT trigger: small amount from unverified phone
    transaction3 = TransactionCheckRequest(
        transaction_id="test_003",
        user_id="user_001",
        amount=50000,
        phone_verified=False
    )

    result3 = rule.check(transaction3, {})
    assert result3 is None

    print("✅ Unverified phone rule passed")


def test_quick_signup_transaction_rule():
    """Test rapid signup + transaction detection"""
    from app.services.rules import QuickSignupTransactionRule

    rule = QuickSignupTransactionRule()

    # Should trigger: large transaction within 24h of signup
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=250000,
        days_since_signup=0.5  # 12 hours
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "quick_signup_transaction"

    # Should NOT trigger: transaction more than 24h after signup
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=250000,
        days_since_signup=2  # 2 days
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    print("✅ Quick signup transaction rule passed")


def test_os_inconsistency_rule():
    """Test OS/platform inconsistency detection"""
    from app.services.rules import OSInconsistencyRule

    rule = OSInconsistencyRule()

    # Should trigger: different OS than usual
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        platform_os="iOS 16",
        platform_os_consistent=False
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "os_inconsistency"

    # Should NOT trigger: consistent OS
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=100000,
        platform_os="Android 12",
        platform_os_consistent=True
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    print("✅ OS inconsistency rule passed")


def test_total_rule_count_with_phase1():
    """Verify total rule count is 39 (29 original + 10 Phase 1)"""
    engine = FraudRulesEngine()
    rule_names = engine.get_all_rule_names()

    assert len(rule_names) == 39, f"Expected 39 rules, got {len(rule_names)}"

    # Verify Phase 1 rules are present
    phase1_rules = [
        "email_domain_age",
        "suspicious_ip_reputation",
        "excessive_failed_logins",
        "unusual_transaction_time",
        "first_transaction_amount",
        "card_bin_reputation",
        "unverified_phone",
        "multiple_devices_same_user",
        "quick_signup_transaction",
        "os_inconsistency"
    ]

    for rule_name in phase1_rules:
        assert rule_name in rule_names, f"Rule {rule_name} not found"

    print(f"✅ All 39 rules present (29 original + 10 Phase 1)")
