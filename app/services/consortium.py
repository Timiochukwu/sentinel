"""Consortium Intelligence Service - Privacy-preserving cross-lender fraud detection"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.database import ConsortiumIntelligence, Transaction
from app.core.security import hash_device_id, hash_bvn, hash_phone, hash_email
from app.models.schemas import TransactionCheckRequest


class ConsortiumService:
    """
    Consortium Intelligence Service

    Detects fraud patterns across multiple lenders while preserving privacy.
    Uses SHA-256 hashing to store device/BVN/phone identifiers without exposing raw PII.
    """

    def __init__(self, db: Session, client_id: str):
        self.db = db
        self.client_id = client_id

    def check_fraud_patterns(
        self,
        transaction: TransactionCheckRequest
    ) -> Dict[str, Any]:
        """
        Check if this transaction matches known fraud patterns across lenders

        Args:
            transaction: Transaction data to check

        Returns:
            Dictionary with consortium intelligence data
        """
        results = {
            "client_count": 0,
            "fraud_count": 0,
            "lenders": [],
            "fraud_types": [],
            "total_amount_involved": 0,
            "risk_level": "none",
            "alerts": []
        }

        # Hash identifiers for privacy-preserving lookup
        device_hash = hash_device_id(transaction.device_id) if transaction.device_id else None
        bvn_hash = hash_bvn(transaction.bvn) if transaction.bvn else None
        phone_hash = hash_phone(transaction.phone) if transaction.phone else None
        email_hash = hash_email(transaction.email) if transaction.email else None

        # Check consortium database for matches
        matches = []

        if device_hash:
            match = self.db.query(ConsortiumIntelligence).filter(
                ConsortiumIntelligence.device_hash == device_hash
            ).first()
            if match:
                matches.append(match)

        if bvn_hash:
            match = self.db.query(ConsortiumIntelligence).filter(
                ConsortiumIntelligence.bvn_hash == bvn_hash
            ).first()
            if match:
                matches.append(match)

        if phone_hash:
            match = self.db.query(ConsortiumIntelligence).filter(
                ConsortiumIntelligence.phone_hash == phone_hash
            ).first()
            if match:
                matches.append(match)

        if email_hash:
            match = self.db.query(ConsortiumIntelligence).filter(
                ConsortiumIntelligence.email_hash == email_hash
            ).first()
            if match:
                matches.append(match)

        # Process matches
        if matches:
            # Deduplicate matches
            unique_matches = {match.id: match for match in matches}

            for match in unique_matches.values():
                results["client_count"] = max(results["client_count"], match.client_count)
                results["fraud_count"] += match.fraud_count

                if match.fraud_types:
                    results["fraud_types"].extend(match.fraud_types)

                results["total_amount_involved"] += float(match.total_amount_involved or 0)
                results["risk_level"] = match.risk_level or "none"

        # Generate alerts based on findings
        if results["client_count"] >= 3:
            results["alerts"].append(
                f"⚠️ LOAN STACKING: Applied to {results['client_count']} other lenders this week"
            )

        if results["fraud_count"] >= 2:
            results["alerts"].append(
                f"🚨 KNOWN FRAUDSTER: Flagged {results['fraud_count']} times by other lenders"
            )

        if results["total_amount_involved"] > 1000000:  # ₦1M
            results["alerts"].append(
                f"💰 HIGH EXPOSURE: Involved in ₦{results['total_amount_involved']:,.0f} of fraud across platform"
            )

        # Deduplicate fraud types
        results["fraud_types"] = list(set(results["fraud_types"]))

        return results

    def report_fraud(
        self,
        transaction: TransactionCheckRequest,
        fraud_type: str,
        amount: float
    ) -> None:
        """
        Report confirmed fraud to consortium database

        Args:
            transaction: Transaction data
            fraud_type: Type of fraud detected
            amount: Amount involved
        """
        # Hash identifiers
        device_hash = hash_device_id(transaction.device_id) if transaction.device_id else None
        bvn_hash = hash_bvn(transaction.bvn) if transaction.bvn else None
        phone_hash = hash_phone(transaction.phone) if transaction.phone else None
        email_hash = hash_email(transaction.email) if transaction.email else None

        # Update or create consortium intelligence record for each identifier
        if device_hash:
            self._update_consortium_record(
                device_hash=device_hash,
                fraud_type=fraud_type,
                amount=amount
            )

        if bvn_hash:
            self._update_consortium_record(
                bvn_hash=bvn_hash,
                fraud_type=fraud_type,
                amount=amount
            )

        if phone_hash:
            self._update_consortium_record(
                phone_hash=phone_hash,
                fraud_type=fraud_type,
                amount=amount
            )

        if email_hash:
            self._update_consortium_record(
                email_hash=email_hash,
                fraud_type=fraud_type,
                amount=amount
            )

        self.db.commit()

    def _update_consortium_record(
        self,
        device_hash: Optional[str] = None,
        bvn_hash: Optional[str] = None,
        phone_hash: Optional[str] = None,
        email_hash: Optional[str] = None,
        fraud_type: str = None,
        amount: float = 0
    ) -> None:
        """Update or create a consortium intelligence record"""

        # Find existing record
        query = self.db.query(ConsortiumIntelligence)

        if device_hash:
            record = query.filter(ConsortiumIntelligence.device_hash == device_hash).first()
        elif bvn_hash:
            record = query.filter(ConsortiumIntelligence.bvn_hash == bvn_hash).first()
        elif phone_hash:
            record = query.filter(ConsortiumIntelligence.phone_hash == phone_hash).first()
        elif email_hash:
            record = query.filter(ConsortiumIntelligence.email_hash == email_hash).first()
        else:
            return

        if record:
            # Update existing record
            record.fraud_count += 1
            record.last_seen_at = datetime.utcnow()
            record.client_count += 1
            record.total_amount_involved = (record.total_amount_involved or 0) + amount

            # Update fraud types
            fraud_types = record.fraud_types or []
            if fraud_type and fraud_type not in fraud_types:
                fraud_types.append(fraud_type)
            record.fraud_types = fraud_types

            # Update risk level
            if record.fraud_count >= 5:
                record.risk_level = "critical"
            elif record.fraud_count >= 3:
                record.risk_level = "high"
            elif record.fraud_count >= 1:
                record.risk_level = "medium"

        else:
            # Create new record
            record = ConsortiumIntelligence(
                device_hash=device_hash,
                bvn_hash=bvn_hash,
                phone_hash=phone_hash,
                email_hash=email_hash,
                fraud_count=1,
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                client_count=1,
                fraud_types=[fraud_type] if fraud_type else [],
                total_amount_involved=amount,
                risk_level="medium"
            )
            self.db.add(record)

    def check_loan_stacking(
        self,
        transaction: TransactionCheckRequest,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        Check if user has applied to multiple lenders recently (loan stacking)

        Args:
            transaction: Transaction data
            days: Number of days to look back (default: 7)

        Returns:
            Dictionary with loan stacking information
        """
        # Hash identifiers
        device_hash = hash_device_id(transaction.device_id) if transaction.device_id else None
        bvn_hash = hash_bvn(transaction.bvn) if transaction.bvn else None
        phone_hash = hash_phone(transaction.phone) if transaction.phone else None

        # Query transactions from other clients in the last N days
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = self.db.query(Transaction).filter(
            Transaction.created_at >= cutoff_date,
            Transaction.client_id != self.client_id  # Exclude current client
        )

        # Check for matches on hashed identifiers
        matching_transactions = []

        if device_hash:
            matches = query.filter(Transaction.device_id == device_hash).all()
            matching_transactions.extend(matches)

        if bvn_hash:
            matches = query.filter(Transaction.bvn == bvn_hash).all()
            matching_transactions.extend(matches)

        if phone_hash:
            matches = query.filter(Transaction.phone == phone_hash).all()
            matching_transactions.extend(matches)

        # Get unique clients
        unique_clients = set(t.client_id for t in matching_transactions)

        return {
            "client_count": len(unique_clients),
            "lenders": list(unique_clients)[:5],  # Max 5 for privacy
            "application_count": len(matching_transactions),
            "days_checked": days
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get consortium intelligence statistics"""

        total_records = self.db.query(ConsortiumIntelligence).count()
        total_fraud_count = self.db.query(ConsortiumIntelligence.fraud_count).scalar() or 0

        critical_count = self.db.query(ConsortiumIntelligence).filter(
            ConsortiumIntelligence.risk_level == "critical"
        ).count()

        high_count = self.db.query(ConsortiumIntelligence).filter(
            ConsortiumIntelligence.risk_level == "high"
        ).count()

        return {
            "total_records": total_records,
            "total_fraud_incidents": total_fraud_count,
            "critical_threats": critical_count,
            "high_threats": high_count,
            "network_effect": f"{total_records:,} patterns shared across lenders"
        }
