# MONTH 9: DEPLOYMENT & DEVOPS

## Overview
Month 9 focuses on production deployment and DevOps infrastructure:
- Infrastructure as Code (Terraform/CloudFormation)
- CI/CD pipelines for automated deployment
- Monitoring and observability
- Backup and disaster recovery

**Total for Month 9:** ~2,100 lines of infrastructure code

---

## Week 1: Infrastructure as Code
**Days 225-231**

### Files to Build
```
terraform/
├── main.tf                        # 185 lines - Main infrastructure
├── variables.tf                   # 95 lines - Variables
├── outputs.tf                     # 75 lines - Outputs
├── vpc.tf                         # 145 lines - VPC setup
├── rds.tf                         # 165 lines - Database
├── elasticache.tf                 # 125 lines - Redis
├── ecs.tf                         # 245 lines - Container service
└── alb.tf                         # 155 lines - Load balancer

terraform/modules/
├── network/
│   └── main.tf                    # 125 lines
└── database/
    └── main.tf                    # 145 lines
```

**Total:** 10 files, ~1,460 lines

### Infrastructure Components
- **VPC**: Private/public subnets across 3 AZs
- **RDS**: PostgreSQL Multi-AZ deployment
- **ElastiCache**: Redis cluster
- **ECS**: Fargate containers
- **ALB**: Application load balancer
- **S3**: Static assets and backups
- **CloudWatch**: Logging and monitoring

### Terraform Configuration
```hcl
# main.tf
terraform {
  required_version = ">= 1.0"

  backend "s3" {
    bucket = "sentinel-terraform-state"
    key    = "prod/terraform.tfstate"
    region = "us-east-1"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Module
module "vpc" {
  source = "./modules/network"

  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets    = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

# RDS PostgreSQL
resource "aws_db_instance" "sentinel" {
  identifier             = "sentinel-postgres"
  engine                = "postgres"
  engine_version        = "15.4"
  instance_class        = "db.t3.large"
  allocated_storage     = 100
  storage_type          = "gp3"
  db_name               = "sentinel"
  username              = var.db_username
  password              = var.db_password
  multi_az              = true
  publicly_accessible   = false
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name  = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "sentinel-final-snapshot-${timestamp()}"
}

# ECS Cluster
resource "aws_ecs_cluster" "sentinel" {
  name = "sentinel-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "api" {
  family                   = "sentinel-api"
  network_mode            = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                     = "1024"
  memory                  = "2048"

  container_definitions = jsonencode([{
    name  = "sentinel-api"
    image = "${var.ecr_repository}:latest"
    portMappings = [{
      containerPort = 8000
      protocol      = "tcp"
    }]
    environment = [
      {
        name  = "DATABASE_URL"
        value = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.sentinel.endpoint}/sentinel"
      },
      {
        name  = "REDIS_URL"
        value = "redis://${aws_elasticache_cluster.sentinel.cache_nodes[0].address}:6379/0"
      }
    ]
    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/sentinel-api"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}
```

### Deployment
```bash
# Initialize Terraform
cd terraform
terraform init

# Plan infrastructure
terraform plan -out=tfplan

# Apply infrastructure
terraform apply tfplan

# Outputs
terraform output
```

---

## Week 2: CI/CD Pipeline
**Days 232-238**

### Files to Build
```
.github/workflows/
├── deploy-prod.yml                # 245 lines - Production deploy
├── deploy-staging.yml             # 215 lines - Staging deploy
└── docker-build.yml               # 185 lines - Docker build

scripts/deploy/
├── deploy.sh                      # 165 lines - Deployment script
├── rollback.sh                    # 125 lines - Rollback script
├── smoke_test.sh                  # 95 lines - Smoke tests
└── blue_green_deploy.sh           # 145 lines - Blue/green deploy
```

**Total:** 7 files, ~1,175 lines

### Deployment Pipeline
1. **Build Stage**
   - Run tests
   - Build Docker image
   - Push to ECR

2. **Deploy Stage**
   - Run database migrations
   - Deploy new task definition
   - Run smoke tests
   - Route traffic

3. **Verify Stage**
   - Health checks
   - Monitoring alerts
   - Rollback if needed

### GitHub Actions Pipeline
```yaml
# .github/workflows/deploy-prod.yml
name: Deploy to Production

on:
  push:
    branches: [main]

env:
  AWS_REGION: us-east-1
  ECR_REPOSITORY: sentinel-api
  ECS_CLUSTER: sentinel-cluster
  ECS_SERVICE: sentinel-api-service

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
          docker tag $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:latest
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ${{ env.AWS_REGION }}

      - name: Run database migrations
        run: |
          # Run migrations in ECS task
          aws ecs run-task \
            --cluster ${{ env.ECS_CLUSTER }} \
            --task-definition sentinel-migration \
            --launch-type FARGATE

      - name: Deploy to ECS
        run: |
          aws ecs update-service \
            --cluster ${{ env.ECS_CLUSTER }} \
            --service ${{ env.ECS_SERVICE }} \
            --force-new-deployment

      - name: Wait for deployment
        run: |
          aws ecs wait services-stable \
            --cluster ${{ env.ECS_CLUSTER }} \
            --services ${{ env.ECS_SERVICE }}

      - name: Run smoke tests
        run: |
          ./scripts/deploy/smoke_test.sh https://api.sentinel.com
```

