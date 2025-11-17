"""
Device Fingerprint Fraud Detection Rules

This module implements fraud detection rules based on browser device fingerprinting.
It's specifically designed to catch loan stacking fraud in the Nigerian lending market.

What is Device Fingerprinting?
Device fingerprinting generates a unique identifier for each device by analyzing browser
and hardware characteristics (screen, canvas rendering, WebGL, fonts, etc.). Unlike
cookies or device IDs, fingerprints are:
- Stable across sessions (persist even in private browsing)
- Difficult to spoof without sophisticated tools
- Unique to each physical device

Why is this important for Nigerian lenders?
1. Loan Stacking: Fraudsters apply to multiple lenders from the same device using
   different identities (fake BVN, phone numbers, etc.)
2. High-Velocity Attacks: Automated bots submit many applications quickly
3. Known Fraudsters: Devices linked to confirmed fraud cases try again with new identities
4. Consortium Intelligence: Detect when a device has been used at multiple lenders

Fraud Rules Implemented:
1. Multiple Users on Same Device - Detects loan stacking (Score: +60)
2. High Velocity - Detects automated attacks (Score: +40)
3. Fraud History - Detects known fraudster devices (Score: +80)
4. Consortium Detection - Detects cross-lender fraud (Score: +70)

All rules query the database for historical patterns and return fraud flags
with detailed explanations for customer service teams.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from app.models.database import Transaction


class FingerprintFraudRules:
    """
    Device fingerprint fraud detection rules

    This class encapsulates all fraud detection logic based on device fingerprints.
    Each method represents a specific fraud pattern we're looking for.

    Usage:
        detector = FingerprintFraudRules()
        flags = detector.check_fingerprint_fraud(
            fingerprint="abc123xyz",
            user_id="user_789",
            client_id="lender_1",
            db=database_session
        )

        # Returns list of fraud flags
        # Example: [
        #   {
        #     "type": "loan_stacking",
        #     "severity": "critical",
        #     "message": "Device used by 5 users in 7 days (loan stacking)",
        #     "score": 60,
        #     "metadata": {"user_count": 5, "fingerprint": "abc123xyz"}
        #   }
        # ]
    """

    def __init__(self):
        """Initialize the fingerprint fraud detector"""
        pass

    def check_fingerprint_fraud(
        self,
        fingerprint: str,
        user_id: str,
        client_id: str,
        db: Session,
        amount: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Check all fingerprint-based fraud rules

        This is the main entry point for fingerprint fraud detection.
        It runs all rules and returns a list of triggered fraud flags.

        Args:
            fingerprint: Device fingerprint hash from FingerprintJS
            user_id: Current user attempting transaction
            client_id: Lender/client ID
            db: SQLAlchemy database session
            amount: Transaction amount (optional, used for severity calculation)

        Returns:
            List of fraud flag dictionaries, each containing:
            - type: Machine-readable flag type (e.g., "loan_stacking")
            - severity: Human-readable severity (low, medium, high, critical)
            - message: Plain English explanation
            - score: Risk score contribution (0-100)
            - metadata: Additional context for debugging/analysis

        Example:
            flags = check_fingerprint_fraud(
                fingerprint="abc123xyz",
                user_id="user_789",
                client_id="lender_1",
                db=db_session,
                amount=500000
            )
        """

        # If no fingerprint provided, can't run these rules
        if not fingerprint or len(fingerprint) < 8:
            return []

        flags = []

        # Rule 1: Multiple users on same device (loan stacking)
        loan_stacking_flag = self._check_multiple_users_same_device(
            fingerprint, user_id, client_id, db, amount
        )
        if loan_stacking_flag:
            flags.append(loan_stacking_flag)

        # Rule 2: High velocity (automated fraud)
        velocity_flag = self._check_high_velocity(
            fingerprint, client_id, db
        )
        if velocity_flag:
            flags.append(velocity_flag)

        # Rule 3: Fraud history (known fraudster device)
        fraud_history_flag = self._check_fraud_history(
            fingerprint, db
        )
        if fraud_history_flag:
            flags.append(fraud_history_flag)

        # Rule 4: Consortium detection (same device at multiple lenders)
        consortium_flag = self._check_consortium_detection(
            fingerprint, client_id, db
        )
        if consortium_flag:
            flags.append(consortium_flag)

        return flags

    def _check_multiple_users_same_device(
        self,
        fingerprint: str,
        user_id: str,
        client_id: str,
        db: Session,
        amount: Optional[float] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Rule 1: Detect multiple users using the same device

        Loan Stacking Pattern:
        Fraudsters apply for loans from multiple lenders using the same device
        but different identities (fake BVN, phone numbers, email addresses).

        Detection Logic:
        - Query last 7 days of transactions with this fingerprint
        - Count distinct user_ids at this lender
        - If >= 3 different users → Likely loan stacking fraud

        Why 3 users?
        - 1 user = Normal (same person, same device)
        - 2 users = Could be legitimate (family sharing device)
        - 3+ users = Very suspicious (likely fraud ring)

        Args:
            fingerprint: Device fingerprint hash
            user_id: Current user
            client_id: Current lender
            db: Database session
            amount: Transaction amount (for severity calculation)

        Returns:
            Fraud flag dict if triggered, None otherwise
        """

        # Query last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        # Count distinct users with this fingerprint at this lender
        # Exclude current user (we only care about OTHER users)
        distinct_users = db.query(
            func.count(func.distinct(Transaction.user_id))
        ).filter(
            and_(
                Transaction.device_fingerprint == fingerprint,
                Transaction.client_id == client_id,
                Transaction.created_at >= seven_days_ago,
                Transaction.user_id != user_id  # Exclude current user
            )
        ).scalar()

        # Add 1 for current user to get total count
        total_user_count = distinct_users + 1

        # Trigger if 3 or more users
        if total_user_count >= 3:
            # Severity increases with more users
            if total_user_count >= 5:
                severity = "critical"
                score = 80
            elif total_user_count >= 4:
                severity = "high"
                score = 70
            else:  # 3 users
                severity = "high"
                score = 60

            return {
                "type": "loan_stacking",
                "severity": severity,
                "message": f"Device used by {total_user_count} users in 7 days (loan stacking)",
                "score": score,
                "confidence": 0.85,
                "metadata": {
                    "user_count": total_user_count,
                    "fingerprint": fingerprint,
                    "time_window": "7 days",
                    "pattern": "multiple_users_same_device"
                }
            }

        return None

    def _check_high_velocity(
        self,
        fingerprint: str,
        client_id: str,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Rule 2: Detect high-velocity automated fraud

        Automated Bot Pattern:
        Fraudsters use bots to submit many loan applications quickly from
        the same device, hoping at least one gets approved.

        Detection Logic:
        - Count transactions from this fingerprint TODAY
        - If > 5 transactions in one day → Likely bot attack

        Why 5 transactions?
        - Normal users: 1-2 applications per day (maybe retry after fixing info)
        - Fraudsters: 10+ applications with different identities
        - Threshold of 5 catches most bots while minimizing false positives

        Args:
            fingerprint: Device fingerprint hash
            client_id: Current lender
            db: Database session

        Returns:
            Fraud flag dict if triggered, None otherwise
        """

        # Get start of today (00:00:00 UTC)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        # Count transactions from this fingerprint today at this lender
        transaction_count = db.query(
            func.count(Transaction.id)
        ).filter(
            and_(
                Transaction.device_fingerprint == fingerprint,
                Transaction.client_id == client_id,
                Transaction.created_at >= today_start
            )
        ).scalar()

        # Add 1 for current transaction
        total_count = transaction_count + 1

        # Trigger if > 5 transactions today
        if total_count > 5:
            # Severity increases with more transactions
            if total_count > 20:
                severity = "critical"
                score = 60
            elif total_count > 10:
                severity = "high"
                score = 50
            else:  # 6-10 transactions
                severity = "medium"
                score = 40

            return {
                "type": "high_velocity_device",
                "severity": severity,
                "message": f"Device used for {total_count} applications today",
                "score": score,
                "confidence": 0.75,
                "metadata": {
                    "transaction_count": total_count,
                    "fingerprint": fingerprint,
                    "time_window": "today",
                    "pattern": "high_velocity_automated"
                }
            }

        return None

    def _check_fraud_history(
        self,
        fingerprint: str,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Rule 3: Detect devices with confirmed fraud history

        Known Fraudster Pattern:
        Once a device is linked to confirmed fraud (via feedback from lenders),
        any future applications from that device should be treated as high risk.

        Detection Logic:
        - Query ALL transactions with this fingerprint where is_fraud = True
        - If any confirmed fraud cases exist → Very high risk

        Why this is effective:
        - Fraudsters often reuse the same device with different identities
        - Once caught once, device fingerprint is permanently flagged
        - Even with new BVN/phone/email, the device gives them away

        Args:
            fingerprint: Device fingerprint hash
            db: Database session

        Returns:
            Fraud flag dict if triggered, None otherwise
        """

        # Count confirmed fraud cases from this fingerprint (across ALL lenders)
        fraud_count = db.query(
            func.count(Transaction.id)
        ).filter(
            and_(
                Transaction.device_fingerprint == fingerprint,
                Transaction.is_fraud == True  # Only confirmed fraud
            )
        ).scalar()

        # If any fraud history exists, flag it
        if fraud_count > 0:
            # Severity increases with more fraud cases
            if fraud_count >= 5:
                severity = "critical"
                score = 100  # Maximum risk
            elif fraud_count >= 3:
                severity = "critical"
                score = 90
            else:  # 1-2 cases
                severity = "critical"
                score = 80

            return {
                "type": "fraud_history_device",
                "severity": severity,
                "message": f"Device linked to {fraud_count} confirmed fraud cases",
                "score": score,
                "confidence": 0.95,  # Very high confidence
                "metadata": {
                    "fraud_count": fraud_count,
                    "fingerprint": fingerprint,
                    "pattern": "known_fraudster_device"
                }
            }

        return None

    def _check_consortium_detection(
        self,
        fingerprint: str,
        client_id: str,
        db: Session
    ) -> Optional[Dict[str, Any]]:
        """
        Rule 4: Detect same device at multiple lenders (consortium intelligence)

        Cross-Lender Loan Stacking:
        Fraudsters apply to multiple lenders simultaneously to maximize loan amounts
        before any single lender can detect the pattern.

        Detection Logic:
        - Query last 7 days for this fingerprint
        - Count distinct lenders (client_ids) excluding current lender
        - If device seen at other lenders → Consortium alert

        Why this is powerful:
        - Individual lenders can't see this pattern alone
        - Consortium sharing enables cross-lender fraud detection
        - This is Sentinel's unique competitive advantage!

        Args:
            fingerprint: Device fingerprint hash
            client_id: Current lender
            db: Database session

        Returns:
            Fraud flag dict if triggered, None otherwise
        """

        # Query last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)

        # Count distinct lenders (excluding current lender)
        other_lenders = db.query(
            func.count(func.distinct(Transaction.client_id))
        ).filter(
            and_(
                Transaction.device_fingerprint == fingerprint,
                Transaction.client_id != client_id,  # Exclude current lender
                Transaction.created_at >= seven_days_ago
            )
        ).scalar()

        # If device seen at other lenders, flag it
        if other_lenders > 0:
            # Severity increases with more lenders
            if other_lenders >= 5:
                severity = "critical"
                score = 90
            elif other_lenders >= 3:
                severity = "critical"
                score = 80
            else:  # 1-2 other lenders
                severity = "high"
                score = 70

            return {
                "type": "consortium_loan_stacking",
                "severity": severity,
                "message": f"Device seen at {other_lenders} other lenders this week",
                "score": score,
                "confidence": 0.85,
                "metadata": {
                    "lender_count": other_lenders,
                    "fingerprint": fingerprint,
                    "time_window": "7 days",
                    "pattern": "cross_lender_stacking"
                }
            }

        return None

    def get_fingerprint_analytics(
        self,
        fingerprint: str,
        db: Session
    ) -> Dict[str, Any]:
        """
        Get detailed analytics for a specific fingerprint

        This is useful for forensic analysis and understanding patterns.
        Returns comprehensive data about this fingerprint's history.

        Args:
            fingerprint: Device fingerprint hash
            db: Database session

        Returns:
            Dictionary with analytics:
            - total_transactions: Total number of transactions
            - unique_users: Number of distinct users
            - unique_lenders: Number of distinct lenders
            - fraud_count: Number of confirmed fraud cases
            - first_seen: Date of first transaction
            - last_seen: Date of last transaction
            - risk_assessment: Overall risk level (low, medium, high, critical)
        """

        # Get all transactions for this fingerprint
        transactions = db.query(Transaction).filter(
            Transaction.device_fingerprint == fingerprint
        ).all()

        if not transactions:
            return {
                "fingerprint": fingerprint,
                "total_transactions": 0,
                "unique_users": 0,
                "unique_lenders": 0,
                "fraud_count": 0,
                "risk_assessment": "unknown"
            }

        # Calculate analytics
        unique_users = len(set(t.user_id for t in transactions))
        unique_lenders = len(set(t.client_id for t in transactions))
        fraud_count = sum(1 for t in transactions if t.is_fraud is True)
        first_seen = min(t.created_at for t in transactions)
        last_seen = max(t.created_at for t in transactions)

        # Determine risk level
        if fraud_count > 0:
            risk = "critical"
        elif unique_users >= 5:
            risk = "critical"
        elif unique_users >= 3 or unique_lenders >= 3:
            risk = "high"
        elif unique_users >= 2 or unique_lenders >= 2:
            risk = "medium"
        else:
            risk = "low"

        return {
            "fingerprint": fingerprint,
            "total_transactions": len(transactions),
            "unique_users": unique_users,
            "unique_lenders": unique_lenders,
            "fraud_count": fraud_count,
            "first_seen": first_seen.isoformat() if first_seen else None,
            "last_seen": last_seen.isoformat() if last_seen else None,
            "risk_assessment": risk
        }
