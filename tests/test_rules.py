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


# ============================================================================
# PHASE 2 FEATURES - 18 NEW RULES (Rules 40-57) TESTS
# ============================================================================

def test_browser_fingerprint_consistency_rule():
    """Test browser fingerprint consistency detection"""
    from app.services.rules import BrowserFingerprintConsistencyRule

    rule = BrowserFingerprintConsistencyRule()

    # Should trigger: canvas fingerprint changed
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        canvas_fingerprint="abc123"
    )

    context = {"previous_canvas_fingerprint": "xyz789"}
    result = rule.check(transaction, context)
    assert result is not None
    assert result.type == "browser_fingerprint_consistency"

    # Should NOT trigger: same fingerprint
    context2 = {"previous_canvas_fingerprint": "abc123"}
    result2 = rule.check(transaction, context2)
    assert result2 is None

    print("✅ Browser fingerprint consistency rule passed")


def test_screen_resolution_anomaly_rule():
    """Test screen resolution anomaly detection"""
    from app.services.rules import ScreenResolutionAnomalyRule

    rule = ScreenResolutionAnomalyRule()

    # Should trigger: screen resolution changed dramatically
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        screen_resolution="1920x1080"
    )

    context = {"previous_screen_resolution": "375x667"}  # Mobile resolution
    result = rule.check(transaction, context)
    assert result is not None
    assert result.type == "screen_resolution_anomaly"

    print("✅ Screen resolution anomaly rule passed")


def test_timezone_hopping_rule():
    """Test timezone hopping detection"""
    from app.services.rules import TimezoneHoppingRule

    rule = TimezoneHoppingRule()

    # Should trigger: timezone changed by more than 8 hours
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        timezone_offset=0  # UTC
    )

    context = {"previous_timezone_offset": -480}  # PST (-8 hours)
    result = rule.check(transaction, context)
    assert result is not None
    assert result.type == "timezone_hopping"

    print("✅ Timezone hopping rule passed")


def test_robot_session_detection_rule():
    """Test bot/robot session detection"""
    from app.services.rules import RobotSessionDetectionRule

    rule = RobotSessionDetectionRule()

    # Should trigger: very short session + unnatural mouse movement
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        session_duration_seconds=2,
        mouse_movement_score=10
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "robot_session_detection"
    assert result.score == 40

    # Should NOT trigger: normal session
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=100000,
        session_duration_seconds=60,
        mouse_movement_score=75
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    print("✅ Robot session detection rule passed")


def test_suspicious_typing_pattern_rule():
    """Test typing speed anomaly detection"""
    from app.services.rules import SuspiciousTypingPatternRule

    rule = SuspiciousTypingPatternRule()

    # Should trigger: extremely fast typing (bot)
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        typing_speed_wpm=200  # Unrealistically fast
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "suspicious_typing_pattern"

    # Should NOT trigger: normal typing
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=100000,
        typing_speed_wpm=65  # Normal human typing
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    print("✅ Suspicious typing pattern rule passed")


def test_excessive_copy_paste_rule():
    """Test excessive copy/paste detection"""
    from app.services.rules import ExcessiveCopyPasteRule

    rule = ExcessiveCopyPasteRule()

    # Should trigger: lots of copy/paste (credential stuffing)
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        copy_paste_count=15
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "excessive_copy_paste"

    # Should NOT trigger: minimal copy/paste
    transaction2 = TransactionCheckRequest(
        transaction_id="test_002",
        user_id="user_001",
        amount=100000,
        copy_paste_count=2
    )

    result2 = rule.check(transaction2, {})
    assert result2 is None

    print("✅ Excessive copy/paste rule passed")


def test_unverified_social_media_rule():
    """Test unverified social media detection"""
    from app.services.rules import UnverifiedSocialMediaRule

    rule = UnverifiedSocialMediaRule()

    # Should trigger: large transaction with unverified social media
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=250000,
        social_media_verified=False
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "unverified_social_media"

    print("✅ Unverified social media rule passed")


def test_new_social_media_account_rule():
    """Test new social media account detection"""
    from app.services.rules import NewSocialMediaAccountRule

    rule = NewSocialMediaAccountRule()

    # Should trigger: brand new social media account
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        social_media_age_days=5
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "new_social_media_account"

    print("✅ New social media account rule passed")