---

## Week 3: Monitoring & Observability
**Days 239-245**

### Files to Build
```
monitoring/
├── prometheus.yml                 # 125 lines - Prometheus config
├── grafana/
│   ├── dashboards/
│   │   ├── api_dashboard.json     # 445 lines - API metrics
│   │   └── fraud_dashboard.json   # 385 lines - Fraud metrics
│   └── datasources.yml            # 65 lines - Data sources
└── alerts/
    ├── api_alerts.yml             # 185 lines - API alerts
    └── fraud_alerts.yml           # 165 lines - Fraud alerts

scripts/monitoring/
├── setup_monitoring.sh            # 145 lines - Setup script
└── alert_rules.py                 # 195 lines - Alert rules
```

**Total:** 8 files, ~1,710 lines

### Monitoring Stack
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **CloudWatch**: AWS-native monitoring
- **PagerDuty**: Incident management
- **Datadog** (optional): APM

### Key Metrics
```yaml
# API Metrics
- Request rate (req/sec)
- Response time (p50, p95, p99)
- Error rate (%)
- Fraud detection rate (%)

# Infrastructure Metrics
- CPU usage (%)
- Memory usage (%)
- Database connections
- Redis memory usage

# Business Metrics
- Total transactions/day
- Fraud detected/day
- Decline rate (%)
- False positive rate (%)
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Sentinel API Metrics",
    "panels": [
      {
        "title": "Request Rate",
        "targets": [{
          "expr": "rate(http_requests_total[5m])"
        }]
      },
      {
        "title": "Response Time (p95)",
        "targets": [{
          "expr": "histogram_quantile(0.95, http_request_duration_seconds)"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
        }]
      }
    ]
  }
}
```

### Alert Rules
```yaml
# alerts/api_alerts.yml
groups:
  - name: api_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} (>5%)"

      - alert: HighLatency
        expr: histogram_quantile(0.95, http_request_duration_seconds) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
          description: "p95 latency is {{ $value }}s (>1s)"

      - alert: LowFraudDetectionRate
        expr: rate(fraud_detected_total[1h]) < 10
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Low fraud detection rate"
          description: "Only {{ $value }} frauds detected in last hour"
```

---

## Week 4: Backup & Disaster Recovery
**Days 246-252**

### Files to Build
```
scripts/backup/
├── backup_database.sh             # 165 lines - DB backup
├── restore_database.sh            # 145 lines - DB restore
├── backup_redis.sh                # 95 lines - Redis backup
└── disaster_recovery.sh           # 185 lines - DR script

terraform/
├── backup.tf                      # 125 lines - Backup config
└── dr.tf                          # 145 lines - DR setup

docs/
├── disaster_recovery_plan.md      # 75 lines - DR plan
└── runbook.md                     # 95 lines - Operations runbook
```

**Total:** 8 files, ~1,030 lines

### Backup Strategy
1. **Database Backups**
   - Automated daily backups (RDS)
   - Point-in-time recovery (7 days)
   - Cross-region replication

2. **Redis Backups**
   - Snapshot every 6 hours
   - AOF persistence enabled

3. **Application State**
   - Model files backed up to S3
   - Configuration backed up

### Backup Script
```bash
# backup_database.sh
#!/bin/bash

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="sentinel_backup_${TIMESTAMP}.sql"

# Create RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier sentinel-postgres \
  --db-snapshot-identifier sentinel-snapshot-${TIMESTAMP}

# Export to S3 (for cross-region backup)
pg_dump $DATABASE_URL | gzip > ${BACKUP_FILE}.gz
aws s3 cp ${BACKUP_FILE}.gz s3://sentinel-backups/database/

# Verify backup
aws rds describe-db-snapshots \
  --db-snapshot-identifier sentinel-snapshot-${TIMESTAMP}

echo "Backup completed: ${BACKUP_FILE}.gz"
```

### Disaster Recovery
```bash
# disaster_recovery.sh
#!/bin/bash

echo "Starting disaster recovery..."

# 1. Restore database from latest snapshot
LATEST_SNAPSHOT=$(aws rds describe-db-snapshots \
  --db-instance-identifier sentinel-postgres \
  --query 'DBSnapshots[0].DBSnapshotIdentifier' \
  --output text)

aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier sentinel-postgres-dr \
  --db-snapshot-identifier $LATEST_SNAPSHOT

# 2. Update DNS to point to DR region
aws route53 change-resource-record-sets \
  --hosted-zone-id Z1234567890ABC \
  --change-batch file://dns_failover.json

# 3. Deploy application to DR region
terraform apply -var-file=dr.tfvars

echo "Disaster recovery complete"
```

---

## Success Criteria

By end of Month 9:
- ✅ Infrastructure fully automated with Terraform
- ✅ CI/CD pipeline deploying to production
- ✅ Zero-downtime deployments
- ✅ Comprehensive monitoring dashboards
- ✅ Alerting configured (PagerDuty)
- ✅ Automated backups (daily)
- ✅ Disaster recovery plan tested

---

**End of Month 9 Overview**
