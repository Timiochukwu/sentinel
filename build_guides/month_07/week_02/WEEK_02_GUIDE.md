# WEEK 2: Performance & Load Testing
**Days 176-182 | Month 7**

## Overview
Load testing with Locust

## Files to Build
- tests/performance/locustfile.py (285 lines)
- tests/performance/test_api_performance.py (195 lines)
- tests/performance/test_db_performance.py (165 lines)
- tests/stress/stress_test.py (215 lines)

**Total:** 4 files, ~860 lines

## Dependencies Add
```
locust==2.18.0
pytest-benchmark==4.0.0
```

## Running Load Tests
```bash
locust -f tests/performance/locustfile.py \
  --host=http://localhost:8000 \
  --users 100 --spawn-rate 10
```

## Performance Targets
- ✅ API Response: < 200ms (p95)
- ✅ Throughput: > 1000 req/sec
- ✅ DB Queries: < 50ms (p95)

**End of Week 2 - Month 7**
