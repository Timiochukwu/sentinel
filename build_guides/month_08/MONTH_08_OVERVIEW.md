# MONTH 8: OPTIMIZATION & SCALING

## Overview
Month 8 focuses on performance optimization and horizontal scaling:
- Database query optimization and indexing
- Caching strategies and Redis optimization
- API performance tuning
- Horizontal scaling preparation

**Total for Month 8:** ~1,800 lines of code

---

## Week 1: Database Optimization
**Days 197-203**

### Files to Build
```
alembic/versions/
├── add_indexes.py                 # 185 lines - Database indexes

app/db/
├── query_optimizer.py             # 225 lines - Query optimization
└── connection_pool.py             # 145 lines - Connection pooling

scripts/
├── analyze_queries.py             # 195 lines - Query analysis
└── optimize_db.py                 # 165 lines - DB optimization
```

**Total:** 5 files, ~915 lines

### Key Optimizations
- Add indexes on frequently queried columns
- Optimize N+1 query problems
- Implement database connection pooling
- Add query result caching

### Database Indexes
```sql
-- Add indexes for common queries
CREATE INDEX idx_transactions_user_id ON transactions(user_id);
CREATE INDEX idx_transactions_created_at ON transactions(created_at DESC);
CREATE INDEX idx_transactions_status ON transactions(status);
CREATE INDEX idx_transactions_fraud_score ON transactions(fraud_score DESC);
CREATE INDEX idx_fraud_flags_transaction_id ON fraud_flags(transaction_id);
CREATE INDEX idx_fraud_flags_severity ON fraud_flags(severity);

-- Composite indexes for complex queries
CREATE INDEX idx_transactions_user_date ON transactions(user_id, created_at DESC);
CREATE INDEX idx_transactions_industry_status ON transactions(industry, status);

-- JSONB indexes for metadata queries
CREATE INDEX idx_transactions_metadata ON transactions USING GIN (metadata);
```

### Query Optimization Examples
```python
# Before: N+1 query problem
def get_transactions_with_flags():
    transactions = db.query(Transaction).all()
    for txn in transactions:
        flags = db.query(FraudFlag).filter(
            FraudFlag.transaction_id == txn.id
        ).all()  # N+1 queries!

# After: Eager loading
def get_transactions_with_flags_optimized():
    transactions = db.query(Transaction).options(
        joinedload(Transaction.fraud_flags)
    ).all()  # Single query with JOIN
```

### Performance Targets
```
✅ Query execution time: < 50ms (p95)
✅ Database connections: Pool of 20-50
✅ Index usage: 90%+ of queries use indexes
✅ Lock contention: < 1% wait time
```

---

## Week 2: Caching Strategies
**Days 204-210**

### Files to Build
```
app/services/
├── cache_strategy.py              # 265 lines - Caching strategies
├── cache_invalidation.py          # 195 lines - Cache invalidation
└── distributed_cache.py           # 185 lines - Distributed caching

app/middleware/
└── cache_middleware.py            # 165 lines - HTTP caching

scripts/
└── cache_warmup.py                # 125 lines - Cache warming
```

**Total:** 5 files, ~935 lines

### Caching Layers
1. **Application Cache** (Redis)
   - User data (TTL: 1 hour)
   - Rule configurations (TTL: 24 hours)
   - ML model predictions (TTL: 5 minutes)

2. **HTTP Cache** (Response caching)
   - Dashboard stats (TTL: 1 minute)
   - Reports (TTL: 5 minutes)
   - Static data (TTL: 1 hour)

3. **Database Query Cache**
   - Frequently accessed queries (TTL: 10 minutes)

### Cache Implementation
```python
# cache_strategy.py
from functools import wraps
import hashlib

def cache_result(ttl: int = 300):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{_hash_args(args, kwargs)}"

            # Check cache
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = func(*args, **kwargs)

            # Store in cache
            redis.setex(cache_key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator

# Usage
@cache_result(ttl=3600)
def get_user_profile(user_id: str):
    return db.query(User).filter(User.user_id == user_id).first()
```

### Cache Warming
```python
# Warm up cache on startup
def warm_cache():
    """Pre-populate cache with frequently accessed data"""

    # Cache rule configurations
    for industry in ['fintech', 'lending', 'crypto']:
        get_vertical_rules(industry)

    # Cache dashboard stats
    get_dashboard_stats()

    # Cache top users
    get_top_users_by_volume()
```

