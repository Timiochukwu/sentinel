# WEEK 4: Model Deployment & Versioning
**Days 106-112 | Month 4**

## Overview
Deploy ML models with versioning and A/B testing:
- Model registry and versioning
- Model deployment pipeline
- A/B testing framework
- Performance monitoring

## Files to Build

```
scripts/ml/
├── model_registry.py              # 175 lines
├── deploy_model.py                # 145 lines
└── ab_testing.py                  # 155 lines

app/services/
└── model_manager.py               # 195 lines
```

**Total:** 4 files, ~670 lines

---

## Key Features

### Model Registry

```python
# model_registry.py
class ModelRegistry:
    """Manage model versions"""

    def register_model(self, name, version, path, metrics):
        """Register new model version"""
        self.models[f"{name}:{version}"] = {
            'path': path,
            'metrics': metrics,
            'deployed_at': datetime.utcnow()
        }

    def get_model(self, name, version='latest'):
        """Get specific model version"""
        if version == 'latest':
            return self._get_latest(name)
        return self.models.get(f"{name}:{version}")
```

### A/B Testing

```python
# ab_testing.py
class ABTester:
    """Run A/B tests on models"""

    def split_traffic(self, user_id, split_ratio=0.5):
        """Route traffic between model A and B"""
        hash_val = hash(user_id) % 100
        return 'model_a' if hash_val < split_ratio * 100 else 'model_b'

    def compare_models(self, model_a, model_b):
        """Compare model performance"""
        results_a = self.evaluate(model_a)
        results_b = self.evaluate(model_b)

        return {
            'model_a_auc': results_a['auc'],
            'model_b_auc': results_b['auc'],
            'winner': 'a' if results_a['auc'] > results_b['auc'] else 'b'
        }
```

---

## Testing

```bash
# Deploy model
python scripts/ml/deploy_model.py --model fraud_model_v2

# Run A/B test
python scripts/ml/ab_testing.py --model-a v1 --model-b v2 --split 50
```

---

## Success Criteria

- ✅ Model registry operational
- ✅ A/B testing framework working
- ✅ Can rollback models
- ✅ Performance monitoring active

---

**End of Week 4 Guide - Month 4 Complete!**
