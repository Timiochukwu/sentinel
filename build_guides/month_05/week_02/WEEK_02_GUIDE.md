# WEEK 2: Reporting & Export APIs
**Days 120-126 | Month 5**

## Overview
Custom reports and data exports

## Files to Build
- app/api/v1/endpoints/reports.py (285 lines)
- app/api/v1/endpoints/exports.py (225 lines)
- app/services/report_generator.py (310 lines)
- app/services/export_service.py (195 lines)
- app/utils/pdf_generator.py (165 lines)
- app/utils/csv_exporter.py (125 lines)

**Total:** 6 files, ~1,305 lines

## Dependencies Add
```
reportlab==4.0.7
openpyxl==3.1.2
```

## Endpoints
```
GET  /api/v1/reports/fraud-summary
GET  /api/v1/reports/custom
GET  /api/v1/exports/csv
GET  /api/v1/exports/pdf
```

## Testing
```bash
curl -X GET "http://localhost:8000/api/v1/reports/fraud-summary?start_date=2024-01-01" \
  -H "X-API-Key: dev-api-key-12345"

curl -X GET "http://localhost:8000/api/v1/exports/csv?days=30" \
  -H "X-API-Key: dev-api-key-12345" > transactions.csv
```

## Success Criteria
- ✅ Report generation working
- ✅ CSV, PDF, Excel exports
- ✅ Scheduled reports
- ✅ Custom report builder

**End of Week 2 - Month 5**
