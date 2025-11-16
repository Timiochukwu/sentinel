# Mac Setup Guide for Sentinel

Complete guide for setting up and running Sentinel on macOS.

---

## ✅ Prerequisites

You mentioned you already have Python installed via Homebrew - perfect! Let's verify and set up the rest.

---

## 🔍 Step 1: Verify Your Python Installation

```bash
# Check Python version (should be 3.11 or higher)
python3 --version

# Should show: Python 3.11.x or Python 3.12.x
```

If you see `Python 3.11+`, you're good! If not:

```bash
# Install Python 3.11 via Homebrew
brew install python@3.11

# Link it
brew link python@3.11
```

---

## 📦 Step 2: Install Required Packages

### Option A: Install Globally (Quick & Easy)

```bash
# Install all Python packages Sentinel needs
pip3 install fastapi uvicorn sqlalchemy psycopg2-binary redis pydantic python-multipart

# Install ML packages
pip3 install numpy pandas scikit-learn xgboost

# Install optional packages
pip3 install httpx pytest python-dotenv
```

### Option B: Use Virtual Environment (Recommended for Production)

```bash
# Navigate to Sentinel directory
cd ~/sentinel  # or wherever you cloned it

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your terminal prompt now

# Install packages
pip install -r requirements.txt
```

---

## 🗄️ Step 3: Install PostgreSQL

Sentinel uses PostgreSQL for storing transaction data.

```bash
# Install PostgreSQL via Homebrew
brew install postgresql@15

# Start PostgreSQL service
brew services start postgresql@15

# Verify it's running
psql --version
# Should show: psql (PostgreSQL) 15.x
```

### Create Database

```bash
# Create Sentinel database
createdb sentinel

# Create test user and grant permissions
psql sentinel

# In PostgreSQL prompt:
CREATE USER sentinel_user WITH PASSWORD 'your_password_here';
GRANT ALL PRIVILEGES ON DATABASE sentinel TO sentinel_user;
\q
```

---

## 🔴 Step 4: Install Redis

Redis is used for rate limiting and caching.

```bash
# Install Redis via Homebrew
brew install redis

# Start Redis service
brew services start redis

# Verify it's running
redis-cli ping
# Should return: PONG
```

---

## ⚙️ Step 5: Configure Environment Variables

```bash
# Navigate to Sentinel directory
cd ~/sentinel

# Copy example environment file
cp .env.example .env

# Edit the .env file
nano .env
```

Update these values:

```bash
# Database
DATABASE_URL=postgresql://sentinel_user:your_password_here@localhost:5432/sentinel

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# API
APP_NAME="Sentinel"
APP_VERSION="1.0.0"
API_V1_PREFIX="/api/v1"
DEBUG=True

# CORS (for frontend)
CORS_ORIGINS=["http://localhost:5173", "http://localhost:8080"]

# Secret key (generate a random string)
SECRET_KEY=your-secret-key-here-change-this-in-production
```

Save with `Ctrl+O`, then `Enter`, then `Ctrl+X`.

---

## 🚀 Step 6: Initialize the Database

```bash
# Make sure you're in the Sentinel directory
cd ~/sentinel

# Run database initialization script
python3 scripts/init_db.py
```

You should see:
```
✅ Database initialized successfully
✅ Created tables
✅ Created sample client
```

---

## 🎯 Step 7: Generate Synthetic Data (Test the Generator!)

```bash
# Generate 10,000 transactions with 10% fraud rate
python3 scripts/generate_synthetic_data.py --count 10000 --fraud-rate 0.10

# This will create: synthetic_transactions.csv
```

You should see:
```
🇳🇬  SENTINEL SYNTHETIC DATA GENERATOR
========================================
🔄 Generating 10,000 transactions (10.0% fraud rate)...
📊 Industries: fintech, ecommerce, betting, crypto, marketplace
  Generated 1,000 transactions...
  Generated 2,000 transactions...
  ...
✅ Generated 10,000 transactions
   Fraudulent: 1,000 (10.0%)
   Legitimate: 9,000 (90.0%)

💾 Saving to synthetic_transactions.csv...
✅ Saved 10,000 transactions to synthetic_transactions.csv
```

---

## 🏃 Step 8: Start the API Server

```bash
# Start Sentinel API
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

You should see:
```
✅ Rate limiting enabled (Redis connected)
🚀 Sentinel v1.0.0 starting up...
📚 API documentation: http://localhost:8080/docs
🏥 Health check: http://localhost:8080/health

INFO:     Uvicorn running on http://0.0.0.0:8080
```

**Keep this terminal window open** - the API is running!

---

## 🧪 Step 9: Test the API

Open a **new terminal window** (keep the server running) and test:

### Test 1: Health Check

```bash
curl http://localhost:8080/health
```

Should return:
```json
{
  "status": "ok",
  "version": "1.0.0",
  "database": "ok",
  "redis": "ok",
  "timestamp": "2024-01-15T12:00:00.000000"
}
```

### Test 2: Check Transaction (Single)

```bash
curl -X POST http://localhost:8080/api/v1/check-transaction \
  -H "Content-Type: application/json" \
  -H "X-API-Key: pro_test123" \
  -d '{
    "transaction_id": "test_001",
    "user_id": "user_123",
    "amount": 500000,
    "transaction_type": "loan_disbursement",
    "device_id": "iphone_abc123",
    "ip_address": "197.210.52.34",
    "account_age_days": 2,
    "transaction_count": 0,
    "phone_changed_recently": true
  }'
