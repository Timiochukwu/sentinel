# WEEK 1: XGBoost Training & Feature Engineering
**Days 85-91 | Month 4**

## Overview
This week implements XGBoost model training for fraud detection:
- Feature engineering pipeline
- XGBoost classifier training
- Model evaluation and metrics
- Feature importance analysis

## Files to Build

```
scripts/ml/
├── __init__.py
├── train_fraud_model.py          # 280 lines - XGBoost training
├── feature_engineering.py        # 195 lines - Feature engineering
└── model_evaluation.py            # 165 lines - Model evaluation

models/
└── README.md                      # Model documentation
```

**Total:** 5 files, ~640 lines

---

## Dependencies

```
# All previous dependencies from Month 3 +
scikit-learn==1.3.2
xgboost==2.0.3
numpy==1.26.2
pandas==2.1.4
joblib==1.3.2
matplotlib==3.8.2
seaborn==0.13.0
```

---

## File Details

### 1. `scripts/ml/train_fraud_model.py` (280 lines)

**Purpose:** Train XGBoost model for fraud detection

**Key Functions:**

```python
import xgboost as xgb
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

def load_training_data():
    """Load historical transactions from database"""
    from app.db.session import SessionLocal
    from app.models.database import Transaction, FraudFlag

    db = SessionLocal()

    # Get all transactions with fraud labels
    query = """
        SELECT
            t.amount,
            t.transaction_type,
            t.industry,
            t.fraud_score,
            t.status,
            t.metadata,
            CASE WHEN t.status = 'declined' THEN 1 ELSE 0 END as is_fraud
        FROM transactions t
        WHERE t.created_at >= NOW() - INTERVAL '90 days'
    """

    df = pd.read_sql(query, db.connection())
    return df

def engineer_features(df):
    """Engineer features from transaction data"""
    from scripts.ml.feature_engineering import FeatureEngineer

    engineer = FeatureEngineer()
    features = engineer.transform(df)

    return features

def train_xgboost_model():
    """Train XGBoost fraud detection model"""

    # Load data
    print("Loading training data...")
    df = load_training_data()
    print(f"Loaded {len(df)} transactions")

    # Engineer features
    print("Engineering features...")
    X = engineer_features(df)
    y = df['is_fraud']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train XGBoost
    print("Training XGBoost model...")
    model = xgb.XGBClassifier(
        max_depth=6,
        learning_rate=0.1,
        n_estimators=100,
        objective='binary:logistic',
        eval_metric='auc',
        use_label_encoder=False
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        early_stopping_rounds=10,
        verbose=True
    )

    # Evaluate
    print("Evaluating model...")
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")

    # Save model
    print("Saving model...")
    model.save_model('models/fraud_model.xgb')

    return model

if __name__ == "__main__":
    train_xgboost_model()
```

---

### 2. `scripts/ml/feature_engineering.py` (195 lines)

**Purpose:** Transform raw transaction data into ML features

**Key Features:**

```python
import pandas as pd
import numpy as np

class FeatureEngineer:
    """Transform raw transactions into ML features"""

    def transform(self, df):
        """Transform dataframe into feature matrix"""

        features = pd.DataFrame()

        # Numerical features
        features['amount'] = df['amount']
        features['amount_log'] = np.log1p(df['amount'])

        # Extract from metadata (JSONB)
        metadata = pd.json_normalize(df['metadata'])

        features['account_age_days'] = metadata.get('account_age_days', 0)
        features['transactions_last_hour'] = metadata.get('transactions_last_hour', 0)
        features['transactions_last_day'] = metadata.get('transactions_last_day', 0)
        features['credit_score'] = metadata.get('credit_score', 500)

        # Boolean features
        features['is_vpn'] = metadata.get('is_vpn', False).astype(int)
        features['is_tor'] = metadata.get('is_tor', False).astype(int)
        features['is_emulator'] = metadata.get('is_emulator', False).astype(int)
        features['kyc_verified'] = metadata.get('kyc_verified', False).astype(int)

        # Categorical features (one-hot encode)
        features = pd.get_dummies(
            features,
            columns=['industry', 'transaction_type'],
            prefix=['ind', 'txn_type']
        )

        # Fill missing values
        features = features.fillna(0)

        return features

    def get_feature_names(self):
        """Return list of feature names"""
        return [
            'amount', 'amount_log', 'account_age_days',
            'transactions_last_hour', 'transactions_last_day',
            'credit_score', 'is_vpn', 'is_tor', 'is_emulator',
            'kyc_verified',
            # ... plus one-hot encoded features
        ]
```

