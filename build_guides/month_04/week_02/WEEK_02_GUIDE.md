# WEEK 2: LSTM for Sequence Analysis
**Days 92-98 | Month 4**

## Overview
Train LSTM model for detecting fraud patterns in transaction sequences:
- LSTM architecture for time series
- Transaction sequence processing
- Temporal fraud pattern detection
- User behavior modeling

## Files to Build

```
scripts/ml/
├── train_lstm_model.py            # 340 lines - LSTM training
├── sequence_processor.py          # 225 lines - Sequence preprocessing
└── lstm_predictor.py              # 180 lines - LSTM inference

app/services/
└── lstm_detector.py               # 295 lines - LSTM fraud detection service
```

**Total:** 4 files, ~1,040 lines

---

## Dependencies

Add to Month 4 Week 1 requirements:

```
tensorflow==2.15.0
keras==2.15.0
```

---

## File Details

### 1. `scripts/ml/train_lstm_model.py` (340 lines)

**Purpose:** Train LSTM for transaction sequence analysis

```python
import tensorflow as tf
from tensorflow import keras
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
import numpy as np

def prepare_sequences(transactions, sequence_length=10):
    """
    Convert transactions into sequences

    Args:
        transactions: List of user transactions
        sequence_length: Number of transactions per sequence

    Returns:
        X: Sequences of transactions
        y: Labels (fraud/not fraud)
    """
    sequences = []
    labels = []

    for user_id in transactions['user_id'].unique():
        user_txns = transactions[transactions['user_id'] == user_id].sort_values('created_at')

        for i in range(len(user_txns) - sequence_length):
            seq = user_txns.iloc[i:i+sequence_length]
            label = user_txns.iloc[i+sequence_length]['is_fraud']

            # Extract features for each transaction in sequence
            seq_features = seq[['amount', 'hour_of_day', 'is_weekend', 'is_vpn']].values
            sequences.append(seq_features)
            labels.append(label)

    return np.array(sequences), np.array(labels)

def build_lstm_model(sequence_length, n_features):
    """Build LSTM model architecture"""

    model = Sequential([
        LSTM(128, input_shape=(sequence_length, n_features), return_sequences=True),
        Dropout(0.2),
        LSTM(64),
        Dropout(0.2),
        Dense(32, activation='relu'),
        Dense(1, activation='sigmoid')
    ])

    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc')]
    )

    return model

def train_lstm():
    """Train LSTM model"""

    # Load data
    print("Loading transaction sequences...")
    df = load_transactions_with_sequences()

    # Prepare sequences
    print("Preparing sequences...")
    X, y = prepare_sequences(df, sequence_length=10)

    # Split data
    split = int(0.8 * len(X))
    X_train, X_test = X[:split], X[split:]
    y_train, y_test = y[:split], y[split:]

    # Build model
    print("Building LSTM model...")
    model = build_lstm_model(sequence_length=10, n_features=4)
    print(model.summary())

    # Train model
    print("Training...")
    history = model.fit(
        X_train, y_train,
        batch_size=32,
        epochs=20,
        validation_data=(X_test, y_test),
        callbacks=[
            keras.callbacks.EarlyStopping(patience=3, restore_best_weights=True),
            keras.callbacks.ModelCheckpoint('models/lstm_fraud_model.h5', save_best_only=True)
        ]
    )

    # Evaluate
    print("Evaluating...")
    loss, accuracy, auc = model.evaluate(X_test, y_test)
    print(f"Test Loss: {loss:.4f}")
    print(f"Test Accuracy: {accuracy:.4f}")
    print(f"Test AUC: {auc:.4f}")

    # Save
    model.save('models/lstm_fraud_model.h5')
    print("Model saved to models/lstm_fraud_model.h5")

    return model, history

if __name__ == "__main__":
    train_lstm()
```

---

### 2. `scripts/ml/sequence_processor.py` (225 lines)

**Purpose:** Process transaction sequences for LSTM

```python
import pandas as pd
import numpy as np
from datetime import datetime

class SequenceProcessor:
    """Process transactions into sequences for LSTM"""

    def __init__(self, sequence_length=10):
        self.sequence_length = sequence_length

    def extract_temporal_features(self, df):
        """Extract time-based features"""

        df['hour_of_day'] = pd.to_datetime(df['created_at']).dt.hour
        df['day_of_week'] = pd.to_datetime(df['created_at']).dt.dayofweek
        df['is_weekend'] = df['day_of_week'].isin([5, 6]).astype(int)
        df['is_night'] = df['hour_of_day'].between(22, 6).astype(int)

        return df

    def create_sequences(self, df, user_id_col='user_id'):
        """Create sequences for each user"""

        sequences = []
        labels = []

        for user in df[user_id_col].unique():
            user_data = df[df[user_id_col] == user].sort_values('created_at')

            if len(user_data) < self.sequence_length + 1:
                continue

            for i in range(len(user_data) - self.sequence_length):
                seq = user_data.iloc[i:i+self.sequence_length]
                next_txn = user_data.iloc[i+self.sequence_length]

                sequences.append(self.extract_features(seq))
                labels.append(next_txn['is_fraud'])

        return np.array(sequences), np.array(labels)
```

