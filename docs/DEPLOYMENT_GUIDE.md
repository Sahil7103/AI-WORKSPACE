# Deployment Guide

Complete guide for deploying AI Workplace Copilot to production.

## Pre-Deployment Checklist

- [ ] Set strong `SECRET_KEY` (min 32 characters)
- [ ] Configure production `DATABASE_URL`
- [ ] Set up production `REDIS_URL`
- [ ] Obtain OpenAI API key (optional)
- [ ] Configure CORS origins correctly
- [ ] Set `DEBUG=False` in environment
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up monitoring and logging
- [ ] Prepare disaster recovery plan
- [ ] Run full test suite
- [ ] Review security settings

## Deployment Options

### 1. Docker Compose (Development/Small Production)

Best for: Getting started, small teams, prototyping

```bash
# Clone repository
git clone https://github.com/yourusername/ai-workplace-copilot.git
cd ai-workplace-copilot

# Create .env file
cp backend/.env.example backend/.env

# Configure production settings
nano backend/.env
# - Set DATABASE_URL
# - Set SECRET_KEY
# - Set OPENAI_API_KEY
# - Set ENVIRONMENT=production

# Start services
cd docker
docker-compose up -d

# Create admin user
docker-compose exec backend python << EOF
from app.services.user_service import UserService
from app.core.database import AsyncSessionLocal
from app.schemas import UserCreate
import asyncio

async def create_admin():
    async with AsyncSessionLocal() as db:
        admin_data = UserCreate(
            username="admin",
            email="admin@example.com",
            password="change_me_now",
            full_name="Administrator"
        )
        admin = await UserService.create_user(db, admin_data)
        admin.role = "admin"
        await db.commit()
        print(f"Admin created: {admin.email}")

asyncio.run(create_admin())
EOF
```

### 2. AWS ECS + RDS + ElastiCache

Best for: Production with auto-scaling

```bash
# 1. Create RDS PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier ai-copilot-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --allocated-storage 100 \
  --master-username aiuser \
  --master-user-password <strong-password>

# 2. Create ElastiCache Redis cluster
aws elasticache create-cache-cluster \
  --cache-cluster-id ai-copilot-cache \
  --cache-node-type cache.t3.micro \
  --engine redis

# 3. Push Docker images to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

docker tag ai-copilot-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-copilot-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-copilot-backend:latest

# 4. Create ECS task definition and service
# See AWS documentation for detailed steps

# 5. Configure CloudFront for frontend
# Point to S3 bucket with frontend static files
```

### 3. Render Deployment

Best for: Small to medium projects, easy setup

#### Backend Service

```bash
# On Render Dashboard:
# 1. New + Web Service
# 2. Connect GitHub repo
# 3. Configure:
#    - Name: ai-copilot-backend
#    - Environment: Python 3.11
#    - Build Command: pip install -r backend/requirements.txt
#    - Start Command: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
#    - Region: Choose closest
#    - Plan: Standard or Pro
```

```
# Environment Variables in Render:
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
```

#### Frontend Service

```bash
# On Render Dashboard:
# 1. New + Static Site
# 2. Connect GitHub or manual deploy
# 3. Configure:
#    - Name: ai-copilot-frontend
#    - Build Command: cd frontend && npm ci && npm run build
#    - Publish Directory: frontend/dist
```

```javascript
// vite.config.js
export default {
  server: {
    proxy: {
      "/api": {
        target: "https://your-backend-url.onrender.com",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
};
```

### 4. Railway Deployment

Best for: Quick staging/production, GitHub integration

```bash
# 1. Connect GitHub repo
# 2. Add services:
#    - PostgreSQL (auto-configured)
#    - Redis (auto-configured)
#    - Backend (Python)
#    - Frontend (Node)

# 3. Configure Backend:
# - Root Directory: backend
# - Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT

# 4. Configure Frontend:
# - Root Directory: frontend
# - Build Command: npm run build
# - Start Command: npm run preview
```

### 5. Heroku Deployment (Legacy)

**Note:** Heroku retired free tier. Use Render/Railway instead.

### 6. Self-Hosted (VPS/Dedicated Server)

Best for: Full control, specific requirements

```bash
# 1. Setup server (Ubuntu 22.04)
ssh root@your-server

# 2. Install dependencies
apt update && apt upgrade -y
apt install python3.11 python3.11-venv python3.11-dev
apt install postgresql postgresql-contrib
apt install redis-server
apt install nodejs npm
apt install nginx certbot python3-certbot-nginx

# 3. Clone and setup
cd /var/www
git clone https://github.com/yourusername/ai-workplace-copilot.git
cd ai-workplace-copilot

# 4. Backend setup
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env

# 5. Create systemd service
sudo nano /etc/systemd/system/ai-copilot-backend.service
```

