# WEEK 3: Neural Networks & Ensemble Methods
**Days 99-105 | Month 4**

## Overview
Build deep neural networks and ensemble methods:
- Deep neural network for fraud detection
- Ensemble methods (voting, stacking)
- Hyperparameter tuning with grid search
- Model comparison framework

## Files to Build

```
scripts/ml/
├── train_neural_network.py       # 310 lines - DNN training
├── ensemble_model.py              # 265 lines - Ensemble methods
└── hyperparameter_tuning.py      # 190 lines - Grid/random search

app/services/
└── ensemble_detector.py           # 285 lines - Ensemble fraud detector
```

**Total:** 4 files, ~1,050 lines

---

## Key Implementation

### Deep Neural Network

```python
# train_neural_network.py
from tensorflow import keras

def build_dnn_model(input_dim):
    """Build deep neural network"""

    model = keras.Sequential([
        keras.layers.Dense(256, activation='relu', input_dim=input_dim),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(128, activation='relu'),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dense(1, activation='sigmoid')
    ])

    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy', keras.metrics.AUC()]
    )

    return model
```

### Ensemble Methods

```python
# ensemble_model.py
from sklearn.ensemble import VotingClassifier, StackingClassifier
import xgboost as xgb
from sklearn.linear_model import LogisticRegression

def create_ensemble():
    """Create ensemble of XGBoost, RF, and LR"""

    estimators = [
        ('xgb', xgb.XGBClassifier()),
        ('rf', RandomForestClassifier()),
        ('lr', LogisticRegression())
    ]

    # Voting ensemble
    voting = VotingClassifier(estimators, voting='soft')

    # Stacking ensemble
    stacking = StackingClassifier(
        estimators=estimators,
        final_estimator=LogisticRegression()
    )

    return voting, stacking
```

---

## Testing

```bash
# Train DNN
python scripts/ml/train_neural_network.py

# Train ensemble
python scripts/ml/ensemble_model.py

# Hyperparameter tuning
python scripts/ml/hyperparameter_tuning.py
```

---

## Success Criteria

- ✅ DNN model trained (AUC > 0.87)
- ✅ Ensemble outperforms single models
- ✅ Hyperparameters optimized
- ✅ Models saved and versioned

---

**End of Week 3 Guide - Month 4**
