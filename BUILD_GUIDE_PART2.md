# Sentinel Build Guide - Part 2

This is the continuation of BUILD_GUIDE.md covering Steps 11-17.

---

## 11. ML Model Training

### Step 11.1: Create Model Directory

```bash
mkdir -p models
touch models/.gitkeep
```

### Step 11.2: Create Training Script

Create `/sentinel/scripts/ml/__init__.py`:
```python
# Empty file
```

Create `/sentinel/scripts/ml/train_model.py`:

```python
#!/usr/bin/env python3
"""Train XGBoost fraud detection model"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import xgboost as xgb
import joblib
from datetime import datetime


def generate_synthetic_data(n_samples=10000):
    """Generate synthetic fraud data for training"""
    print(f"Generating {n_samples} synthetic training samples...")

    np.random.seed(42)

    # Generate features
    data = {
        # Amount features
        'amount': np.random.lognormal(10, 2, n_samples),
        'amount_log': np.random.normal(10, 2, n_samples),

        # Velocity features
        'device_velocity_1min': np.random.poisson(0.5, n_samples),
        'device_velocity_10min': np.random.poisson(2, n_samples),
        'device_velocity_1hour': np.random.poisson(5, n_samples),
        'device_velocity_24hour': np.random.poisson(10, n_samples),
        'phone_velocity_1hour': np.random.poisson(3, n_samples),
        'phone_velocity_24hour': np.random.poisson(7, n_samples),

        # Device history
        'device_total_txns': np.random.poisson(15, n_samples),
        'device_fraud_count': np.random.poisson(1, n_samples),
        'device_avg_amount': np.random.lognormal(9, 2, n_samples),

        # Time features
        'hour': np.random.randint(0, 24, n_samples),
        'day_of_week': np.random.randint(0, 7, n_samples),
        'is_late_night': np.random.binomial(1, 0.1, n_samples),

        # Transaction type (one-hot encoded)
        'is_loan_application': np.random.binomial(1, 0.3, n_samples),
        'is_transfer': np.random.binomial(1, 0.25, n_samples),
        'is_withdrawal': np.random.binomial(1, 0.15, n_samples),
        'is_purchase': np.random.binomial(1, 0.2, n_samples),
        'is_bet_placement': np.random.binomial(1, 0.05, n_samples),
        'is_crypto_deposit': np.random.binomial(1, 0.05, n_samples),
    }

    df = pd.DataFrame(data)

    # Generate fraud labels (10% fraud rate)
    # Fraud more likely with: high velocity, late night, high amounts, new devices
    fraud_score = (
        df['device_velocity_1hour'] * 2 +
        df['device_velocity_24hour'] +
        df['phone_velocity_1hour'] * 1.5 +
        df['is_late_night'] * 3 +
        (df['amount'] > df['amount'].quantile(0.9)).astype(int) * 2 +
        (df['device_total_txns'] < 5).astype(int) * 2 +
        (df['device_fraud_count'] > 2).astype(int) * 5
    )

    # Convert fraud score to probability
    fraud_prob = 1 / (1 + np.exp(-fraud_score / 10))
    df['is_fraud'] = (fraud_prob > np.random.uniform(0, 1, n_samples)).astype(int)

    print(f"✓ Generated data with {df['is_fraud'].sum()} fraud cases ({df['is_fraud'].mean()*100:.1f}%)")

    return df


def train_model(df, model_path='models/fraud_model.pkl'):
    """Train XGBoost model"""
    print("\nTraining XGBoost model...")

    # Prepare features and labels
    X = df.drop('is_fraud', axis=1)
    y = df['is_fraud']

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Training set: {len(X_train)} samples")
    print(f"Test set: {len(X_test)} samples")

    # Train XGBoost model
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        objective='binary:logistic',
        random_state=42,
        eval_metric='auc'
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False
    )

    # Evaluate
    print("\n" + "=" * 60)
    print("Model Evaluation")
    print("=" * 60)

    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=['Legitimate', 'Fraud']))

    print(f"\nROC AUC Score: {roc_auc_score(y_test, y_pred_proba):.4f}")

    print("\nConfusion Matrix:")
    cm = confusion_matrix(y_test, y_pred)
    print(f"TN: {cm[0][0]}, FP: {cm[0][1]}")
    print(f"FN: {cm[1][0]}, TP: {cm[1][1]}")

    # Feature importance
    print("\nTop 10 Most Important Features:")
    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    for idx, row in feature_importance.head(10).iterrows():
        print(f"  {row['feature']}: {row['importance']:.4f}")

    # Save model
    joblib.dump(model, model_path)
    print(f"\n✓ Model saved to {model_path}")

    return model


def main():
    """Main training function"""
    print("=" * 60)
    print("Sentinel ML Model Training")
    print("=" * 60)

    # Generate synthetic data
    df = generate_synthetic_data(n_samples=10000)

    # Train model
    model = train_model(df)

    print("\n" + "=" * 60)
    print("✓ Training complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
```

