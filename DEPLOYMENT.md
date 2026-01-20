# SentinelRisk Production Deployment Guide

## Overview
This guide covers deploying the production-ready SentinelRisk fraud detection system with all security, monitoring, and scalability features.

## Prerequisites

### Infrastructure Requirements
- **Docker & Docker Compose** (latest versions)
- **PostgreSQL 15+** (or managed service)
- **Redis 7+** (for caching and rate limiting)
- **Load Balancer** (nginx/HAProxy/cloud load balancer)
- **SSL Certificates** (for HTTPS)

### System Requirements
- **Minimum**: 4 CPU cores, 8GB RAM, 50GB storage
- **Recommended**: 8 CPU cores, 16GB RAM, 100GB storage
- **High Availability**: Multiple nodes with shared database

## Quick Start Deployment

### 1. Environment Setup

```bash
# Clone the repository
git clone <repository-url>
cd SentinelRisk

# Copy environment template
cp .env.example .env

# Generate secure secrets
openssl rand -hex 32  # For SECRET_KEY
openssl rand -hex 16  # For POSTGRES_PASSWORD
```

### 2. Configure Environment

Edit `.env` file with your production values:

```bash
# Security
SECRET_KEY=your-32-character-secret-key-here
POSTGRES_PASSWORD=your-secure-postgres-password

# Database
DATABASE_URL=postgresql+asyncpg://sentinel_user:your-password@postgres:5432/sentinelrisk

# Monitoring (optional)
SENTRY_DSN=https://your-sentry-dsn
GRAFANA_PASSWORD=your-grafana-admin-password

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### 3. Deploy with Docker Compose

```bash
# Deploy all services
docker-compose -f docker-compose.prod.yml up -d

# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f api
```

### 4. Initialize System

```bash
# Wait for services to be ready
sleep 30

# Create admin user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@company.com",
    "password": "SecurePass123!",
    "full_name": "System Administrator",
    "role": "admin"
  }'

# Test health endpoint
curl http://localhost:8000/health
```

## Production Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│     Nginx       │────│   API Gateway   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │   Prometheus    │◄────────────┤
                       └─────────────────┘             │
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│     Redis       │────│   PostgreSQL    │◄────────────┤
│   (Caching)     │    │   (Database)    │             │
└─────────────────┘    └─────────────────┘             │
                                                        │
┌─────────────────┐    ┌─────────────────┐             │
│     Grafana     │────│   Sentry        │             │
│ (Visualization) │    │ (Error Tracking)│             │
└─────────────────┘    └─────────────────┘             │
                                                        ▼
                                         ┌─────────────────┐
                                         │  SentinelRisk   │
                                         │   API Cluster   │
                                         └─────────────────┘
```

## Security Configuration

### SSL/TLS Setup
```bash
# Generate SSL certificates (Let's Encrypt recommended)
certbot certonly --webroot -w /var/www/html -d yourdomain.com

# Update nginx configuration
cp nginx/nginx.conf.example nginx/nginx.conf
# Edit with your SSL paths
```

### Firewall Rules
```bash
# Allow only necessary ports
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw allow 22/tcp    # SSH (restricted)
ufw deny 8000/tcp   # Direct API access
ufw enable
```

### Database Security
```sql
-- Create database user with limited permissions
CREATE USER sentinel_user WITH PASSWORD 'secure_password';
GRANT CONNECT ON DATABASE sentinelrisk TO sentinel_user;
GRANT USAGE ON SCHEMA public TO sentinel_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sentinel_user;
```

## Monitoring Setup

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'sentinelrisk'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s
```

### Grafana Dashboards
1. Access Grafana: `http://localhost:3000`
2. Login with admin credentials
3. Import pre-configured dashboards from `monitoring/grafana/dashboards/`

### Sentry Integration
```bash
# Set Sentry DSN in environment
export SENTRY_DSN="https://your-sentry-dsn"

# Test error tracking
curl -X POST "http://localhost:8000/test-error"
```

## Performance Optimization

### Database Optimization
```sql
-- Create indexes for performance
CREATE INDEX idx_prediction_logs_timestamp ON prediction_logs(timestamp);
CREATE INDEX idx_prediction_logs_decision ON prediction_logs(decision);
CREATE INDEX idx_review_queue_status ON review_queue(status);
CREATE INDEX idx_review_queue_priority ON review_queue(priority);

-- Analyze table statistics
ANALYZE prediction_logs;
ANALYZE review_queue;
```

### API Performance
```python
# Enable connection pooling in settings
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Configure Redis for caching
REDIS_URL=redis://redis:6379/0
```

### Load Testing
```bash
# Install k6
curl https://github.com/grafana/k6/releases/download/v0.47.0/k6-v0.47.0-linux-amd64.tar.gz | tar xvz

# Run load test
./k6 run --vus 100 --duration 30s tests/load_test.js
```

## Backup and Recovery

### Database Backups
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker exec postgres pg_dump -U sentinel_user sentinelrisk > backup_$DATE.sql
gzip backup_$DATE.sql
aws s3 cp backup_$DATE.sql.gz s3://your-backup-bucket/
EOF

# Schedule daily backups
echo "0 2 * * * /path/to/backup.sh" | crontab -
```

### Model Backups
```bash
# Backup model artifacts
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/
aws s3 cp models_backup_$(date +%Y%m%d).tar.gz s3://your-backup-bucket/
```

## Scaling Strategies

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  api:
    scale: 3  # Run 3 API instances
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 2G
```

### Database Scaling
- **Read Replicas**: For read-heavy workloads
- **Connection Pooling**: PgBouncer for connection management
- **Partitioning**: By date for large datasets

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database status
   docker-compose exec postgres pg_isready
   
   # Check connection logs
   docker-compose logs postgres
   ```

2. **High Memory Usage**
   ```bash
   # Monitor memory usage
   docker stats
   
   # Adjust container limits
   docker-compose -f docker-compose.prod.yml up -d --scale api=2
   ```

3. **Rate Limiting Issues**
   ```bash
   # Check Redis status
   docker-compose exec redis redis-cli ping
   
   # Monitor rate limit usage
   curl -H "X-API-KEY: your-key" http://localhost:8000/metrics
   ```

### Health Checks
```bash
# API Health
curl http://localhost:8000/health

# Database Health
docker-compose exec postgres pg_isready -U sentinel_user

# Redis Health
docker-compose exec redis redis-cli ping
```

## Maintenance

### Regular Tasks
- **Daily**: Review error logs in Sentry
- **Weekly**: Check performance metrics in Grafana
- **Monthly**: Update dependencies and security patches
- **Quarterly**: Model retraining and performance evaluation

### Security Updates
```bash
# Update Docker images
docker-compose pull

# Restart services
docker-compose -f docker-compose.prod.yml up -d

# Check for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image sentinelrisk_api:latest
```

## Support and Monitoring

### Alert Configuration
- **High error rate**: > 5% for 5 minutes
- **High latency**: P95 > 1 second
- **Database connections**: > 80% of pool
- **Memory usage**: > 85% of available

### Emergency Procedures
1. **Service Outage**: Check health endpoints first
2. **Database Issues**: Switch to read replica if available
3. **High Load**: Scale API instances horizontally
4. **Security Incident**: Review audit logs immediately

## Next Steps

After deployment:
1. **Configure monitoring alerts**
2. **Set up backup procedures**
3. **Create user onboarding process**
4. **Document API usage for clients**
5. **Plan regular model retraining schedule**

For technical support, check the logs in `/logs` directory or contact the development team.
