#!/usr/bin/env python
"""
Train XGBoost fraud detection model

Usage:
    python scripts/ml/train_model.py

This script:
1. Loads transaction data from database
2. Engineers features
3. Trains XGBoost model
4. Evaluates performance
5. Saves model to models/fraud_model.json
"""

import sys
from pathlib import Path
import pickle
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, precision_recall_curve

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from app.core.config import settings


def load_data():
    """Load transaction data from database"""
    print("📊 Loading transaction data from database...")

    engine = create_engine(settings.DATABASE_URL)

    query = """
    SELECT
        t.*,
        CASE WHEN t.is_fraud = true THEN 1 ELSE 0 END as label
    FROM transactions t
    WHERE t.is_fraud IS NOT NULL  -- Only labeled data
    ORDER BY t.created_at DESC
    LIMIT 10000  -- Adjust based on available data
    """

    df = pd.read_sql(query, engine)

    print(f"✅ Loaded {len(df)} transactions")
    print(f"   Fraud cases: {df['label'].sum()} ({df['label'].mean()*100:.2f}%)")

    return df


def engineer_features(df):
    """Engineer features for ML model"""
    print("🔧 Engineering features...")

    features = pd.DataFrame()

    # Amount features
    features['amount'] = df['amount']
    features['amount_log'] = np.log1p(df['amount'])
    features['amount_sqrt'] = np.sqrt(df['amount'])

    # Account age features
    features['account_age_days'] = df['account_age_days'].fillna(0)
    features['account_age_log'] = np.log1p(df['account_age_days'].fillna(1))
    features['is_new_account'] = (df['account_age_days'].fillna(0) < 7).astype(int)
    features['is_very_new_account'] = (df['account_age_days'].fillna(0) < 3).astype(int)

    # Transaction history
    features['transaction_count'] = df['transaction_count'].fillna(0)
    features['transaction_count_log'] = np.log1p(df['transaction_count'].fillna(0))

    # Contact changes
    features['phone_changed_recently'] = df['phone_changed_recently'].fillna(False).astype(int)
    features['email_changed_recently'] = df['email_changed_recently'].fillna(False).astype(int)
    features['any_contact_changed'] = (
        features['phone_changed_recently'] | features['email_changed_recently']
    ).astype(int)

    # Temporal features
    df['created_at'] = pd.to_datetime(df['created_at'])
    features['hour_of_day'] = df['created_at'].dt.hour
    features['day_of_week'] = df['created_at'].dt.dayofweek
    features['is_weekend'] = (df['created_at'].dt.dayofweek >= 5).astype(int)
    features['is_night'] = ((df['created_at'].dt.hour >= 2) & (df['created_at'].dt.hour <= 5)).astype(int)
    features['is_business_hours'] = ((df['created_at'].dt.hour >= 9) & (df['created_at'].dt.hour <= 17)).astype(int)

    # Risk score features
    features['risk_score'] = df['risk_score'].fillna(0)
    features['risk_score_normalized'] = features['risk_score'] / 100.0

    # Derived features
    features['transactions_per_day'] = np.where(
        df['account_age_days'] > 0,
        df['transaction_count'] / df['account_age_days'],
        0
    )

    features['amount_per_transaction'] = np.where(
        df['transaction_count'] > 0,
        df['amount'] / df['transaction_count'],
        df['amount']
    )

    # Round amount detection
    round_amounts = [50000, 100000, 200000, 500000, 1000000]
    features['is_round_amount'] = df['amount'].isin(round_amounts).astype(int)

    print(f"✅ Engineered {len(features.columns)} features")

    return features


def train_model(X_train, y_train, X_val, y_val):
    """Train XGBoost model"""
    print("🚀 Training XGBoost model...")

    # Create DMatrix
    dtrain = xgb.DMatrix(X_train, label=y_train, feature_names=list(X_train.columns))
    dval = xgb.DMatrix(X_val, label=y_val, feature_names=list(X_train.columns))

    # Parameters
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'learning_rate': 0.1,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 1,
        'seed': 42
    }

    # Train with early stopping
    evals = [(dtrain, 'train'), (dval, 'val')]
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=1000,
        evals=evals,
        early_stopping_rounds=50,
        verbose_eval=50
    )

    print(f"✅ Training completed (best iteration: {model.best_iteration})")

    return model