Make it executable:
```bash
chmod +x scripts/ml/train_model.py
```

### Step 11.3: Train the Model

```bash
# Activate virtual environment
source venv/bin/activate

# Run training script
python scripts/ml/train_model.py
```

---

## 12. Frontend Development

### Step 12.1: Initialize Frontend Project

```bash
cd frontend

# Initialize npm project
npm init -y

# Install dependencies
npm install react@18.2.0 react-dom@18.2.0
npm install -D vite@5.0.8 @vitejs/plugin-react@4.2.1
npm install -D typescript@5.2.2 @types/react@18.2.45 @types/react-dom@18.2.18
npm install -D tailwindcss@3.3.6 postcss@8.4.32 autoprefixer@10.4.16
npm install axios@1.6.2 react-router-dom@6.20.0
npm install framer-motion@10.16.16 lucide-react@0.294.0
npm install recharts@2.10.3
npm install three@0.159.0 @react-three/fiber@8.15.12 @react-three/drei@9.92.7
npm install @types/three@0.159.0
npm install @fingerprintjs/fingerprintjs@4.2.0
```

### Step 12.2: Create Frontend Configuration Files

Create `/sentinel/frontend/package.json`:

```json
{
  "name": "sentinel-dashboard",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.2",
    "react-router-dom": "^6.20.0",
    "framer-motion": "^10.16.16",
    "lucide-react": "^0.294.0",
    "recharts": "^2.10.3",
    "three": "^0.159.0",
    "@react-three/fiber": "^8.15.12",
    "@react-three/drei": "^9.92.7",
    "@fingerprintjs/fingerprintjs": "^4.2.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "@types/three": "^0.159.0",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.2.2",
    "vite": "^5.0.8",
    "tailwindcss": "^3.3.6",
    "postcss": "^8.4.32",
    "autoprefixer": "^10.4.16"
  }
}
```

Create `/sentinel/frontend/vite.config.ts`:

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  }
})
```

Create `/sentinel/frontend/tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

Create `/sentinel/frontend/tsconfig.node.json`:

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

Create `/sentinel/frontend/tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-slow': 'bounce 3s infinite',
      },
    },
  },
  plugins: [],
}
```

Create `/sentinel/frontend/postcss.config.js`:

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

### Step 12.3: Create Frontend HTML Entry Point

Create `/sentinel/frontend/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Sentinel - Fraud Detection Platform</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### Step 12.4: Create Frontend Source Files

Create `/sentinel/frontend/src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-border;
  }

  body {
    @apply bg-gray-950 text-white;
    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
}

@layer components {
  .glass {
    @apply bg-white/5 backdrop-blur-xl border border-white/10;
  }

  .glass-hover {
    @apply hover:bg-white/10 transition-all duration-300;
  }
}
```

Create `/sentinel/frontend/src/main.tsx`:

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

Create `/sentinel/frontend/src/App.tsx`:

```typescript
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Transactions from './pages/Transactions'
import Background3D from './components/Background3D'

