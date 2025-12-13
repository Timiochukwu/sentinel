"""
Identity verification fraud detection rules

This module contains fraud detection rules related to identity verification,
including email, phone, BVN validation, and consortium network checks.

Rules for:
- Email verification and reputation
- Phone verification and carrier risk
- BVN (Bank Verification Number) validation
- Consortium network fraud linkage
"""

from typing import Optional, Dict, Any
from app.schemas import TransactionCheckRequest, FraudFlag
from .base import FraudRule


class DisposableEmailRule(FraudRule):
    """Rule 12: Disposable Email - Email from tempmail, guerrillamail, etc"""

    def __init__(self):
        super().__init__(
            name="disposable_email",
            description="Disposable/temporary email address",
            base_score=20,
            severity="low",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
        self.disposable_domains = [
            "tempmail.com", "guerrillamail.com", "10minutemail.com",
            "throwaway.email", "mailinator.com", "temp-mail.org"
        ]

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.email:
            email_lower = transaction.email.lower()
            for domain in self.disposable_domains:
                if domain in email_lower:
                    return FraudFlag(
                        type=self.name,
                        severity=self.severity,
                        message=f"Disposable email service detected: {domain}",
                        score=self.base_score,
                        confidence=0.95
                    )
        return None

class SequentialApplicationsRule(FraudRule):
    """Rule 15: Sequential Applications - Pattern like user1@, user2@, user3@"""

    def __init__(self):
        super().__init__(
            name="sequential_applications",
            description="Sequential email/user ID pattern",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.email:
            # Check for patterns like user1@, user2@, test1@, etc.
            pattern = r'(user|test|demo|temp)\d+@'
            if re.search(pattern, transaction.email.lower()):
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Sequential pattern detected in email: {transaction.email}",
                    score=self.base_score,
                    confidence=0.81
                )
        return None


### E-COMMERCE FRAUD RULES ###

class EmailDomainLegitimacyRule(FraudRule):
    """Email domain legitimacy check"""
    def __init__(self):
        super().__init__(
            name="email_domain_legitimacy",
            description="Email from suspicious domain",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.email:
            if transaction.identity_features.email.domain:
                domain = transaction.identity_features.email.domain.lower()
                suspicious_domains = ['tempmail.com', 'guerrillamail.com', 'mailinator.com', '10minutemail.com']
                if any(d in domain for d in suspicious_domains):
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"Suspicious email domain: {domain}")
        return None

class EmailVerificationMismatchRule(FraudRule):
    """Unverified email with high-value transaction"""
    def __init__(self):
        super().__init__(
            name="email_verification_mismatch",
            description="Unverified email with suspicious activity",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.email:
            if not transaction.identity_features.email.verification_status and transaction.amount > 500000:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.75, message="Unverified email with large transaction")
        return None

class PhoneVerificationFailureRule(FraudRule):
    """Phone fails verification attempts"""
    def __init__(self):
        super().__init__(
            name="phone_verification_failure",
            description="Phone fails multiple verification attempts",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        verification_attempts = context.get("phone_verification_attempts", 0)
        if verification_attempts > 3:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"Phone failed {verification_attempts} verification attempts")
        return None

class PhoneCountryMismatchRule(FraudRule):
    """Phone country differs from IP country"""
    def __init__(self):
        super().__init__(
            name="phone_country_mismatch",
            description="Phone country differs from location",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.phone and transaction.identity_features.network:
            phone_country = transaction.identity_features.phone.country_code
            ip_country = transaction.identity_features.network.ip_country
            if phone_country and ip_country and phone_country != ip_country:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message=f"Phone ({phone_country}) != IP ({ip_country})")
        return None

class BVNAgeInconsistencyRule(FraudRule):
    """BVN age inconsistent with other indicators"""
    def __init__(self):
        super().__init__(
            name="bvn_age_inconsistency",
            description="BVN age mismatches account age",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        bvn_age = context.get("bvn_age_days", 0)
        account_age = transaction.account_age_days or 0
        if bvn_age > 0 and account_age > 0:
            age_diff = abs(bvn_age - account_age)
            if age_diff > 365:  # More than 1 year difference
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message=f"BVN age ({bvn_age}d) vs account ({account_age}d)")
        return None

class MultipleEmailsDeviceRule(FraudRule):
    """Device has multiple email addresses"""
    def __init__(self):
        super().__init__(
            name="multiple_emails_device",
            description="Multiple emails linked to device",
            base_score=23,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        email_count = context.get("device_email_count", 1)
        if email_count > 5:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message=f"Device linked to {email_count} emails")
        return None

class BankAccountVerificationFailRule(FraudRule):
    """Bank account fails verification"""
    def __init__(self):
        super().__init__(
            name="bank_account_verification_fail",
            description="Bank account not verified",
            base_score=24,
            severity="medium",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.transaction_features and transaction.transaction_features.banking:
            verified = transaction.transaction_features.banking.account_verification
            if verified is False and transaction.amount > 500000:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Unverified bank account with large transaction")
        return None

class ConsortiumEmailFrequencyRule(FraudRule):
    """Email seen at many lenders recently"""
    def __init__(self):
        super().__init__(
            name="consortium_email_frequency",
            description="Email appearing at multiple lenders",
            base_score=30,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.consortium_matching:
            if transaction.network_features.consortium_matching.email_seen_elsewhere:
                count = context.get("email_lender_count", 2)
                if count > 3:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message=f"Email at {count} other lenders")
        return None

class ConsortiumPhoneFrequencyRule(FraudRule):
    """Phone seen at many lenders"""
    def __init__(self):
        super().__init__(
            name="consortium_phone_frequency",
            description="Phone at multiple lenders",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.consortium_matching:
            if transaction.network_features.consortium_matching.phone_seen_elsewhere:
                count = context.get("phone_lender_count", 2)
                if count > 3:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"Phone at {count} other lenders")
        return None

class ConsortiumBVNFrequencyRule(FraudRule):
    """BVN seen with multiple identities"""
    def __init__(self):
        super().__init__(
            name="consortium_bvn_frequency",
            description="BVN linked to multiple accounts",
            base_score=35,
            severity="critical",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.consortium_matching:
            if transaction.network_features.consortium_matching.bvn_seen_elsewhere:
                count = context.get("bvn_account_count", 2)
                if count > 2:
                    return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message=f"BVN linked to {count} accounts")
        return None

class NetworkVelocityEmailRule(FraudRule):
    """High velocity across email"""
    def __init__(self):
        super().__init__(
            name="network_velocity_email",
            description="High transaction velocity on email",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.velocity:
            velocity = transaction.network_features.velocity.velocity_email
            if velocity and velocity > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.80, message=f"Email velocity: {velocity} txns")
        return None

class NetworkVelocityPhoneRule(FraudRule):
    """High velocity across phone"""
    def __init__(self):
        super().__init__(
            name="network_velocity_phone",
            description="High transaction velocity on phone",
            base_score=28,
            severity="high",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.velocity:
            velocity = transaction.network_features.velocity.velocity_phone
            if velocity and velocity > 10:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.82, message=f"Phone velocity: {velocity} txns")
        return None

class EmailFraudHistoryRule(FraudRule):
    """Email linked to confirmed fraud"""
    def __init__(self):
        super().__init__(
            name="email_fraud_history",
            description="Email linked to fraud cases",
            base_score=35,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.email_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.95, message="Email linked to confirmed fraud")
        return None

class PhoneFraudHistoryRule(FraudRule):
    """Phone linked to confirmed fraud"""
    def __init__(self):
        super().__init__(
            name="phone_fraud_history",
            description="Phone linked to fraud cases",
            base_score=34,
            severity="critical",
            verticals=["lending", "fintech", "payments"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.phone_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.94, message="Phone linked to confirmed fraud")
        return None

class EmailSimilarityHighRule(FraudRule):
    """Email similar to known fraud case"""
    def __init__(self):
        super().__init__(
            name="email_similarity_high",
            description="Email similar to fraud cases",
            base_score=26,
            severity="high",
            verticals=["lending", "fintech", "payments", "ecommerce"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.derived_features and transaction.derived_features.similarity:
            similarity = transaction.derived_features.similarity.email_similarity
            if similarity and similarity > 0.8:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.78, message=f"Email similarity: {similarity:.2f}")
        return None

class EmailDomainAgeRule(FraudRule):
    """Rule 30: Email Domain Age - Newly created email domains"""

    def __init__(self):
        super().__init__(
            name="email_domain_age",
            description="Email from newly created domain",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.email_domain_age_days is not None:
            if transaction.email_domain_age_days < 30:  # Less than 30 days old
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"Email domain only {transaction.email_domain_age_days} days old",
                    score=self.base_score,
                    confidence=0.76
                )
        return None

class UnverifiedPhoneRule(FraudRule):
    """Rule 36: Unverified Phone - Transaction from unverified phone"""

    def __init__(self):
        super().__init__(
            name="unverified_phone",
            description="Transaction from unverified phone number",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )

    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if not transaction.phone_verified:
            if transaction.amount > 100000:  # Large transaction from unverified phone
                return FraudFlag(
                    type=self.name,
                    severity=self.severity,
                    message=f"₦{transaction.amount:,.0f} transaction from unverified phone number",
                    score=self.base_score,
                    confidence=0.79
                )
        return None

class EmailFraudLinkageRule(FraudRule):
    """Rule 62: Email Fraud Linkage"""
    def __init__(self):
        super().__init__(
            name="email_fraud_linkage",
            description="Email linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shared_email_with_fraud:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="Email linked to fraud accounts")
        return None

class PhoneFraudLinkageRule(FraudRule):
    """Rule 63: Phone Fraud Linkage"""
    def __init__(self):
        super().__init__(
            name="phone_fraud_linkage",
            description="Phone linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace", "gaming"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.shared_phone_with_fraud:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="Phone linked to fraud accounts")
        return None

class IllegalEmailDomainRule(FraudRule):
    """Rule 67: Illegitimate Email Domain"""
    def __init__(self):
        super().__init__(
            name="illegitimate_email_domain",
            description="Email domain lacks legitimacy",
            base_score=25,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.email_domain_legitimacy and transaction.email_domain_legitimacy < 20:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.79, message="Domain legitimacy score low")
        return None

class HighRiskPhoneCarrierRule(FraudRule):
    """Rule 68: High-Risk Phone Carrier"""
    def __init__(self):
        super().__init__(
            name="high_risk_phone_carrier",
            description="Phone from high-risk carrier",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.phone_carrier_risk and transaction.phone_carrier_risk > 70:
            return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.76, message="Phone carrier flagged as high-risk")
        return None

class BVNFraudMatchRule(FraudRule):
    """Rule 69: BVN Fraud Match"""
    def __init__(self):
        super().__init__(
            name="bvn_fraud_match",
            description="BVN linked to fraud",
            base_score=45,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.bvn_fraud_match_count and transaction.bvn_fraud_match_count > 0:
            return FraudFlag(type=self.name, severity=self.severity, score=40 + min(transaction.bvn_fraud_match_count * 2, 20), confidence=0.94, message=f"BVN linked to {transaction.bvn_fraud_match_count} fraud cases")
        return None

class EmailReputationRule(FraudRule):
    """Rule: Low email reputation"""
    def __init__(self):
        super().__init__(
            name="email_reputation_low",
            description="Low email reputation score",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.email:
            if transaction.identity_features.email.reputation_score and transaction.identity_features.email.reputation_score < 40:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.70, message="Poor email reputation")
        return None

class PhoneAgeRule(FraudRule):
    """Rule: New phone number"""
    def __init__(self):
        super().__init__(
            name="phone_age_new",
            description="Brand new phone number",
            base_score=22,
            severity="medium",
            verticals=["lending", "fintech", "payments", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.phone:
            if transaction.identity_features.phone.age_days and transaction.identity_features.phone.age_days < 7:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.72, message="Phone number <7 days old")
        return None

class PhoneCarrierRiskRule(FraudRule):
    """Rule: High-risk phone carrier"""
    def __init__(self):
        super().__init__(
            name="phone_carrier_risk",
            description="Phone carrier high risk",
            base_score=18,
            severity="medium",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.phone:
            if transaction.identity_features.phone.carrier_risk and transaction.identity_features.phone.carrier_risk > 70:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.65, message="High-risk phone carrier")
        return None

class UnverifiedPhoneIdentityRule(FraudRule):
    """Rule: Unverified phone in identity"""
    def __init__(self):
        super().__init__(
            name="phone_unverified_identity",
            description="Phone not verified",
            base_score=20,
            severity="medium",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.phone:
            if not transaction.identity_features.phone.verification_status:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.68, message="Phone not verified")
        return None

class BVNFraudHistoryRule(FraudRule):
    """Rule: BVN linked to fraud"""
    def __init__(self):
        super().__init__(
            name="bvn_fraud_linked",
            description="BVN linked to fraud accounts",
            base_score=45,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.identity_features and transaction.identity_features.bvn:
            if transaction.identity_features.bvn.verification_status is False:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.85, message="BVN not verified or linked to fraud")
        return None

class NetworkEmailFraudLinkRule(FraudRule):
    """Rule: Email linked to fraud"""
    def __init__(self):
        super().__init__(
            name="email_fraud_link",
            description="Email linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "crypto", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.email_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Email linked to fraud accounts")
        return None

class NetworkPhoneFraudLinkRule(FraudRule):
    """Rule: Phone linked to fraud"""
    def __init__(self):
        super().__init__(
            name="phone_fraud_link",
            description="Phone linked to fraud accounts",
            base_score=40,
            severity="critical",
            verticals=["lending", "fintech", "payments", "ecommerce", "betting", "marketplace"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.phone_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.90, message="Phone linked to fraud accounts")
        return None

class NetworkBVNFraudLinkRule(FraudRule):
    """Rule: BVN linked to fraud"""
    def __init__(self):
        super().__init__(
            name="bvn_fraud_link",
            description="BVN linked to fraud accounts",
            base_score=42,
            severity="critical",
            verticals=["lending", "fintech", "payments", "betting"]
        )
    def check(self, transaction: TransactionCheckRequest, context: Dict[str, Any]) -> Optional[FraudFlag]:
        if transaction.network_features and transaction.network_features.fraud_linkage:
            if transaction.network_features.fraud_linkage.bvn_linked_to_fraud:
                return FraudFlag(type=self.name, severity=self.severity, score=self.base_score, confidence=0.92, message="BVN linked to fraud accounts")
        return None

# Export all identity rules
IDENTITY_RULES = [
    DisposableEmailRule(),
    SequentialApplicationsRule(),
    EmailDomainLegitimacyRule(),
    EmailVerificationMismatchRule(),
    PhoneVerificationFailureRule(),
    PhoneCountryMismatchRule(),
    BVNAgeInconsistencyRule(),
    MultipleEmailsDeviceRule(),
    BankAccountVerificationFailRule(),
    ConsortiumEmailFrequencyRule(),
    ConsortiumPhoneFrequencyRule(),
    ConsortiumBVNFrequencyRule(),
    NetworkVelocityEmailRule(),
    NetworkVelocityPhoneRule(),
    EmailFraudHistoryRule(),
    PhoneFraudHistoryRule(),
    EmailSimilarityHighRule(),
    EmailDomainAgeRule(),
    UnverifiedPhoneRule(),
    EmailFraudLinkageRule(),
    PhoneFraudLinkageRule(),
    IllegalEmailDomainRule(),
    HighRiskPhoneCarrierRule(),
    BVNFraudMatchRule(),
    EmailReputationRule(),
    PhoneAgeRule(),
    PhoneCarrierRiskRule(),
    UnverifiedPhoneIdentityRule(),
    BVNFraudHistoryRule(),
    NetworkEmailFraudLinkRule(),
    NetworkPhoneFraudLinkRule(),
    NetworkBVNFraudLinkRule(),
]