```

Should return fraud detection result:
```json
{
  "transaction_id": "test_001",
  "risk_score": 75,
  "risk_level": "high",
  "decision": "decline",
  "flags": [
    {
      "type": "new_account_large_amount",
      "severity": "medium",
      "message": "Account only 2 days old requesting ₦500,000",
      "score": 30
    },
    {
      "type": "sim_swap_pattern",
      "severity": "critical",
      "message": "Phone changed + new device + withdrawal - classic SIM swap pattern",
      "score": 45
    }
  ]
}
```

### Test 3: Rate Limiting

```bash
# Send 105 requests quickly (limit is 100/min for pro tier)
for i in {1..105}; do
  curl -H "X-API-Key: starter_test123" http://localhost:8080/api/v1/check-transaction \
       -d '{"transaction_id":"test_'$i'", "user_id":"user_123", "amount":50000}' \
       -H "Content-Type: application/json"
done

# First 100 should succeed
# Last 5 should return: 429 Too Many Requests
```

---

## 📊 Step 10: View API Documentation

Open your browser and go to:

**http://localhost:8080/docs**

You'll see interactive API documentation where you can:
- View all endpoints
- Test API calls directly in browser
- See request/response schemas
- Try the batch API

---

## 🎨 Step 11: Start the Frontend (Optional)

If you want the beautiful 3D dashboard:

```bash
# Open a NEW terminal window
cd ~/sentinel/frontend

# Install dependencies (first time only)
npm install

# Start frontend dev server
npm run dev
```

You should see:
```
  VITE v5.x.x  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

Open **http://localhost:5173** in your browser to see the dashboard!

---

## 🔧 Troubleshooting

### Issue: "Command not found: python3"

```bash
# Create alias
echo 'alias python3=/usr/local/bin/python3' >> ~/.zshrc
source ~/.zshrc
```

### Issue: "Cannot connect to database"

```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# If not running, start it
brew services start postgresql@15

# Test connection
psql -U sentinel_user -d sentinel
```

### Issue: "Cannot connect to Redis"

```bash
# Check if Redis is running
brew services list | grep redis

# If not running, start it
brew services start redis

# Test connection
redis-cli ping
```

### Issue: "Module not found"

```bash
# Make sure you're in the right directory
cd ~/sentinel

# Reinstall packages
pip3 install -r requirements.txt
```

### Issue: "Port 8080 already in use"

```bash
# Find what's using port 8080
lsof -i :8080

# Kill the process
kill -9 <PID>

# Or use a different port
python3 -m uvicorn app.main:app --reload --port 8081
```

---

## 📝 Quick Reference Commands

### Start Everything

```bash
# Terminal 1: Start API
cd ~/sentinel
python3 -m uvicorn app.main:app --reload --port 8080

# Terminal 2: Start Frontend (optional)
cd ~/sentinel/frontend
npm run dev
```

### Stop Everything

```bash
# Stop API: Ctrl+C in Terminal 1
# Stop Frontend: Ctrl+C in Terminal 2

# Stop background services
brew services stop postgresql@15
brew services stop redis
```

### Generate More Data

```bash
# Generate 50,000 transactions
python3 scripts/generate_synthetic_data.py --count 50000

# Generate only fintech and e-commerce
python3 scripts/generate_synthetic_data.py --count 10000 --industries fintech,ecommerce

# Generate with 20% fraud rate
python3 scripts/generate_synthetic_data.py --count 10000 --fraud-rate 0.20

# Generate to JSON instead of CSV
python3 scripts/generate_synthetic_data.py --count 5000 --format json
```

---

## 🎯 Next Steps

Now that everything is set up:

1. **✅ Generate synthetic data** - You can do this right now!
2. **✅ Test the API** - Send some fraud checks
3. **✅ View the dashboard** - See fraud detection in action
4. **⏭️ Train ML model** - Use synthetic data to train
5. **⏭️ Find beta customers** - Get real data

---

## 💡 Pro Tips

### Use iTerm2 (Better Terminal)

```bash
# Install iTerm2
brew install --cask iterm2
```

### Use VS Code for Editing

```bash
# Install VS Code
brew install --cask visual-studio-code

# Open Sentinel in VS Code
cd ~/sentinel
code .
```

### Monitor Redis

```bash
# Watch Redis in real-time
redis-cli monitor

# Check rate limiting keys
redis-cli keys "rate_limit:*"

# Check cache keys
redis-cli keys "fraud_check_cache:*"
```

### Monitor PostgreSQL

```bash
# Connect to database
psql sentinel

# View tables
\dt

# View recent transactions
SELECT * FROM transactions ORDER BY created_at DESC LIMIT 10;

# Count fraud vs legitimate
SELECT is_fraud, COUNT(*) FROM transactions GROUP BY is_fraud;
```

---

## 🚀 You're All Set!

Your Mac is now fully set up with Sentinel. You can:

✅ Generate unlimited synthetic data
✅ Run fraud detection API
✅ Test all 3 critical features (rate limiting, caching, batch API)
✅ View beautiful 3D dashboard
✅ Train ML models

**Ready to generate data?**

```bash
cd ~/sentinel
python3 scripts/generate_synthetic_data.py --count 10000
```

Let's go! 🇳🇬
