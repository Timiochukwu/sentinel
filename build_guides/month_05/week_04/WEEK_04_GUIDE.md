# WEEK 4: Webhook Management
**Days 134-140 | Month 5**

## Overview
Webhook configuration and management

## Files to Build
- app/api/v1/endpoints/webhook_config.py (195 lines)
- app/api/v1/endpoints/settings.py (145 lines)
- app/services/config_service.py (210 lines)
- app/models/webhook_config.py (105 lines)

**Total:** 4 files, ~655 lines

## Endpoints
```
GET    /api/v1/webhooks
POST   /api/v1/webhooks
PUT    /api/v1/webhooks/{id}
DELETE /api/v1/webhooks/{id}
POST   /api/v1/webhooks/{id}/test
```

## Testing
```bash
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://webhook.site/your-url",
    "events": ["fraud_detected"],
    "secret": "webhook_secret"
  }'
```

## Success Criteria
- ✅ Webhook CRUD working
- ✅ Event filtering
- ✅ Webhook testing
- ✅ Retry policies configured

**End of Week 4 - Month 5 Complete!**