def test_unverified_address_rule():
    """Test unverified address detection"""
    from app.services.rules import UnverifiedAddressRule

    rule = UnverifiedAddressRule()

    # Should trigger: large transaction with unverified address
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=350000,
        address_verified=False
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "unverified_address"

    print("✅ Unverified address rule passed")


def test_shipping_billing_distance_rule():
    """Test shipping/billing distance mismatch detection"""
    from app.services.rules import ShippingBillingDistanceRule

    rule = ShippingBillingDistanceRule()

    # Should trigger: very large distance between shipping and billing
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        shipping_distance_km=2000
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "shipping_billing_distance"

    print("✅ Shipping/billing distance rule passed")


def test_unusual_transaction_frequency_rule():
    """Test unusual transaction frequency detection"""
    from app.services.rules import UnusualTransactionFrequencyRule

    rule = UnusualTransactionFrequencyRule()

    # Should trigger: very high transaction frequency
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        transaction_frequency_per_day=25
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "unusual_transaction_frequency"

    print("✅ Unusual transaction frequency rule passed")


def test_amount_anomaly_rule():
    """Test transaction amount anomaly detection"""
    from app.services.rules import AmountAnomalyRule

    rule = AmountAnomalyRule()

    # Should trigger: amount very different from average
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=1000000,
        avg_transaction_amount=100000
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "amount_anomaly"

    print("✅ Amount anomaly rule passed")


def test_chargeback_history_rule():
    """Test chargeback history detection"""
    from app.services.rules import ChargebackHistoryRule

    rule = ChargebackHistoryRule()

    # Should trigger: user has chargeback history
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        chargeback_history_count=3
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "chargeback_history"

    print("✅ Chargeback history rule passed")


def test_refund_abuse_pattern_rule_phase2():
    """Test refund abuse pattern detection (Phase 2)"""
    from app.services.rules import RefundAbusePatternRule

    rule = RefundAbusePatternRule()

    # Should trigger: excessive refund history
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        refund_history_count=10
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "refund_abuse_pattern"

    print("✅ Refund abuse pattern rule passed")


def test_holiday_weekend_transaction_rule():
    """Test holiday/weekend transaction detection"""
    from app.services.rules import HolidayWeekendTransactionRule

    rule = HolidayWeekendTransactionRule()

    # Should trigger: large transaction on holiday/weekend
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=250000,
        holiday_weekend_transaction=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "holiday_weekend_transaction"

    print("✅ Holiday/weekend transaction rule passed")


def test_browser_consistency_rule():
    """Test browser consistency detection"""
    from app.services.rules import BrowserConsistencyRule

    rule = BrowserConsistencyRule()

    # Should trigger: browser fingerprint changed
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        browser_fonts_hash="hash123"
    )

    context = {"previous_browser_fonts_hash": "hash456"}
    result = rule.check(transaction, context)
    assert result is not None
    assert result.type == "browser_consistency"

    print("✅ Browser consistency rule passed")


# ============================================================================
# PHASE 3 FEATURES - 52 NEW RULES (Rules 56-107) TESTS
# ============================================================================

def test_keystroke_dynamics_rule():
    """Test keystroke dynamics detection"""
    from app.services.rules import KeystrokeDynamicsRule

    rule = KeystrokeDynamicsRule()

    # Should trigger: keystroke dynamics don't match
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        keystroke_dynamics_score=20
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "keystroke_dynamics"

    print("✅ Keystroke dynamics rule passed")


def test_mobile_swipe_pattern_rule():
    """Test mobile swipe pattern detection"""
    from app.services.rules import MobileSwipePatternRule

    rule = MobileSwipePatternRule()

    # Should trigger: unnatural swipe pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        swipe_pattern_score=15
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "mobile_swipe_pattern"

    print("✅ Mobile swipe pattern rule passed")


def test_touch_pressure_inconsistency_rule():
    """Test touch pressure consistency detection"""
    from app.services.rules import TouchPressureInconsistencyRule

    rule = TouchPressureInconsistencyRule()

    # Should trigger: touch pressure pattern changed
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        touch_pressure_consistent=False
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "touch_pressure_inconsistency"

    print("✅ Touch pressure inconsistency rule passed")