def evaluate_model(model, X_test, y_test):
    """Evaluate model performance"""
    print("\n📈 Evaluating model performance...")

    dtest = xgb.DMatrix(X_test, feature_names=list(X_test.columns))

    # Predictions
    y_pred_proba = model.predict(dtest)
    y_pred = (y_pred_proba >= 0.5).astype(int)

    # Metrics
    auc_score = roc_auc_score(y_test, y_pred_proba)

    print(f"\n🎯 Model Performance:")
    print(f"   AUC-ROC: {auc_score:.4f}")
    print(f"\n{classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud'])}")

    # Precision-Recall at different thresholds
    precision, recall, thresholds = precision_recall_curve(y_test, y_pred_proba)

    print("\n📊 Precision-Recall at different thresholds:")
    for threshold in [0.3, 0.5, 0.7, 0.9]:
        idx = (np.abs(thresholds - threshold)).argmin()
        print(f"   Threshold {threshold:.1f}: Precision={precision[idx]:.3f}, Recall={recall[idx]:.3f}")

    # Feature importance
    importance = model.get_score(importance_type='gain')
    importance_df = pd.DataFrame([
        {'feature': k, 'gain': v}
        for k, v in importance.items()
    ]).sort_values('gain', ascending=False)

    print("\n🔝 Top 10 Most Important Features:")
    print(importance_df.head(10).to_string(index=False))

    return {
        'auc_score': auc_score,
        'feature_importance': importance
    }


def save_model(model, scaler, feature_names, output_dir='models'):
    """Save trained model"""
    print(f"\n💾 Saving model to {output_dir}/...")

    Path(output_dir).mkdir(exist_ok=True)

    # Save XGBoost model
    model_path = f"{output_dir}/fraud_model.json"
    model.save_model(model_path)
    print(f"   ✅ Model saved to {model_path}")

    # Save scaler
    scaler_path = f"{output_dir}/fraud_model_scaler.pkl"
    with open(scaler_path, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"   ✅ Scaler saved to {scaler_path}")

    # Save feature names
    features_path = f"{output_dir}/fraud_model_features.pkl"
    with open(features_path, 'wb') as f:
        pickle.dump(feature_names, f)
    print(f"   ✅ Feature names saved to {features_path}")


def main():
    """Main training pipeline"""
    print("=" * 70)
    print("🤖 Sentinel Fraud Detection - Model Training")
    print("=" * 70)

    # Load data
    df = load_data()

    if len(df) < 100:
        print("❌ Not enough data to train model. Need at least 100 labeled transactions.")
        print("   Run the system for a while and collect feedback before training.")
        return

    # Engineer features
    X = engineer_features(df)
    y = df['label']

    # Split data
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.5, random_state=42, stratify=y_temp
    )

    print(f"\n📦 Dataset split:")
    print(f"   Training: {len(X_train)} samples")
    print(f"   Validation: {len(X_val)} samples")
    print(f"   Test: {len(X_test)} samples")

    # Scale features
    print("\n🔢 Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index
    )
    X_val_scaled = pd.DataFrame(
        scaler.transform(X_val),
        columns=X_val.columns,
        index=X_val.index
    )
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=X_test.columns,
        index=X_test.index
    )

    # Train model
    model = train_model(X_train_scaled, y_train, X_val_scaled, y_val)

    # Evaluate
    metrics = evaluate_model(model, X_test_scaled, y_test)

    # Save model
    save_model(model, scaler, list(X.columns))

    print("\n" + "=" * 70)
    print("✅ Model training completed successfully!")
    print("=" * 70)
    print(f"\n📊 Final AUC Score: {metrics['auc_score']:.4f}")
    print("\n🚀 Model is ready to use in production!")
    print("   The fraud detector will automatically load it on startup.")


if __name__ == "__main__":
    main()
