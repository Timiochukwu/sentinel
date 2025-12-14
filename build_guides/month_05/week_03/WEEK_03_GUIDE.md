# WEEK 3: Batch Processing APIs
**Days 127-133 | Month 5**

## Overview
Batch fraud checks with Celery

## Files to Build
- app/api/v1/endpoints/batch.py (265 lines)
- app/services/batch_processor.py (340 lines)
- app/services/async_tasks.py (215 lines)
- app/workers/celery_app.py (125 lines)

**Total:** 4 files, ~945 lines

## Dependencies Add
```
celery[redis]==5.3.4
flower==2.0.1
```

## Endpoints
```
POST /api/v1/batch/fraud-check
GET  /api/v1/batch/jobs/{job_id}/status
GET  /api/v1/batch/jobs/{job_id}/results
```

## Testing
```bash
# Submit batch job
curl -X POST http://localhost:8000/api/v1/batch/fraud-check \
  -H "Content-Type: application/json" \
  -d '{"transactions": [...]}'

# Check status
curl http://localhost:8000/api/v1/batch/jobs/job_123/status
```

## Success Criteria
- ✅ Batch processing working
- ✅ Celery workers running
- ✅ Job status tracking
- ✅ Can process 1000s of transactions

**End of Week 3 - Month 5**