def test_device_acceleration_pattern_rule():
    """Test device acceleration pattern detection"""
    from app.services.rules import DeviceAccelerationPatternRule

    rule = DeviceAccelerationPatternRule()

    # Should trigger: abnormal acceleration pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        acceleration_pattern_score=15
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "device_acceleration_pattern"

    print("✅ Device acceleration pattern rule passed")


def test_scroll_behavior_anomaly_rule():
    """Test scroll behavior anomaly detection"""
    from app.services.rules import ScrollBehaviorAnomalyRule

    rule = ScrollBehaviorAnomalyRule()

    # Should trigger: unnatural scroll behavior
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        scroll_behavior_score=10
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "scroll_behavior_anomaly"

    print("✅ Scroll behavior anomaly rule passed")


def test_shared_account_detection_rule():
    """Test shared account detection"""
    from app.services.rules import SharedAccountDetectionRule

    rule = SharedAccountDetectionRule()

    # Should trigger: many users sharing same device/IP
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        co_user_count=8
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "shared_account_detection"

    print("✅ Shared account detection rule passed")


def test_email_fraud_linkage_rule():
    """Test email fraud linkage detection"""
    from app.services.rules import EmailFraudLinkageRule

    rule = EmailFraudLinkageRule()

    # Should trigger: email linked to fraud account
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        shared_email_with_fraud=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "email_fraud_linkage"
    assert result.score == 40

    print("✅ Email fraud linkage rule passed")


def test_phone_fraud_linkage_rule():
    """Test phone fraud linkage detection"""
    from app.services.rules import PhoneFraudLinkageRule

    rule = PhoneFraudLinkageRule()

    # Should trigger: phone linked to fraud account
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        shared_phone_with_fraud=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "phone_fraud_linkage"
    assert result.score == 40

    print("✅ Phone fraud linkage rule passed")


def test_device_fraud_linkage_rule():
    """Test device fraud linkage detection"""
    from app.services.rules import DeviceFraudLinkageRule

    rule = DeviceFraudLinkageRule()

    # Should trigger: device linked to fraud account
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        shared_device_with_fraud=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "device_fraud_linkage"
    assert result.score == 40

    print("✅ Device fraud linkage rule passed")


def test_ip_fraud_linkage_rule():
    """Test IP fraud linkage detection"""
    from app.services.rules import IPFraudLinkageRule

    rule = IPFraudLinkageRule()

    # Should trigger: IP linked to fraud account
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        shared_ip_with_fraud=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "ip_fraud_linkage"
    assert result.score == 40

    print("✅ IP fraud linkage rule passed")


def test_name_uniqueness_rule():
    """Test name uniqueness detection"""
    from app.services.rules import NameUniquenessRule

    rule = NameUniquenessRule()

    # Should trigger: very common name (potential synthetic identity)
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        first_name_uniqueness=0.95,  # Very common name
        last_name_uniqueness=0.98
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "name_uniqueness"

    print("✅ Name uniqueness rule passed")


def test_email_domain_legitimacy_rule():
    """Test email domain legitimacy detection"""
    from app.services.rules import EmailDomainLegitimacyRule

    rule = EmailDomainLegitimacyRule()

    # Should trigger: suspicious email domain
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        email_domain_legitimacy=20
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "email_domain_legitimacy"

    print("✅ Email domain legitimacy rule passed")


def test_phone_carrier_risk_rule():
    """Test phone carrier risk detection"""
    from app.services.rules import PhoneCarrierRiskRule

    rule = PhoneCarrierRiskRule()

    # Should trigger: risky phone carrier
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        phone_carrier_risk=85
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "phone_carrier_risk"

    print("✅ Phone carrier risk rule passed")


def test_bvn_fraud_matching_rule():
    """Test BVN fraud matching detection"""
    from app.services.rules import BVNFraudMatchingRule

    rule = BVNFraudMatchingRule()

    # Should trigger: BVN linked to fraud
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        bvn_fraud_match_count=2
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "bvn_fraud_matching"

    print("✅ BVN fraud matching rule passed")


