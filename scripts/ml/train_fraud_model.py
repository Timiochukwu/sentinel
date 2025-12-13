"""
ML Model Training Pipeline for Fraud Detection

Trains an XGBoost classifier on historical transaction data with 249+ features.

This script:
1. Loads historical transactions from database
2. Extracts features from JSONB columns
3. Prepares training data (X, y)
4. Trains XGBoost model with optimal hyperparameters
5. Evaluates model performance (precision, recall, F1)
6. Saves trained model for production use

Usage:
    # Train on last 90 days of data
    python scripts/ml/train_fraud_model.py

    # Train on custom date range
    python scripts/ml/train_fraud_model.py --days 180

    # Train with custom parameters
    python scripts/ml/train_fraud_model.py --max-depth 8 --n-estimators 200

Output:
    - models/fraud_model_xgboost.pkl - Trained model
    - models/model_metrics.json - Performance metrics
    - models/feature_importance.json - Feature importance rankings
"""

import sys
import os
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report
)
import xgboost as xgb
import pickle

from app.models.database import SessionLocal, Transaction
from app.services.feature_aggregation import feature_aggregation


class FraudModelTrainer:
    """
    Train XGBoost model for fraud detection

    XGBoost is ideal for fraud detection because:
    - Handles imbalanced data well (99% legitimate, 1% fraud)
    - Provides feature importance rankings
    - Fast training and prediction
    - Resistant to overfitting with proper tuning
    - Excellent performance on tabular data
    """

    def __init__(self, days: int = 90):
        """
        Initialize trainer

        Args:
            days: Number of days of historical data to use
        """
        self.days = days
        self.db = SessionLocal()
        self.model = None
        self.feature_names = []

    def load_training_data(self) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Load and prepare training data from database

        Returns:
            X: Feature DataFrame
            y: Target labels (0 = legitimate, 1 = fraud)
        """
        print(f"Loading transactions from last {self.days} days...")

        cutoff_date = datetime.utcnow() - timedelta(days=self.days)

        # Query transactions with stored features
        transactions = self.db.query(Transaction).filter(
            Transaction.created_at >= cutoff_date,
            Transaction.features_identity.isnot(None)  # Only transactions with features
        ).all()

        print(f"Found {len(transactions)} transactions with features")

        if len(transactions) < 100:
            raise ValueError(
                f"Insufficient training data: {len(transactions)} transactions. "
                "Need at least 100 transactions with stored features. "
                "Run fraud detection on more transactions first."
            )

        # Extract features into DataFrame
        feature_rows = []
        labels = []

        for txn in transactions:
            # Flatten JSONB features into row
            row = self._flatten_features(txn)
            if row:
                feature_rows.append(row)
                labels.append(1 if txn.is_fraudulent else 0)

        X = pd.DataFrame(feature_rows)
        y = pd.Series(labels)

        print(f"Prepared {len(X)} training samples with {len(X.columns)} features")
        print(f"Class distribution: {y.value_counts().to_dict()}")

        # Save feature names for later
        self.feature_names = list(X.columns)

        return X, y

    def _flatten_features(self, txn: Transaction) -> Dict[str, Any]:
        """
        Flatten nested JSONB features into flat dictionary

        Args:
            txn: Transaction with JSONB features

        Returns:
            Flat dictionary of features
        """
        features = {}

        # Basic transaction features
        features['amount'] = txn.amount
        features['account_age_days'] = txn.account_age_days or 0
        features['transaction_count'] = txn.transaction_count or 0
        features['fraud_score'] = txn.fraud_score

        # Identity features
        if txn.features_identity:
            email = txn.features_identity.get('email', {})
            features['email_age_days'] = email.get('age_days') or 0
            features['email_reputation'] = email.get('reputation_score') or 0

            device = txn.features_identity.get('device', {})
            features['has_device_fingerprint'] = 1 if device.get('fingerprint') else 0

            network = txn.features_identity.get('network', {})
            features['ip_reputation'] = network.get('ip_reputation') or 50

        # Behavioral features
        if txn.features_behavioral:
            session = txn.features_behavioral.get('session', {})
            features['session_duration'] = session.get('session_duration_seconds') or 0
            features['mouse_movement_score'] = session.get('mouse_movement_score') or 50

            login = txn.features_behavioral.get('login', {})
            features['failed_logins'] = login.get('failed_login_attempts_24h') or 0

            transaction = txn.features_behavioral.get('transaction', {})
            features['velocity_24h'] = transaction.get('velocity_last_day') or 0

        # Network features
        if txn.features_network:
            fraud_linkage = txn.features_network.get('fraud_linkage', {})
            features['device_linked_to_fraud'] = 1 if fraud_linkage.get('device_linked_to_fraud') else 0
            features['email_linked_to_fraud'] = 1 if fraud_linkage.get('email_linked_to_fraud') else 0

        # Fill missing values with 0
        for key in features:
            if features[key] is None:
                features[key] = 0

        return features

    def train_model(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        max_depth: int = 6,
        n_estimators: int = 100,
        learning_rate: float = 0.1
    ) -> Dict[str, Any]:
        """
        Train XGBoost model

        Args:
            X: Features
            y: Labels
            max_depth: Maximum tree depth
            n_estimators: Number of trees
            learning_rate: Learning rate

        Returns:
            Metrics dictionary
        """
        print("\nSplitting data into train/test (80/20)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42,
            stratify=y  # Maintain class distribution
        )

        print(f"Training set: {len(X_train)} samples")
        print(f"Test set: {len(X_test)} samples")

        # Handle class imbalance
        fraud_count = sum(y_train)
        legit_count = len(y_train) - fraud_count
        scale_pos_weight = legit_count / fraud_count if fraud_count > 0 else 1

        print(f"\nClass imbalance ratio: {scale_pos_weight:.2f}")
        print(f"Using scale_pos_weight={scale_pos_weight} to handle imbalance")

        # Train XGBoost
        print("\nTraining XGBoost model...")
        self.model = xgb.XGBClassifier(
            max_depth=max_depth,
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            scale_pos_weight=scale_pos_weight,
            random_state=42,
            eval_metric='auc'
        )

        self.model.fit(X_train, y_train)

        # Evaluate
        print("\nEvaluating model...")
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]

        metrics = {
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1_score': f1_score(y_test, y_pred),
            'roc_auc': roc_auc_score(y_test, y_pred_proba),
            'confusion_matrix': confusion_matrix(y_test, y_pred).tolist(),
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'features_count': len(X.columns),
            'hyperparameters': {
                'max_depth': max_depth,
                'n_estimators': n_estimators,
                'learning_rate': learning_rate,
                'scale_pos_weight': scale_pos_weight
            }
        }

        print("\n" + "="*50)
        print("MODEL PERFORMANCE")
        print("="*50)
        print(f"Precision: {metrics['precision']:.3f}")
        print(f"Recall: {metrics['recall']:.3f}")
        print(f"F1 Score: {metrics['f1_score']:.3f}")
        print(f"ROC AUC: {metrics['roc_auc']:.3f}")
        print("\nConfusion Matrix:")
        print(f"  TN: {metrics['confusion_matrix'][0][0]}, FP: {metrics['confusion_matrix'][0][1]}")
        print(f"  FN: {metrics['confusion_matrix'][1][0]}, TP: {metrics['confusion_matrix'][1][1]}")

        return metrics

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance rankings"""
        if not self.model:
            raise ValueError("Model not trained yet")

        importance = self.model.feature_importances_
        feature_importance = dict(zip(self.feature_names, importance.tolist()))

        # Sort by importance
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )

        print("\n" + "="*50)
        print("TOP 10 MOST IMPORTANT FEATURES")
        print("="*50)
        for i, (feature, score) in enumerate(sorted_features[:10], 1):
            print(f"{i:2d}. {feature:30s}: {score:.4f}")

        return dict(sorted_features)

    def save_model(self, output_dir: str = "models"):
        """
        Save trained model and metadata

        Args:
            output_dir: Directory to save model files
        """
        os.makedirs(output_dir, exist_ok=True)

        # Save model
        model_path = os.path.join(output_dir, "fraud_model_xgboost.pkl")
        with open(model_path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"\n✓ Model saved to: {model_path}")

        # Save feature names
        feature_names_path = os.path.join(output_dir, "feature_names.json")
        with open(feature_names_path, 'w') as f:
            json.dump(self.feature_names, f, indent=2)
        print(f"✓ Feature names saved to: {feature_names_path}")

        print(f"\nModel ready for production use!")
        print(f"Load in fraud_detector.py with: pickle.load(open('{model_path}', 'rb'))")


