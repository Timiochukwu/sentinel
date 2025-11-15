"""Machine Learning and Continuous Learning Service"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from app.models.database import RuleAccuracy, Transaction
from decimal import Decimal


class LearningService:
    """
    Continuous learning service that tracks rule accuracy and adjusts weights

    This service implements the feedback loop to improve fraud detection over time.
    """

    def __init__(self, db: Session):
        self.db = db

    def process_feedback(
        self,
        transaction_id: str,
        actual_outcome: str,
        fraud_type: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Process feedback about a transaction's actual outcome

        Args:
            transaction_id: Transaction ID
            actual_outcome: "fraud" or "legitimate"
            fraud_type: Type of fraud if confirmed

        Returns:
            Dictionary with accuracy impact information
        """
        # Get the transaction
        transaction = self.db.query(Transaction).filter(
            Transaction.transaction_id == transaction_id
        ).first()

        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Update transaction with actual outcome
        transaction.is_fraud = (actual_outcome == "fraud")
        transaction.fraud_type = fraud_type

        # Get the flags that were triggered
        flags = transaction.flags or []

        # Update rule accuracy for each flag
        accuracy_updates = []

        for flag in flags:
            rule_name = flag.get("type")
            if not rule_name:
                continue

            # Get or create rule accuracy record
            rule_accuracy = self.db.query(RuleAccuracy).filter(
                RuleAccuracy.rule_name == rule_name
            ).first()

            if not rule_accuracy:
                rule_accuracy = RuleAccuracy(rule_name=rule_name)
                self.db.add(rule_accuracy)

            # Update statistics
            rule_accuracy.triggered_count += 1

            if actual_outcome == "fraud":
                # Rule correctly predicted fraud
                rule_accuracy.correct_predictions += 1
            else:
                # Rule incorrectly flagged as fraud (false positive)
                rule_accuracy.false_positives += 1

            # Recalculate metrics
            total = rule_accuracy.triggered_count
            correct = rule_accuracy.correct_predictions
            fp = rule_accuracy.false_positives

            # Accuracy = correct predictions / total predictions
            rule_accuracy.accuracy = Decimal(correct / total) if total > 0 else Decimal(0)

            # Precision = correct / (correct + false positives)
            rule_accuracy.precision = Decimal(correct / (correct + fp)) if (correct + fp) > 0 else Decimal(0)

            # Adjust weight based on accuracy
            if rule_accuracy.accuracy >= Decimal("0.80"):
                # High accuracy - increase trust
                rule_accuracy.current_weight = min(Decimal("1.5"), rule_accuracy.current_weight + Decimal("0.1"))
            elif rule_accuracy.accuracy < Decimal("0.60"):
                # Low accuracy - decrease trust
                rule_accuracy.current_weight = max(Decimal("0.5"), rule_accuracy.current_weight - Decimal("0.1"))

            accuracy_updates.append({
                "rule": rule_name,
                "accuracy": float(rule_accuracy.accuracy),
                "weight": float(rule_accuracy.current_weight)
            })

        # Also check for false negatives (fraud that wasn't caught)
        if actual_outcome == "fraud" and transaction.risk_level == "low":
            # This is a false negative - fraud that we missed
            # We should track this but it's harder to attribute to specific rules
            pass

        self.db.commit()

        return {
            "updated_rules": accuracy_updates,
            "total_feedback_count": self.get_total_feedback_count()
        }

    def get_total_feedback_count(self) -> int:
        """Get total number of feedback submissions"""
        return self.db.query(Transaction).filter(
            Transaction.is_fraud.isnot(None)
        ).count()

    def get_rule_accuracy(self, rule_name: str) -> Optional[Dict]:
        """Get accuracy metrics for a specific rule"""
        rule_accuracy = self.db.query(RuleAccuracy).filter(
            RuleAccuracy.rule_name == rule_name
        ).first()

        if not rule_accuracy:
            return None

        return {
            "rule_name": rule_accuracy.rule_name,
            "triggered_count": rule_accuracy.triggered_count,
            "correct_predictions": rule_accuracy.correct_predictions,
            "false_positives": rule_accuracy.false_positives,
            "accuracy": float(rule_accuracy.accuracy),
            "precision": float(rule_accuracy.precision),
            "current_weight": float(rule_accuracy.current_weight)
        }

    def get_all_rule_accuracies(self) -> list:
        """Get accuracy metrics for all rules"""
        rules = self.db.query(RuleAccuracy).all()

        return [
            {
                "rule_name": rule.rule_name,
                "triggered_count": rule.triggered_count,
                "accuracy": float(rule.accuracy),
                "precision": float(rule.precision),
                "current_weight": float(rule.current_weight)
            }
            for rule in rules
        ]

    def calculate_overall_accuracy(self, client_id: Optional[str] = None) -> Dict:
        """
        Calculate overall fraud detection accuracy

        Args:
            client_id: Optional client ID to filter by

        Returns:
            Dictionary with overall metrics
        """
        query = self.db.query(Transaction).filter(
            Transaction.is_fraud.isnot(None)  # Only transactions with feedback
        )

        if client_id:
            query = query.filter(Transaction.client_id == client_id)

        transactions = query.all()

        if not transactions:
            return {
                "total_transactions": 0,
                "accuracy": 0,
                "precision": 0,
                "recall": 0,
                "false_positive_rate": 0
            }

        total = len(transactions)
        true_positives = 0  # Correctly identified fraud
        false_positives = 0  # Incorrectly flagged as fraud
        true_negatives = 0  # Correctly identified as legitimate
        false_negatives = 0  # Missed fraud

        for txn in transactions:
            predicted_fraud = txn.risk_level in ["high", "medium"]
            actual_fraud = txn.is_fraud

            if predicted_fraud and actual_fraud:
                true_positives += 1
            elif predicted_fraud and not actual_fraud:
                false_positives += 1
            elif not predicted_fraud and not actual_fraud:
                true_negatives += 1
            elif not predicted_fraud and actual_fraud:
                false_negatives += 1

        # Calculate metrics
        accuracy = (true_positives + true_negatives) / total if total > 0 else 0

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0

        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0

        false_positive_rate = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0

        return {
            "total_transactions": total,
            "accuracy": round(accuracy, 4),
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "false_positive_rate": round(false_positive_rate, 4),
            "true_positives": true_positives,
            "false_positives": false_positives,
            "true_negatives": true_negatives,
            "false_negatives": false_negatives
        }
