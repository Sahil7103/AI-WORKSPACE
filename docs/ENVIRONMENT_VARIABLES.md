# Environment Variables Reference

Complete reference for all configurable environment variables.

## Configuration Files

### Backend (.env)

Located in: `backend/.env`

Copy from: `backend/.env.example`

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

## Database Configuration

### PostgreSQL

```bash
# Database URL
DATABASE_URL=postgresql://username:password@localhost:5432/ai_workplace_copilot

# Format: postgresql://user:password@host:port/database
# Local development: postgresql://postgres:password@localhost/ai_workplace_copilot
# AWS RDS: postgresql://admin:password@db-instance.xxxxx.us-east-1.rds.amazonaws.com:5432/ai_workplace_copilot

# Optional: Connection pooling
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10
```

## Cache Configuration

### Redis

```bash
# Redis URL
REDIS_URL=redis://localhost:6379

# With password
REDIS_URL=redis://:password@localhost:6379

# Format: redis://[password@]host:port[/db]

# Optional
REDIS_DB=0
REDIS_SOCKET_TIMEOUT=5
```

## Security Configuration

### JWT & Passwords

```bash
# Secret key for JWT signing (generate with: openssl rand -hex 32)
SECRET_KEY=your-secret-key-min-32-chars-long-like-this-example

# Token expiration in hours (default: 24)
TOKEN_EXPIRE_HOURS=24

# CORS origins (comma-separated)
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# Environment
ENVIRONMENT=development  # or production
DEBUG=True  # Set to False in production
```

## LLM Configuration

### OpenAI

```bash
# API key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-your-api-key-here

# Model selection
OPENAI_MODEL=gpt-3.5-turbo  # or gpt-4, gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.7  # 0-2, higher = more creative
OPENAI_MAX_TOKENS=2000

# Rate limits
OPENAI_REQUEST_TIMEOUT=30
OPENAI_MAX_RETRIES=3
```

## Embeddings Configuration

### Local (Sentence Transformers)

```bash
# Model name from HuggingFace
EMBEDDING_MODEL=all-MiniLM-L6-v2  # ~90MB, fast
# or: all-mpnet-base-v2  # ~430MB, better quality
# or: all-distilroberta-v1  # balanced

# Embedding dimension (depends on model)
EMBEDDING_DIMENSION=384  # for all-MiniLM-L6-v2
# 768 for all-mpnet-base-v2
```

### Cloud (OpenAI)

```bash
# Use OpenAI embeddings
USE_OPENAI_EMBEDDINGS=True
OPENAI_EMBEDDING_MODEL=text-embedding-3-small  # or text-embedding-3-large
OPENAI_EMBEDDING_DIMENSION=1536  # for text-embedding-3-large
```

## Vector Store Configuration

### FAISS (Local)

```bash
# FAISS settings
VECTOR_STORE_TYPE=faiss  # or pinecone
FAISS_INDEX_PATH=./faiss_index  # Where to save the index
FAISS_SIMILARITY_THRESHOLD=0.7  # 0-1, higher = more strict matching
```

### Pinecone (Cloud)

```bash
# Pinecone settings
VECTOR_STORE_TYPE=pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-west1-gcp  # Your Pinecone environment
PINECONE_INDEX_NAME=ai-copilot
PINECONE_SIMILARITY_THRESHOLD=0.7
```

## Document Processing

### Chunking

```bash
# Document chunking settings
CHUNK_SIZE=500  # Characters per chunk
CHUNK_OVERLAP=50  # Overlap between chunks
CHUNKING_STRATEGY=overlap  # or sentence, paragraph

# File processing
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=pdf,docx,txt

# Supported: pdf, docx, txt
# (Add more by extending DocumentService)
```

## Logging Configuration

### Application Logging

```bash
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL=INFO  # DEBUG in development

# Log directory
LOG_DIR=./logs

# File logging
LOG_FILE_NAME=app.log
LOG_MAX_SIZE_MB=100  # Rotate files at this size
LOG_BACKUP_COUNT=10  # Keep 10 rotated files
```

## Server Configuration

### FastAPI/Uvicorn

```bash
# Server settings
API_HOST=0.0.0.0  # Listen on all interfaces
API_PORT=8000
API_WORKERS=4  # Number of worker processes

# Request handling
REQUEST_TIMEOUT=30  # seconds
MAX_UPLOAD_SIZE=52428800  # 50MB in bytes

# CORS & Security
ALLOWED_HOSTS=localhost,127.0.0.1
TRUST_PROXY=False  # Set True if behind reverse proxy
```

## Frontend Configuration

### Vite/React

Located in: `frontend/.env.local`

```bash
# API configuration
VITE_API_URL=http://localhost:8000
# or in production: VITE_API_URL=https://api.yourdomain.com

# Feature flags
VITE_ENABLE_STREAMING=true  # Enable SSE streaming responses
VITE_ENABLE_AGENTS=true     # Enable AI agents feature

# Debug
VITE_DEBUG=false  # Verbose console logging
```