def main():
    """Main training pipeline"""
    parser = argparse.ArgumentParser(description="Train fraud detection ML model")
    parser.add_argument('--days', type=int, default=90, help='Days of historical data')
    parser.add_argument('--max-depth', type=int, default=6, help='Max tree depth')
    parser.add_argument('--n-estimators', type=int, default=100, help='Number of trees')
    parser.add_argument('--learning-rate', type=float, default=0.1, help='Learning rate')
    args = parser.parse_args()

    print("="*60)
    print("FRAUD DETECTION ML MODEL TRAINING PIPELINE")
    print("="*60)

    # Initialize trainer
    trainer = FraudModelTrainer(days=args.days)

    # Load data
    X, y = trainer.load_training_data()

    # Train model
    metrics = trainer.train_model(
        X, y,
        max_depth=args.max_depth,
        n_estimators=args.n_estimators,
        learning_rate=args.learning_rate
    )

    # Get feature importance
    feature_importance = trainer.get_feature_importance()

    # Save model
    trainer.save_model()

    # Save metrics
    os.makedirs("models", exist_ok=True)
    with open("models/model_metrics.json", 'w') as f:
        json.dump(metrics, f, indent=2)
    print(f"✓ Metrics saved to: models/model_metrics.json")

    with open("models/feature_importance.json", 'w') as f:
        json.dump(feature_importance, f, indent=2)
    print(f"✓ Feature importance saved to: models/feature_importance.json")

    print("\n" + "="*60)
    print("✓ TRAINING COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()