### Performance Targets
```
✅ Cache hit rate: > 80%
✅ Cache response time: < 5ms
✅ Memory usage: < 2GB Redis
✅ Cache invalidation: < 1 second
```

---

## Week 3: API Performance Tuning
**Days 211-217**

### Files to Build
```
app/middleware/
├── compression.py                 # 125 lines - Response compression
└── request_optimization.py        # 145 lines - Request optimization

app/api/
├── pagination.py                  # 165 lines - Efficient pagination
└── field_filtering.py             # 135 lines - Response filtering

scripts/
├── benchmark_api.py               # 185 lines - API benchmarking
└── profile_endpoints.py           # 145 lines - Endpoint profiling
```

**Total:** 6 files, ~900 lines

### Optimizations
1. **Response Compression** (gzip)
2. **Pagination** (cursor-based)
3. **Field Filtering** (GraphQL-style)
4. **Request Batching**
5. **Connection Keep-Alive**

### Pagination Optimization
```python
# Before: Offset pagination (slow for large datasets)
@router.get("/transactions")
def get_transactions(skip: int = 0, limit: int = 100):
    return db.query(Transaction).offset(skip).limit(limit).all()
    # OFFSET 10000 becomes very slow!

# After: Cursor-based pagination (fast for all pages)
@router.get("/transactions")
def get_transactions(cursor: str = None, limit: int = 100):
    query = db.query(Transaction).order_by(Transaction.created_at.desc())

    if cursor:
        # Decode cursor to get last seen timestamp
        cursor_time = decode_cursor(cursor)
        query = query.filter(Transaction.created_at < cursor_time)

    transactions = query.limit(limit + 1).all()

    # Generate next cursor
    has_more = len(transactions) > limit
    next_cursor = encode_cursor(transactions[limit-1].created_at) if has_more else None

    return {
        'transactions': transactions[:limit],
        'next_cursor': next_cursor,
        'has_more': has_more
    }
```

### Response Compression
```python
# Add gzip middleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
# Responses > 1KB are compressed (70-90% size reduction)
```

### Performance Targets
```
✅ Response size: 70% reduction (gzip)
✅ Pagination: O(1) for all pages
✅ Field filtering: 50% response size reduction
✅ API latency: < 100ms (p95)
```

---

## Week 4: Horizontal Scaling Preparation
**Days 218-224**

### Files to Build
```
docker/
├── Dockerfile                     # 95 lines - App container
├── docker-compose.yml             # 145 lines - Multi-container
└── docker-compose.prod.yml        # 165 lines - Production setup

kubernetes/
├── deployment.yml                 # 185 lines - K8s deployment
├── service.yml                    # 75 lines - K8s service
├── ingress.yml                    # 95 lines - Ingress config
└── configmap.yml                  # 65 lines - Configuration

scripts/
├── scale_workers.sh               # 85 lines - Worker scaling
└── health_check.py                # 105 lines - Health checks
```

**Total:** 9 files, ~1,015 lines

### Docker Setup
```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY scripts/ ./scripts/

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (Production)
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/sentinel
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis
    deploy:
      replicas: 3  # Horizontal scaling
      resources:
        limits:
          cpus: '1'
          memory: 1G

  postgres:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=secret

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api

volumes:
  pgdata:
```

### Kubernetes Deployment
```yaml
# kubernetes/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sentinel-api
spec:
  replicas: 3  # Horizontal scaling
  selector:
    matchLabels:
      app: sentinel-api
  template:
    metadata:
      labels:
        app: sentinel-api
    spec:
      containers:
      - name: api
        image: sentinel-api:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Scaling Strategy
```bash
# Docker Compose scaling
docker-compose up --scale api=5

# Kubernetes horizontal pod autoscaling
kubectl autoscale deployment sentinel-api \
  --cpu-percent=70 \
  --min=3 \
  --max=10
```

### Performance Targets
```
✅ Horizontal scaling: Support 3-10 instances
✅ Load balancing: Round-robin across instances
✅ Session affinity: Stateless design
✅ Health checks: < 1 second response
✅ Zero-downtime deployments: Rolling updates
```

---

## Success Criteria

By end of Month 8:
- ✅ Database queries optimized (< 50ms p95)
- ✅ Caching hit rate > 80%
- ✅ API response time < 100ms (p95)
- ✅ Docker containers production-ready
- ✅ Kubernetes deployment configured
- ✅ Can scale to 10+ instances

---

**End of Month 8 Overview**