def test_family_fraud_link_rule():
    """Test family fraud linkage detection"""
    from app.services.rules import FamilyFraudLinkRule

    rule = FamilyFraudLinkRule()

    # Should trigger: family member has fraud history
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        family_member_with_fraud=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "family_fraud_link"

    print("✅ Family fraud link rule passed")


def test_known_fraudster_pattern_rule():
    """Test known fraudster pattern detection"""
    from app.services.rules import KnownFraudsterPatternRule

    rule = KnownFraudsterPatternRule()

    # Should trigger: matches known fraudster pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        known_fraudster_pattern=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "known_fraudster_pattern"

    print("✅ Known fraudster pattern rule passed")


def test_synthetic_identity_rule():
    """Test synthetic identity detection"""
    from app.services.rules import SyntheticIdentityRule

    rule = SyntheticIdentityRule()

    # Should trigger: synthetic identity detected
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        linked_to_synthetic_fraud=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "synthetic_identity"

    print("✅ Synthetic identity rule passed")


def test_cross_vertical_velocity_rule():
    """Test cross-vertical velocity detection"""
    from app.services.rules import CrossVerticalVelocityRule

    rule = CrossVerticalVelocityRule()

    # Should trigger: high velocity across verticals
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        velocity_between_verticals=15
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "cross_vertical_velocity"

    print("✅ Cross-vertical velocity rule passed")


def test_account_resurrection_rule():
    """Test account resurrection detection"""
    from app.services.rules import AccountResurrectionRule

    rule = AccountResurrectionRule()

    # Should trigger: old account reactivated
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        account_resurrection_attempt=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "account_resurrection"

    print("✅ Account resurrection rule passed")


def test_account_history_fraud_matching_rule():
    """Test account history fraud pattern matching"""
    from app.services.rules import AccountHistoryFraudMatchingRule

    rule = AccountHistoryFraudMatchingRule()

    # Should trigger: historical account matches fraud patterns
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        account_history_matches_fraud=3
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "account_history_fraud_matching"

    print("✅ Account history fraud matching rule passed")


def test_previously_declined_transaction_rule():
    """Test previously declined transaction detection"""
    from app.services.rules import PreviouslyDeclinedTransactionRule

    rule = PreviouslyDeclinedTransactionRule()

    # Should trigger: transaction was previously declined
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        previously_declined_transaction=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "previously_declined_transaction"

    print("✅ Previously declined transaction rule passed")


def test_chargeback_abuse_pattern_rule_phase3():
    """Test chargeback abuse pattern detection (Phase 3)"""
    from app.services.rules import ChargebackAbusePatternRule

    rule = ChargebackAbusePatternRule()

    # Should trigger: chargeback abuse pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        chargeback_abuse_pattern=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "chargeback_abuse_pattern"

    print("✅ Chargeback abuse pattern rule passed")


def test_entropy_anomaly_rule():
    """Test entropy anomaly detection"""
    from app.services.rules import EntropyAnomalyRule

    rule = EntropyAnomalyRule()

    # Should trigger: entropy score indicates anomaly
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        entropy_score=0.95  # Very high entropy = very unusual
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "entropy_anomaly"

    print("✅ Entropy anomaly rule passed")


def test_ml_anomaly_score_rule():
    """Test ML anomaly score detection"""
    from app.services.rules import MLAnomalyScoreRule

    rule = MLAnomalyScoreRule()

    # Should trigger: high ML anomaly score
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        anomaly_score=0.85
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "ml_anomaly_score"

    print("✅ ML anomaly score rule passed")


def test_low_legitimacy_score_rule():
    """Test low legitimacy score detection"""
    from app.services.rules import LowLegitimacyScoreRule

    rule = LowLegitimacyScoreRule()

    # Should trigger: low legitimacy score
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        transaction_legitimacy_score=20
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "low_legitimacy_score"

    print("✅ Low legitimacy score rule passed")


def test_profile_deviation_rule():
    """Test user profile deviation detection"""
    from app.services.rules import ProfileDeviationRule

    rule = ProfileDeviationRule()

    # Should trigger: large deviation from user profile
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        user_profile_deviation=0.8
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "profile_deviation"

    print("✅ Profile deviation rule passed")