---

### 3. `scripts/ml/model_evaluation.py` (165 lines)

**Purpose:** Evaluate model performance

**Key Metrics:**

```python
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, confusion_matrix
)
import matplotlib.pyplot as plt
import seaborn as sns

def evaluate_model(model, X_test, y_test):
    """Comprehensive model evaluation"""

    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    metrics = {
        'accuracy': accuracy_score(y_test, y_pred),
        'precision': precision_score(y_test, y_pred),
        'recall': recall_score(y_test, y_pred),
        'f1_score': f1_score(y_test, y_pred),
        'roc_auc': roc_auc_score(y_test, y_pred_proba)
    }

    print("Model Performance:")
    for metric, value in metrics.items():
        print(f"  {metric}: {value:.4f}")

    # Confusion matrix
    plot_confusion_matrix(y_test, y_pred)

    # Feature importance
    plot_feature_importance(model)

    return metrics

def plot_confusion_matrix(y_test, y_pred):
    """Plot confusion matrix"""
    cm = confusion_matrix(y_test, y_pred)

    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.savefig('models/confusion_matrix.png')
    print("Confusion matrix saved to models/confusion_matrix.png")

def plot_feature_importance(model):
    """Plot top 20 feature importances"""
    importances = model.feature_importances_

    # Get top 20
    indices = np.argsort(importances)[::-1][:20]

    plt.figure(figsize=(10, 8))
    plt.barh(range(20), importances[indices])
    plt.title('Top 20 Feature Importances')
    plt.xlabel('Importance')
    plt.savefig('models/feature_importance.png')
    print("Feature importance saved to models/feature_importance.png")
```

---

## Testing

### Train the Model

```bash
# Ensure you have training data in database
python scripts/generate_synthetic_data.py --count 10000

# Train XGBoost model
python scripts/ml/train_fraud_model.py
```

**Expected Output:**
```
Loading training data...
Loaded 10000 transactions
Engineering features...
Training XGBoost model...
[0]     validation_0-auc:0.89234
[10]    validation_0-auc:0.92156
[20]    validation_0-auc:0.93421
...
Evaluating model...
              precision    recall  f1-score   support
           0       0.98      0.99      0.98      1800
           1       0.91      0.85      0.88       200

ROC-AUC Score: 0.9342
Saving model...
Model saved to models/fraud_model.xgb
```

---

### Verify Model File

```bash
# Check model file exists
ls -lh models/fraud_model.xgb

# Load and test model
python << 'EOF'
import xgboost as xgb

model = xgb.Booster()
model.load_model('models/fraud_model.xgb')
print("✓ Model loaded successfully")
print(f"Number of features: {model.num_features()}")
EOF
```

---

### Evaluate Model

```bash
python scripts/ml/model_evaluation.py
```

**Expected:** Metrics printed + confusion matrix and feature importance plots saved

---

## Success Criteria

By end of Week 1 (Month 4):
- ✅ XGBoost model trained successfully
- ✅ ROC-AUC score > 0.85
- ✅ Precision > 0.85 (low false positives)
- ✅ Recall > 0.80 (catch most fraud)
- ✅ Model saved to models/fraud_model.xgb
- ✅ Feature importance analyzed
- ✅ Confusion matrix generated

---

## Next Week Preview

**Week 2:** LSTM for Sequence Analysis
- Train LSTM model for transaction sequences
- Detect temporal fraud patterns
- User behavior modeling

---

## Notes

- Start with synthetic data if you don't have real fraud data yet
- Adjust class weights if dataset is imbalanced
- Tune hyperparameters based on your data
- Consider cross-validation for more robust evaluation

---

**End of Week 1 Guide - Month 4**
