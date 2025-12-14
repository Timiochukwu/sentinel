# WEEK 1: Admin Authentication & User Management
**Days 113-119 | Month 5**

## Overview
Build admin panel with RBAC and user management

## Files to Build
- app/api/v1/endpoints/admin.py (245 lines)
- app/api/v1/endpoints/users.py (210 lines)  
- app/services/admin_service.py (185 lines)
- app/services/user_service.py (165 lines)
- app/models/admin.py (95 lines)

**Total:** 5 files, ~900 lines

## Endpoints
```
POST   /api/v1/admin/login
GET    /api/v1/admin/users
POST   /api/v1/admin/users
PUT    /api/v1/admin/users/{id}
DELETE /api/v1/admin/users/{id}
```

## Testing
```bash
# Admin login
curl -X POST http://localhost:8000/api/v1/admin/login \
  -d '{"username": "admin", "password": "admin123"}'

# Get users  
curl -X GET http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer $ADMIN_TOKEN"
```

## Success Criteria
- ✅ Admin authentication working
- ✅ User CRUD complete
- ✅ Role-based access control  
- ✅ Audit logging enabled

**End of Week 1 - Month 5**