def test_device_manufacturer_risk_rule():
    """Test device manufacturer risk detection"""
    from app.services.rules import DeviceManufacturerRiskRule

    rule = DeviceManufacturerRiskRule()

    # Should trigger: risky device manufacturer
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        device_manufacturer_risk=90
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "device_manufacturer_risk"

    print("✅ Device manufacturer risk rule passed")


def test_device_age_rule():
    """Test device age detection"""
    from app.services.rules import DeviceAgeRule

    rule = DeviceAgeRule()

    # Should trigger: very new device model
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        device_model_age_months=1
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "device_age"

    print("✅ Device age rule passed")


def test_emulator_detection_rule():
    """Test emulator detection"""
    from app.services.rules import EmulatorDetectionRule

    rule = EmulatorDetectionRule()

    # Should trigger: running on emulator
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        emulator_detected=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "emulator_detection"

    print("✅ Emulator detection rule passed")


def test_jailbreak_detection_rule():
    """Test jailbreak/root detection"""
    from app.services.rules import JailbreakDetectionRule

    rule = JailbreakDetectionRule()

    # Should trigger: device is jailbroken/rooted
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        jailbreak_detected=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "jailbreak_detection"

    print("✅ Jailbreak detection rule passed")


def test_suspicious_app_detection_rule():
    """Test suspicious app detection"""
    from app.services.rules import SuspiciousAppDetectionRule

    rule = SuspiciousAppDetectionRule()

    # Should trigger: suspicious app installed
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        suspicious_app_installed=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "suspicious_app_detection"

    print("✅ Suspicious app detection rule passed")


def test_lending_cross_sell_fraud_rule():
    """Test lending cross-sell fraud detection"""
    from app.services.rules import LendingCrossSellFraudRule

    rule = LendingCrossSellFraudRule()

    # Should trigger: lending cross-sell fraud pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        lending_cross_sell_pattern=True,
        industry="lending"
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "lending_cross_sell_fraud"

    print("✅ Lending cross-sell fraud rule passed")


def test_ecommerce_dropshipper_fraud_rule():
    """Test ecommerce dropshipper fraud detection"""
    from app.services.rules import EcommerceDroshipperFraudRule

    rule = EcommerceDroshipperFraudRule()

    # Should trigger: dropshipping fraud pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        ecommerce_dropshipper_pattern=True,
        industry="ecommerce"
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "ecommerce_dropshipper_fraud"

    print("✅ Ecommerce dropshipper fraud rule passed")


def test_crypto_pump_dump_rule():
    """Test crypto pump & dump detection"""
    from app.services.rules import CryptoPumpDumpRule

    rule = CryptoPumpDumpRule()

    # Should trigger: pump & dump pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        crypto_pump_dump_signal=True,
        industry="crypto"
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "crypto_pump_dump"

    print("✅ Crypto pump & dump rule passed")


def test_betting_arbitrage_rule():
    """Test betting arbitrage detection"""
    from app.services.rules import BettingArbitrageRule

    rule = BettingArbitrageRule()

    # Should trigger: betting arbitrage pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        betting_arbitrage_likelihood=85,
        industry="betting"
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "betting_arbitrage"

    print("✅ Betting arbitrage rule passed")


def test_marketplace_collusion_rule():
    """Test marketplace collusion detection"""
    from app.services.rules import MarketplaceCollusionRule

    rule = MarketplaceCollusionRule()

    # Should trigger: marketplace seller collusion
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        marketplace_seller_collusion=True,
        industry="marketplace"
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "marketplace_collusion"

    print("✅ Marketplace collusion rule passed")


def test_transaction_pattern_entropy_rule():
    """Test transaction pattern entropy detection"""
    from app.services.rules import TransactionPatternEntropyRule

    rule = TransactionPatternEntropyRule()

    # Should trigger: high entropy in transaction patterns
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        transaction_pattern_entropy=0.9
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "transaction_pattern_entropy"

    print("✅ Transaction pattern entropy rule passed")


def test_behavioral_consistency_rule():
    """Test behavioral consistency detection"""
    from app.services.rules import BehavioralConsistencyRule

    rule = BehavioralConsistencyRule()

    # Should trigger: low behavioral consistency
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        behavioral_consistency_score=15
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "behavioral_consistency"

    print("✅ Behavioral consistency rule passed")