## Docker Configuration

### Environment Override

Pass via `docker-compose.yml`:

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=postgresql://...
      - OPENAI_API_KEY=sk-...
      - SECRET_KEY=your-key
```

Or in `.env` file in docker directory:

```bash
# docker/.env
DATABASE_URL=postgresql://...
OPENAI_API_KEY=sk-...
```

## Special Configuration Profiles

### Development Profile

```bash
ENVIRONMENT=development
DEBUG=True
LOG_LEVEL=DEBUG
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
TOKEN_EXPIRE_HOURS=24
OPENAI_API_KEY=  # Leave empty to use mocks
```

### Production Profile

```bash
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING
CORS_ORIGINS=https://yourdomain.com
TOKEN_EXPIRE_HOURS=12
OPENAI_API_KEY=sk-...  # Required for real responses
FAISS_SIMILARITY_THRESHOLD=0.8  # More strict
```

### Testing Profile

```bash
ENVIRONMENT=testing
DEBUG=True
DATABASE_URL=sqlite:///./test.db  # In-memory
REDIS_URL=dummy://  # Mock Redis
OPENAI_API_KEY=test-key
```

## Configuration Validation

### Check Configuration

```python
# Python script to validate
from app.core.config import settings

# Print all settings
for key, value in settings.dict().items():
    if 'key' not in key.lower() and 'password' not in key.lower():
        print(f"{key}: {value}")
```

### Environment Variable Rules

1. **Priority Order:**
   - Environment variables (highest)
   - .env file
   - Default values (lowest)

2. **Type Conversion:**
   - `True/False` → Boolean
   - `123` → Integer
   - `123.45` → Float
   - Strings as-is

3. **Case Sensitivity:**
   - Environment variables: UPPERCASE
   - Python attributes: lowercase with underscores

## Common Configuration Scenarios

### Local Development

```bash
# .env for local dev
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_workplace_copilot
REDIS_URL=redis://localhost:6379
SECRET_KEY=dev-secret-key-change-in-production
ENVIRONMENT=development
DEBUG=True
CORS_ORIGINS=http://localhost:3000
OPENAI_API_KEY=  # Leave empty for mocks
VECTOR_STORE_TYPE=faiss
```

### Docker Local

```bash
# All services configured in docker-compose.yml
DATABASE_URL=postgresql://student:graduation@postgres:5432/ai_workplace_copilot
REDIS_URL=redis://redis:6379
# ... other settings
```

### AWS Deployment

```bash
# RDS PostgreSQL
DATABASE_URL=postgresql://admin:SecurePassword123@ai-copilot-db.xxxxx.us-east-1.rds.amazonaws.com:5432/ai_copilot

# ElastiCache Redis
REDIS_URL=redis://ai-copilot-cache.xxxxx.ng.0001.use1.cache.amazonaws.com:6379

# Secrets Manager
OPENAI_API_KEY=  # Store in Secrets Manager, fetch at runtime

# S3 for files
FILE_STORAGE_TYPE=s3
AWS_S3_BUCKET=ai-copilot-uploads
AWS_REGION=us-east-1
```

### Render Deployment

```bash
# Use native Render databases
DATABASE_URL=postgresql://user:password@dpg-xxxxx.render.com:5432/db_name
REDIS_URL=redis://default:xxxxx@redis-xxxxx.render.com:6379

# Other settings same as production
ENVIRONMENT=production
DEBUG=False
```

## Troubleshooting Configuration

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql $DATABASE_URL

# Common issues:
# - DATABASE_URL format incorrect
# - Database service not running
# - Credentials wrong
# - Network/firewall blocking
```

### Redis Connection Issues

```bash
# Test Redis connection
redis-cli -u $REDIS_URL PING  # Should return PONG

# Common issues:
# - REDIS_URL format incorrect
# - Redis service not running
# - Port not exposed (Docker)
```

### OpenAI API Issues

```bash
# Test OpenAI API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Common issues:
# - Invalid API key
# - API key lacks permissions
# - Rate limits exceeded
# - Account has no credits
```

## Secrets Rotation

Rotate secrets regularly:

```bash
# Generate new SECRET_KEY
openssl rand -hex 32

# Update in .env
SECRET_KEY=new-secret-key

# Restart application
docker-compose restart backend

# Old tokens will no longer work (expiration enforced)
```

## Configuration Documentation

Update documentation when adding new variables:

1. Add to `.env.example`
2. Add to this reference
3. Document in DEVELOPMENT_GUIDE.md
4. Add validation in config.py
5. Use type hints for clarity

---

For production deployments, use secure secret management tools:

- AWS Secrets Manager
- HashiCorp Vault
- Azure Key Vault
- 1Password