```ini
[Unit]
Description=AI Copilot Backend
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/ai-workplace-copilot/backend
ExecStart=/var/www/ai-workplace-copilot/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Environment="PATH=/var/www/ai-workplace-copilot/backend/venv/bin"
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 6. Frontend setup
cd ../frontend
npm ci
npm run build

# 7. Setup Nginx
sudo nano /etc/nginx/sites-available/ai-copilot
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 50M;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    # SSL Certificates
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    client_max_body_size 50M;

    # API
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        root /var/www/ai-workplace-copilot/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
# 8. Enable SSL
sudo certbot --nginx -d your-domain.com

# 9. Start services
sudo systemctl enable ai-copilot-backend
sudo systemctl start ai-copilot-backend
sudo systemctl restart nginx

# 10. Monitor
sudo journalctl -u ai-copilot-backend -f
sudo tail -f /var/log/nginx/error.log
```

## Database Migrations

Prepare database for production:

```bash
# Backup current database
pg_dump -U aiuser ai_workplace_copilot > backup_$(date +%Y%m%d).sql

# If using Alembic (recommended for production):
alembic upgrade head

# Or manually apply schema
python -c "
from app.core.database import init_db
import asyncio
asyncio.run(init_db())
"

# Verify
psql -U aiuser -d ai_workplace_copilot -c "\dt"
```

## Monitoring & Logging

### Application Metrics

```python
# In app/main.py, add:
from prometheus_client import Counter, Histogram, make_wsgi_app
from prometheus_fastapi_openmetrics import PrometheusMiddleware

app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", make_wsgi_app())
```

### Logging

```bash
# Configure log aggregation (ELK, Datadog, etc.)
# All logs go to backend/logs/app.log

# View logs
tail -f backend/logs/app.log

# Docker
docker logs ai-workplace-copilot-backend-1
```

### Health Checks

```bash
# Add to monitoring
curl https://your-domain.com/health

# AWS ECS target group health check
# Path: /health
# Port: 8000
# Healthy threshold: 2
# Unhealthy threshold: 3
# Timeout: 5 seconds
# Interval: 30 seconds
```

## Backup & Disaster Recovery

### Database Backups

```bash
# Daily backup script
#!/bin/bash
BACKUP_DIR="/backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -U aiuser ai_workplace_copilot | gzip > $BACKUP_DIR/backup_$TIMESTAMP.sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

### Document Storage Backups

```bash
# Backup uploads directory
aws s3 sync backend/uploads s3://ai-copilot-backups/uploads/

# Or use rsync for VPS
rsync -avz backend/uploads/ backup-server:/backups/documents/
```

### Recovery Procedure

```bash
# Restore database
gzip -d backup_20240115.sql.gz
psql -U aiuser ai_workplace_copilot < backup_20240115.sql

# Restore documents
aws s3 sync s3://ai-copilot-backups/uploads/ backend/uploads/
```

## Scaling Considerations

### Horizontal Scaling

```yaml
# Add multiple backend instances
docker-compose scale backend=3

# OR use Kubernetes
kubectl scale deployment ai-copilot-backend --replicas=3
```

### Caching Strategy

```python
# Implement aggressive caching
@app.get("/documents")
async def list_documents(...):
    cache_key = f"docs:{user_id}:{page}"
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Fetch from DB
    docs = ...
    await cache.set(cache_key, docs, expire=3600)  # 1 hour
    return docs
```

### Database Optimization

```sql
-- Add indexes
CREATE INDEX idx_documents_user_id ON documents(uploaded_by_id);
CREATE INDEX idx_chat_sessions_user_id ON chat_sessions(user_id);
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id);

-- Connection pooling
-- PgBouncer configuration for production
```

## Security Hardening

1. **SSL/TLS**

   ```bash
   certbot certonly --standalone -d your-domain.com
   ```

2. **Firewall Rules**

   ```bash
   ufw allow 22/tcp
   ufw allow 80/tcp
   ufw allow 443/tcp
   ufw allow 5432/tcp  # Only from private network
   ufw enable
   ```

3. **Secret Management**

   ```bash
   # Use AWS Secrets Manager
   aws secretsmanager create-secret --name ai-copilot/prod \
     --secret-string '{...}'

   # Or HashiCorp Vault
   ```

4. **API Rate Limiting**

   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address

   limiter = Limiter(key_func=get_remote_address)
   app.state.limiter = limiter

   @app.get("/api/endpoint")
   @limiter.limit("100/minute")
   async def endpoint(request: Request):
       pass
   ```

## Post-Deployment

1. **Test end-to-end workflow**
   - Register new user
   - Upload document
   - Ask questions
   - Check responses

2. **Monitor for 24 hours**
   - Check error logs
   - Monitor resource usage
   - Verify backups

3. **Setup alerts**

   ```bash
   # High CPU, memory, disk usage
   # Error rate > 5%
   # Database connection pool exhaustion
   # API response times > 5 seconds
   ```

4. **Document the setup**
   - Server credentials (secure location)
   - Deployment procedures
   - Rollback procedures
   - Escalation contacts

---

## Quick Deployment Summary

```bash
# Render (recommended for simplicity)
1. Push to GitHub
2. Connect Render.com
3. Configure environment
4. Auto-deploy on push

# Docker Compose
1. Server with Docker
2. Clone repo
3. Configure .env
4. docker-compose up -d

# Self-hosted
1. VPS setup
2. Install deps
3. Configure Nginx
4. Get SSL certificate
5. Start services
```

For specific issues or questions, check the main README.md and development guide.