---

### 3. `app/services/lstm_detector.py` (295 lines)

**Purpose:** LSTM-based fraud detection service

```python
import tensorflow as tf
import numpy as np

class LSTMFraudDetector:
    """LSTM-based fraud detector for sequences"""

    def __init__(self, model_path='models/lstm_fraud_model.h5'):
        self.model = tf.keras.models.load_model(model_path)
        self.sequence_length = 10

    async def predict_sequence(self, user_transactions):
        """
        Predict fraud for next transaction based on sequence

        Args:
            user_transactions: Recent transactions for user (list of dicts)

        Returns:
            {
                "fraud_probability": 0.85,
                "lstm_score": 85,
                "sequence_anomaly": True
            }
        """

        # Get last N transactions
        recent = user_transactions[-self.sequence_length:]

        if len(recent) < self.sequence_length:
            return {
                "fraud_probability": 0.0,
                "lstm_score": 0,
                "sequence_anomaly": False,
                "insufficient_history": True
            }

        # Convert to feature matrix
        features = self._extract_features(recent)
        features = np.array([features])  # Batch dimension

        # Predict
        probability = self.model.predict(features)[0][0]

        return {
            "fraud_probability": float(probability),
            "lstm_score": int(probability * 100),
            "sequence_anomaly": probability > 0.7,
            "insufficient_history": False
        }

    def _extract_features(self, transactions):
        """Extract features from transaction sequence"""

        features = []
        for txn in transactions:
            features.append([
                txn['amount'],
                txn.get('hour_of_day', 12),
                txn.get('is_weekend', 0),
                txn.get('is_vpn', 0)
            ])

        return np.array(features)
```

---

## Testing

### Train LSTM Model

```bash
python scripts/ml/train_lstm_model.py
```

**Expected Output:**
```
Loading transaction sequences...
Preparing sequences...
Created 5000 sequences
Building LSTM model...
Model: "sequential"
_________________________________________________________________
Layer (type)                Output Shape              Param #
=================================================================
lstm (LSTM)                 (None, 10, 128)           68096
dropout (Dropout)           (None, 10, 128)           0
lstm_1 (LSTM)              (None, 64)                49408
dropout_1 (Dropout)         (None, 64)                0
dense (Dense)               (None, 32)                2080
dense_1 (Dense)             (None, 1)                 33
=================================================================
Training...
Epoch 1/20 - loss: 0.4523 - auc: 0.7234
Epoch 5/20 - loss: 0.2156 - auc: 0.8912
...
Test AUC: 0.8945
Model saved to models/lstm_fraud_model.h5
```

---

### Test LSTM Predictor

```python
python << 'EOF'
from app.services.lstm_detector import LSTMFraudDetector

detector = LSTMFraudDetector()

# Simulate recent transactions
recent_txns = [
    {'amount': 10000, 'hour_of_day': 14, 'is_weekend': 0, 'is_vpn': 0},
    {'amount': 15000, 'hour_of_day': 15, 'is_weekend': 0, 'is_vpn': 0},
    # ... 8 more transactions
    {'amount': 500000, 'hour_of_day': 2, 'is_weekend': 1, 'is_vpn': 1}  # Suspicious
]

result = await detector.predict_sequence(recent_txns)
print(f"LSTM Fraud Probability: {result['fraud_probability']:.2f}")
print(f"Sequence Anomaly: {result['sequence_anomaly']}")
EOF
```

---

## Success Criteria

By end of Week 2 (Month 4):
- ✅ LSTM model trained on sequences
- ✅ AUC score > 0.85 for sequence prediction
- ✅ Can detect temporal fraud patterns
- ✅ Model saved to models/lstm_fraud_model.h5
- ✅ LSTM service integrated

---

## Next Week Preview

**Week 3:** Neural Networks & Ensemble
- Deep neural network training
- Ensemble methods (voting, stacking)
- Hyperparameter tuning

---

**End of Week 2 Guide - Month 4**
