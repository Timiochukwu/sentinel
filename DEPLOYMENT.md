# Deployment Guide - Sentinel Fraud Detection Platform

## Quick Start (Development)

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (recommended)

### 2. Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd sentinel

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Initialize database
docker-compose exec api python scripts/init_db.py

# Check logs
docker-compose logs -f api
```

The API will be available at `http://localhost:8000`

### 3. Manual Setup (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL
createdb sentinel
# Update DATABASE_URL in .env

# Start Redis
redis-server

# Initialize database
python scripts/init_db.py

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

### Railway.app Deployment

1. **Create Railway Account**
   - Go to https://railway.app
   - Sign up with GitHub

2. **Deploy from GitHub**
   ```bash
   # Push to GitHub
   git add .
   git commit -m "Initial commit"
   git push origin main

   # On Railway
   - New Project → Deploy from GitHub
   - Select repository
   - Railway will auto-detect Dockerfile
   ```

3. **Add Services**
   ```
   - Add PostgreSQL database
   - Add Redis
   - Railway will provide connection URLs
   ```

4. **Configure Environment Variables**
   ```
   DATABASE_URL=<from Railway PostgreSQL>
   REDIS_URL=<from Railway Redis>
   SECRET_KEY=<generate secure key>
   ENVIRONMENT=production
   DEBUG=false
   ```

5. **Deploy**
   ```
   Railway will auto-deploy on git push
   ```

### AWS Deployment

#### Using ECS (Elastic Container Service)

1. **Build and Push Docker Image**
   ```bash
   # Build
   docker build -t sentinel-api .

   # Tag for ECR
   docker tag sentinel-api:latest <aws-account-id>.dkr.ecr.<region>.amazonaws.com/sentinel-api:latest

   # Push to ECR
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com
   docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/sentinel-api:latest
   ```

2. **Create RDS PostgreSQL Instance**
   - Engine: PostgreSQL 15
   - Instance class: db.t3.small (development) or db.r5.large (production)
   - Storage: 100GB SSD
   - Enable automated backups

3. **Create ElastiCache Redis**
   - Engine: Redis 7
   - Node type: cache.t3.micro (development) or cache.r5.large (production)

4. **Create ECS Task Definition**
   ```json
   {
     "family": "sentinel-api",
     "networkMode": "awsvpc",
     "containerDefinitions": [
       {
         "name": "sentinel-api",
         "image": "<ecr-image-url>",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "DATABASE_URL",
             "value": "<rds-connection-string>"
           },
           {
             "name": "REDIS_URL",
             "value": "<elasticache-connection-string>"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/sentinel-api",
             "awslogs-region": "<region>",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ],
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "512",
     "memory": "1024"
   }
   ```

5. **Create ECS Service**
   - Launch type: Fargate
   - Desired tasks: 2 (for high availability)
   - Load balancer: Application Load Balancer
   - Health check: `/health`

6. **Set up Auto Scaling**
   ```
   - Target tracking scaling policy
   - Metric: CPU utilization
   - Target value: 70%
   - Min tasks: 2
   - Max tasks: 10
   ```

### Environment Variables (Production)

```bash
# Application
APP_NAME=Sentinel Fraud Detection
APP_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<generate-long-random-string>

# Database
DATABASE_URL=postgresql://user:password@host:5432/sentinel
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://host:6379/0
REDIS_MAX_CONNECTIONS=50

# Security
CORS_ORIGINS=["https://yourdomain.com"]

# Monitoring
SENTRY_DSN=<your-sentry-dsn>
ENABLE_METRICS=true
```

## Performance Tuning

### PostgreSQL Optimization

```sql
-- Increase shared buffers (25% of RAM)
ALTER SYSTEM SET shared_buffers = '2GB';

-- Increase work memory
ALTER SYSTEM SET work_mem = '64MB';

-- Enable parallel queries
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;

-- Reload configuration
SELECT pg_reload_conf();
```

### Redis Configuration

```
# /etc/redis/redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save ""  # Disable RDB snapshots for performance
```

### Application Optimization

```bash
# Run with multiple workers
uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# Or use gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Monitoring & Logging

### Sentry Integration

```bash
# Already integrated in app/main.py
# Just set SENTRY_DSN in environment variables
```

### CloudWatch Logs (AWS)

```bash
# View logs
aws logs tail /ecs/sentinel-api --follow

# Create metric filters
aws logs put-metric-filter \
  --log-group-name /ecs/sentinel-api \
  --filter-name HighRiskTransactions \
  --filter-pattern '[... risk_level = "high"]' \
  --metric-transformations \
    metricName=HighRiskCount,metricNamespace=Sentinel,metricValue=1
```

### Prometheus Metrics

```python
# Metrics exposed at /metrics endpoint
# Scrape with Prometheus:

# prometheus.yml
scrape_configs:
  - job_name: 'sentinel-api'
    static_configs:
      - targets: ['api:8000']
```

## Backup & Recovery

### Database Backups

```bash
# Automated daily backups
0 2 * * * pg_dump -U sentinel sentinel | gzip > /backups/sentinel_$(date +\%Y\%m\%d).sql.gz

# Restore from backup
gunzip < backup.sql.gz | psql -U sentinel sentinel
```

### Disaster Recovery

1. **RTO (Recovery Time Objective)**: < 1 hour
2. **RPO (Recovery Point Objective)**: < 15 minutes
3. **Strategy**:
   - Use AWS RDS automated backups (point-in-time recovery)
   - Multi-AZ deployment for high availability
   - Cross-region replication for disaster recovery

## Security Checklist

- [ ] Use HTTPS/TLS for all connections
- [ ] Rotate API keys regularly
- [ ] Enable database encryption at rest
- [ ] Set up VPC with private subnets
- [ ] Use AWS Secrets Manager for sensitive data
- [ ] Enable CloudTrail for audit logging
- [ ] Set up WAF (Web Application Firewall)
- [ ] Regular security audits and penetration testing
- [ ] Keep dependencies updated (Dependabot)

## Cost Estimation (AWS)

### Development Environment
- ECS Fargate (1 task): ~$15/month
- RDS db.t3.small: ~$25/month
- ElastiCache cache.t3.micro: ~$15/month
- **Total: ~$55/month**

### Production Environment
- ECS Fargate (4 tasks): ~$120/month
- RDS db.r5.large: ~$200/month
- ElastiCache cache.r5.large: ~$150/month
- ALB: ~$20/month
- Data transfer: ~$50/month
- **Total: ~$540/month**

## Support

For deployment support:
- Email: support@sentinel-fraud.com
- Slack: sentinel-community.slack.com
- Documentation: https://docs.sentinel-fraud.com