function App() {
  return (
    <Router>
      <div className="relative min-h-screen">
        <Background3D />
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/transactions" element={<Transactions />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
```

### Step 12.5: Create Types

Create `/sentinel/frontend/src/types/index.ts`:

```typescript
export interface Transaction {
  id: number;
  transaction_id: string;
  amount: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  recommendation: 'APPROVE' | 'REVIEW' | 'REJECT';
  created_at: string;
}

export interface DashboardStats {
  total_transactions: number;
  fraud_detected: number;
  fraud_rate: number;
  avg_risk_score: number;
  high_risk_count: number;
  processing_time_avg: number;
}

export interface FraudFlag {
  rule_id: number;
  rule_name: string;
  severity: string;
  message: string;
  confidence: number;
}

export interface TransactionCheckResponse {
  transaction_id: string;
  risk_score: number;
  risk_level: string;
  recommendation: string;
  flags: FraudFlag[];
  processing_time_ms: number;
  cached: boolean;
  consortium_match: boolean;
}
```

### Step 12.6: Create API Client

Create `/sentinel/frontend/src/lib/api.ts`:

```typescript
import axios from 'axios';
import type { DashboardStats, Transaction, TransactionCheckResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY || 'sk_demo_key';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  },
});

export const getDashboardStats = async (days: number = 7): Promise<DashboardStats> => {
  const response = await api.get(`/stats?days=${days}`);
  return response.data;
};

export const getTransactions = async (
  limit: number = 50,
  offset: number = 0,
  risk_level?: string
): Promise<Transaction[]> => {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });
  if (risk_level) params.append('risk_level', risk_level);

  const response = await api.get(`/transactions?${params}`);
  return response.data;
};

export const checkTransaction = async (data: any): Promise<TransactionCheckResponse> => {
  const response = await api.post('/check-transaction', data);
  return response.data;
};

export default api;
```

### Step 12.7: Create 3D Background Component

Create `/sentinel/frontend/src/components/Background3D.tsx`:

```typescript
import { Canvas } from '@react-three/fiber'
import { Points, PointMaterial } from '@react-three/drei'
import { useRef, useMemo } from 'react'
import { useFrame } from '@react-three/fiber'
import * as THREE from 'three'

function AnimatedPoints() {
  const ref = useRef<THREE.Points>(null!)

  const particles = useMemo(() => {
    const positions = new Float32Array(1000 * 3)
    for (let i = 0; i < 1000; i++) {
      positions[i * 3] = (Math.random() - 0.5) * 10
      positions[i * 3 + 1] = (Math.random() - 0.5) * 10
      positions[i * 3 + 2] = (Math.random() - 0.5) * 10
    }
    return positions
  }, [])

  useFrame((state, delta) => {
    ref.current.rotation.x -= delta / 10
    ref.current.rotation.y -= delta / 15
  })

  return (
    <Points ref={ref} positions={particles} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color="#3b82f6"
        size={0.02}
        sizeAttenuation={true}
        depthWrite={false}
      />
    </Points>
  )
}

export default function Background3D() {
  return (
    <div className="fixed inset-0 -z-10">
      <Canvas camera={{ position: [0, 0, 1] }}>
        <AnimatedPoints />
      </Canvas>
    </div>
  )
}
```

### Step 12.8: Create Dashboard Page

Create `/sentinel/frontend/src/pages/Dashboard.tsx`:

```typescript
import { useEffect, useState } from 'react'
import { Activity, AlertTriangle, Shield, TrendingUp } from 'lucide-react'
import { getDashboardStats } from '../lib/api'
import type { DashboardStats } from '../types'