def test_account_age_velocity_ratio_rule():
    """Test account age to velocity ratio detection"""
    from app.services.rules import AccountAgeVelocityRatioRule

    rule = AccountAgeVelocityRatioRule()

    # Should trigger: high velocity for account age
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        account_age_velocity_ratio=5.5  # Very high ratio
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "account_age_velocity_ratio"

    print("✅ Account age velocity ratio rule passed")


def test_geographic_consistency_rule():
    """Test geographic consistency detection"""
    from app.services.rules import GeographicConsistencyRule

    rule = GeographicConsistencyRule()

    # Should trigger: low geographic consistency
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        geographic_consistency_score=10
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "geographic_consistency"

    print("✅ Geographic consistency rule passed")


def test_temporal_consistency_rule():
    """Test temporal consistency detection"""
    from app.services.rules import TemporalConsistencyRule

    rule = TemporalConsistencyRule()

    # Should trigger: low temporal consistency
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        temporal_consistency_score=15
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "temporal_consistency"

    print("✅ Temporal consistency rule passed")


def test_multi_account_cross_funding_rule():
    """Test multi-account cross-funding detection"""
    from app.services.rules import MultiAccountCrossFundingRule

    rule = MultiAccountCrossFundingRule()

    # Should trigger: money flowing between accounts
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        multi_account_cross_funding=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "multi_account_cross_funding"

    print("✅ Multi-account cross-funding rule passed")


def test_round_trip_transaction_rule():
    """Test round-trip transaction detection"""
    from app.services.rules import RoundTripTransactionRule

    rule = RoundTripTransactionRule()

    # Should trigger: round-trip transaction pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        round_trip_transaction=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "round_trip_transaction"

    print("✅ Round-trip transaction rule passed")


def test_test_transaction_pattern_rule():
    """Test transaction pattern detection"""
    from app.services.rules import TestTransactionPatternRule

    rule = TestTransactionPatternRule()

    # Should trigger: small test transactions before large one
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        test_transaction_pattern=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "test_transaction_pattern"

    print("✅ Test transaction pattern rule passed")


def test_rapid_account_progression_rule():
    """Test rapid account progression detection"""
    from app.services.rules import RapidAccountProgressionRule

    rule = RapidAccountProgressionRule()

    # Should trigger: rapid account tier progression
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        rapid_account_progression=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "rapid_account_progression"

    print("✅ Rapid account progression rule passed")


def test_suspicious_beneficiary_pattern_rule():
    """Test suspicious beneficiary pattern detection"""
    from app.services.rules import SuspiciousBeneficiaryPatternRule

    rule = SuspiciousBeneficiaryPatternRule()

    # Should trigger: suspicious beneficiary pattern
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        suspicious_beneficiary_pattern=True
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "suspicious_beneficiary_pattern"

    print("✅ Suspicious beneficiary pattern rule passed")


def test_deep_learning_fraud_score_rule():
    """Test deep learning fraud score detection"""
    from app.services.rules import DeepLearningFraudScoreRule

    rule = DeepLearningFraudScoreRule()

    # Should trigger: high deep learning fraud score
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        deep_learning_fraud_score=0.85
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "deep_learning_fraud_score"

    print("✅ Deep learning fraud score rule passed")


def test_ensemble_model_confidence_rule():
    """Test ensemble model confidence detection"""
    from app.services.rules import EnsembleModelConfidenceRule

    rule = EnsembleModelConfidenceRule()

    # Should trigger: high ensemble model fraud confidence
    transaction = TransactionCheckRequest(
        transaction_id="test_001",
        user_id="user_001",
        amount=100000,
        ensemble_model_confidence=0.92
    )

    result = rule.check(transaction, {})
    assert result is not None
    assert result.type == "ensemble_model_confidence"

    print("✅ Ensemble model confidence rule passed")


def test_total_rule_count_with_phase2_phase3():
    """Verify total rule count is 109 (29 original + 10 Phase 1 + 70 Phase 2&3)"""
    engine = FraudRulesEngine()
    rule_names = engine.get_all_rule_names()

    assert len(rule_names) == 109, f"Expected 109 rules, got {len(rule_names)}"

    print(f"✅ All 109 rules present (29 original + 10 Phase 1 + 70 Phase 2&3)")