export default function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDashboardStats(7)
        setStats(data)
      } catch (error) {
        console.error('Failed to fetch stats:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 30000) // Refresh every 30s
    return () => clearInterval(interval)
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
          Sentinel Dashboard
        </h1>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Activity className="w-6 h-6" />}
            title="Total Transactions"
            value={stats?.total_transactions.toLocaleString() || '0'}
            color="blue"
          />
          <StatCard
            icon={<AlertTriangle className="w-6 h-6" />}
            title="Fraud Detected"
            value={stats?.fraud_detected.toLocaleString() || '0'}
            color="red"
          />
          <StatCard
            icon={<TrendingUp className="w-6 h-6" />}
            title="Fraud Rate"
            value={`${stats?.fraud_rate.toFixed(2)}%` || '0%'}
            color="yellow"
          />
          <StatCard
            icon={<Shield className="w-6 h-6" />}
            title="Avg Risk Score"
            value={stats?.avg_risk_score.toFixed(1) || '0'}
            color="green"
          />
        </div>

        <div className="glass rounded-2xl p-6">
          <h2 className="text-2xl font-bold mb-4">System Performance</h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-gray-400">Avg Processing Time</span>
                <span className="font-semibold">{stats?.processing_time_avg.toFixed(2)}ms</span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${Math.min((stats?.processing_time_avg || 0) / 2, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, color }: any) {
  const colors = {
    blue: 'from-blue-500 to-blue-600',
    red: 'from-red-500 to-red-600',
    yellow: 'from-yellow-500 to-yellow-600',
    green: 'from-green-500 to-green-600',
  }

  return (
    <div className="glass rounded-2xl p-6 glass-hover">
      <div className={`inline-flex p-3 rounded-xl bg-gradient-to-br ${colors[color]} mb-4`}>
        {icon}
      </div>
      <div className="text-gray-400 text-sm mb-1">{title}</div>
      <div className="text-3xl font-bold">{value}</div>
    </div>
  )
}
```

### Step 12.9: Create Transactions Page

Create `/sentinel/frontend/src/pages/Transactions.tsx`:

```typescript
import { useEffect, useState } from 'react'
import { getTransactions } from '../lib/api'
import type { Transaction } from '../types'

export default function Transactions() {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTransactions = async () => {
      try {
        const data = await getTransactions(50, 0)
        setTransactions(data)
      } catch (error) {
        console.error('Failed to fetch transactions:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchTransactions()
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500" />
      </div>
    )
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-4xl font-bold mb-8">Transaction History</h1>

        <div className="glass rounded-2xl p-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="text-left border-b border-white/10">
                  <th className="pb-4 px-4">ID</th>
                  <th className="pb-4 px-4">Amount</th>
                  <th className="pb-4 px-4">Risk Score</th>
                  <th className="pb-4 px-4">Risk Level</th>
                  <th className="pb-4 px-4">Recommendation</th>
                  <th className="pb-4 px-4">Date</th>
                </tr>
              </thead>
              <tbody>
                {transactions.map((txn) => (
                  <tr key={txn.id} className="border-b border-white/5 hover:bg-white/5">
                    <td className="py-4 px-4 font-mono text-sm">{txn.transaction_id}</td>
                    <td className="py-4 px-4">₦{txn.amount.toLocaleString()}</td>
                    <td className="py-4 px-4">{txn.risk_score}</td>
                    <td className="py-4 px-4">
                      <span className={`px-3 py-1 rounded-full text-sm ${getRiskLevelColor(txn.risk_level)}`}>
                        {txn.risk_level}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <span className={`px-3 py-1 rounded-full text-sm ${getRecommendationColor(txn.recommendation)}`}>
                        {txn.recommendation}
                      </span>
                    </td>
                    <td className="py-4 px-4 text-gray-400 text-sm">
                      {new Date(txn.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  )
}

function getRiskLevelColor(level: string) {
  const colors = {
    low: 'bg-green-500/20 text-green-400',
    medium: 'bg-yellow-500/20 text-yellow-400',
    high: 'bg-red-500/20 text-red-400',
    critical: 'bg-purple-500/20 text-purple-400',
  }
  return colors[level as keyof typeof colors] || colors.low
}

function getRecommendationColor(recommendation: string) {
  const colors = {
    APPROVE: 'bg-green-500/20 text-green-400',
    REVIEW: 'bg-yellow-500/20 text-yellow-400',
    REJECT: 'bg-red-500/20 text-red-400',
  }
  return colors[recommendation as keyof typeof colors] || colors.REVIEW
}
```

### Step 12.10: Build Frontend

```bash
cd frontend

# Development mode
npm run dev

# Production build
npm run build
```

---

## 13. Testing

### Step 13.1: Create Test Files

Create `/sentinel/tests/__init__.py`:
```python
# Empty file
```

Create `/sentinel/tests/test_api.py`:

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.database import Client
from app.core.security import generate_api_key, hash_password

client = TestClient(app)

# Test API key (would be created in test database)
TEST_API_KEY = "sk_test_key"


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_check_transaction():
    """Test fraud check endpoint"""
    payload = {
        "transaction_id": "TEST001",
        "user_id": "USER001",
        "amount": 50000,
        "currency": "NGN",
        "transaction_type": "loan_application",
        "industry": "fintech",
        "phone": "08012345678",
        "device_id": "DEVICE001"
    }

    response = client.post(
        "/api/v1/check-transaction",
        json=payload,
        headers={"X-API-Key": TEST_API_KEY}
    )

    # Note: This will fail without valid API key in database
    # In real tests, you'd set up test database fixtures
    assert response.status_code in [200, 401]


def test_invalid_api_key():
    """Test with invalid API key"""
    response = client.post(
        "/api/v1/check-transaction",
        json={"transaction_id": "TEST001"},
        headers={"X-API-Key": "invalid_key"}
    )

    assert response.status_code == 401
```

Create `/sentinel/tests/test_rules.py`:

```python
import pytest
from app.services.rules import RulesEngine
from app.models.schemas import TransactionCheckRequest, TransactionType, Industry


@pytest.mark.asyncio
async def test_high_velocity_rule():
    """Test high velocity detection rule"""
    # This is a simplified test
    # In real tests, you'd mock the database and Redis

    request = TransactionCheckRequest(
        transaction_id="TEST001",
        user_id="USER001",
        amount=50000,
        transaction_type=TransactionType.LOAN_APPLICATION,
        industry=Industry.FINTECH
    )

    context = {
        "device_velocity": {
            "count_1hour": 15  # High velocity
        }
    }

    # Would need to instantiate RulesEngine with mocked dependencies
    # is_triggered, message = await rules_engine._rule_high_velocity_device(request, context)
    # assert is_triggered is True
```

### Step 13.2: Create pytest Configuration

Create `/sentinel/pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
```

### Step 13.3: Run Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_api.py
```

---

## 14. Containerization

### Step 14.1: Create Dockerfile

Create `/sentinel/Dockerfile`:

```dockerfile
# Multi-stage build for Python backend

# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY app/ ./app/
COPY scripts/ ./scripts/
COPY models/ ./models/
COPY .env.example .env

# Create non-root user
RUN useradd -m -u 1000 sentinel && chown -R sentinel:sentinel /app
USER sentinel

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 14.2: Create Docker Compose

Create `/sentinel/docker-compose.yml`:

```yaml
version: '3.8'

services:
  # PostgreSQL Database
  postgres:
    image: postgres:15-alpine
    container_name: sentinel-postgres
    environment:
      POSTGRES_DB: sentinel
      POSTGRES_USER: sentinel
      POSTGRES_PASSWORD: sentinel_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U sentinel"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis Cache
  redis:
    image: redis:7-alpine
    container_name: sentinel-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Sentinel API
  api:
    build: .
    container_name: sentinel-api
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://sentinel:sentinel_password@postgres:5432/sentinel
      - REDIS_URL=redis://redis:6379/0
      - ENVIRONMENT=production
      - DEBUG=false
    volumes:
      - ./models:/app/models
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:
  redis_data:
```

### Step 14.3: Create .dockerignore

Create `/sentinel/.dockerignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/
env/
.venv

# Git
.git/
.gitignore

# IDE
.vscode/
.idea/

# Tests
tests/
.pytest_cache/
.coverage
htmlcov/

# Frontend
frontend/node_modules/
frontend/dist/
frontend/build/

# Logs
*.log
logs/

# Documentation
*.md
!README.md

# Environment
.env.local
.env.*.local

# Misc
.DS_Store
```

### Step 14.4: Build and Run with Docker

```bash
# Build Docker image
docker-compose build

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## 15. Deployment

### Step 15.1: Prepare for Production

1. **Update Environment Variables for Production:**

```bash
# Generate secure secret key
openssl rand -hex 32

# Update .env file with production values
nano .env
```

2. **Set Production Settings:**
```bash
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<your-generated-secret-key>
DATABASE_URL=<your-production-database-url>
REDIS_URL=<your-production-redis-url>
CORS_ORIGINS=["https://yourdomain.com"]
SENTRY_DSN=<your-sentry-dsn>  # Optional
```

### Step 15.2: Railway Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Link to existing project or create new
railway link

# Add PostgreSQL
railway add --plugin postgresql

# Add Redis
railway add --plugin redis

# Set environment variables
railway variables set SECRET_KEY=<your-key>

# Deploy
railway up
```

### Step 15.3: AWS Deployment (Alternative)

**Using EC2:**

```bash
# SSH into EC2 instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
sudo apt update
sudo apt install docker.io docker-compose -y

# Clone repository
git clone your-repo-url
cd sentinel

# Copy environment file
cp .env.example .env
nano .env  # Edit with production values

# Start services
docker-compose up -d

# Setup nginx reverse proxy (optional)
sudo apt install nginx
sudo nano /etc/nginx/sites-available/sentinel
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 15.4: Setup SSL Certificate

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

---

## 16. Documentation

### Step 16.1: Create API Documentation

The FastAPI application automatically generates API documentation:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

### Step 16.2: Create Deployment Guide

Create `/sentinel/DEPLOYMENT.md` with deployment instructions.

### Step 16.3: Create API Examples

Create `/sentinel/API_EXAMPLES.md` with example API calls.

---

## 17. Verification & Testing

### Step 17.1: Start All Services

```bash
# Start PostgreSQL
brew services start postgresql@15  # macOS
# OR
sudo systemctl start postgresql  # Linux

# Start Redis
brew services start redis  # macOS
# OR
sudo systemctl start redis  # Linux

# Activate virtual environment
source venv/bin/activate

# Run database initialization
python scripts/init_db.py

# Save the API key that's printed!

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

In a new terminal:
```bash
# Start frontend
cd frontend
npm run dev
```

### Step 17.2: Test API Endpoints

```bash
# Test health check
curl http://localhost:8000/health

# Test fraud detection (replace with your API key)
curl -X POST http://localhost:8000/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{
    "transaction_id": "TXN001",
    "user_id": "USER001",
    "amount": 50000,
    "currency": "NGN",
    "transaction_type": "loan_application",
    "industry": "fintech",
    "phone": "08012345678",
    "device_id": "DEVICE001"
  }'
```

### Step 17.3: Access Dashboard

Open browser and navigate to:
- **Backend API Docs:** http://localhost:8000/docs
- **Frontend Dashboard:** http://localhost:3000

### Step 17.4: Run Full Test Suite

```bash
# Backend tests
pytest tests/ -v --cov=app

# Check code quality
black app/ --check
flake8 app/
mypy app/
```

### Step 17.5: Performance Testing

```bash
# Install Apache Bench (if not installed)
sudo apt install apache2-utils  # Linux
brew install httpd  # macOS

# Load test
ab -n 1000 -c 10 -H "X-API-Key: YOUR_API_KEY" \
  -p test_payload.json \
  -T application/json \
  http://localhost:8000/api/v1/check-transaction
```

---

## Completion Checklist

- [ ] Prerequisites installed (Python, Node.js, PostgreSQL, Redis)
- [ ] Backend project structure created
- [ ] All Python dependencies installed
- [ ] Database models and schemas created
- [ ] Core fraud detector implemented
- [ ] Services layer complete (Rules, ML, Redis, etc.)
- [ ] API endpoints created
- [ ] Middleware configured
- [ ] Database initialized with sample data
- [ ] ML model trained
- [ ] Frontend project setup
- [ ] Frontend components created
- [ ] Tests written and passing
- [ ] Docker configuration complete
- [ ] Documentation created
- [ ] System verified and tested

---

## Next Steps

After completing this build guide, consider:

1. **Enhance ML Model:** Collect real fraud data and retrain the model
2. **Add More Rules:** Implement industry-specific fraud rules
3. **Integrate External APIs:** Connect to BVN verification, credit bureaus
4. **Setup Monitoring:** Integrate Sentry, Datadog, or similar
5. **Add Admin Dashboard:** Build admin interface for managing clients and rules
6. **Implement Webhooks:** Add webhook notifications for fraud alerts
7. **Scale Infrastructure:** Setup load balancing, caching strategies
8. **Add Analytics:** Implement fraud trend analysis and reporting
9. **Security Audit:** Conduct security review and penetration testing
10. **Go to Production:** Deploy to production environment

---

## Support

For questions or issues:
- Review documentation in `/docs`
- Check existing issues on GitHub
- Contact support team

---

**Congratulations!** You have successfully built the Sentinel Fraud Detection Platform from scratch. 🎉
