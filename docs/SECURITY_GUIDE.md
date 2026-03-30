# Security Guide

Production-grade security implementation and best practices.

## Overview

This guide covers security measures implemented in the system and additional recommendations for production deployment.

## Implemented Security Measures

### 1. Authentication

**Implemented:**

- JWT (JSON Web Tokens) with HS256 algorithm
- Bcrypt password hashing (cost factor: 12)
- Password requirements enforced at registration
- Token expiration (24 hours)
- Secure token storage (localStorage with HTTPOnly flag preference)

**Code Example:**

```python
# app/core/security.py
from passlib.context import CryptContext
from jose import jwt, JWTError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(SECRET_KEY, to_encode, algorithm="HS256")
    return encoded_jwt
```

**Recommendations for Production:**

- Use OAuth 2.0 / OIDC for enterprise SSO
- Implement refresh tokens
- Add multi-factor authentication (MFA)
- Use secure token storage (secure cookies with HTTPOnly flag)

### 2. Authorization & Access Control

**Implemented:**

- Role-Based Access Control (RBAC): Admin, Employee
- User-scoped data access
- Route-level permission checks
- Resource ownership validation

**Code Example:**

```python
# In routes
from app.core.security import get_current_user, get_current_admin_user

@router.get("/admin/users")
async def list_users(
    current_user: User = Depends(get_current_admin_user)
):
    # Only admin users can access
    return users

@router.get("/documents")
async def list_documents(current_user: User = Depends(get_current_user)):
    # Get only current user's documents
    return db.query(Document).filter(
        Document.uploaded_by_id == current_user.id
    ).all()
```

**Recommendations for Production:**

- Implement fine-grained permissions (edit, delete, share)
- Add role hierarchies
- Use policy-based access control (PBAC)
- Audit access logs

### 3. Input Validation

**Implemented:**

- Pydantic schema validation on all endpoints
- File type and size validation
- Email format validation
- SQL injection prevention (ORM parameterization)

**Code Example:**

```python
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr  # Validates email format
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., max_length=100)

# Pydantic auto-validates before route handler
@router.post("/auth/register")
async def register(user_data: UserCreate):
    # user_data is guaranteed valid
    pass
```

**Recommendations for Production:**

- Implement WAF (Web Application Firewall)
- Add rate limiting per user
- Validate file content (not just extension)
- Implement CSRF tokens for state-changing operations

### 4. Data Protection

**Implemented:**

- Password hashing (never stored in plain text)
- Sensitive data in environment variables
- HTTPS enforced (in production)
- Database connection encryption

**Environment Variables Example:**

```bash
# .env - NEVER commit to source control
SECRET_KEY=your-very-secret-key-min-32-chars
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:password@host/db
REDIS_URL=redis://password@host:port
```

**.gitignore:**

```
.env
.env.local
.env.*.local
```

**Recommendations for Production:**

- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Enable database encryption at rest
- Use TLS 1.3 for all connections
- Implement field-level encryption for sensitive data
- Use encrypted backups

### 5. HTTPS/TLS

**Implemented (in Docker/Production):**

- Nginx with SSL/TLS
- HTTP → HTTPS redirect
- Secure headers

**Nginx Configuration:**

```nginx
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/domain/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/domain/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
}
```

**Recommendations for Production:**

- Use Let's Encrypt certificates (free)
- Automatic renewal (certbot)
- Monitor certificate expiration
- Use strong cipher suites only
- Disable SSLv3, TLSv1.0, TLSv1.1 (use TLS 1.2+)

### 6. CORS (Cross-Origin Resource Sharing)

**Implemented:**

```python
# In app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Production Configuration:**

```python
allow_origins=[
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    # Don't use "*" in production
],
```

### 7. Dependency Injection Security

**Implemented:**

- `get_current_user()` - Verifies JWT token
- `get_current_admin_user()` - Checks admin role
- Used in FastAPI `Depends()` for automatic injection

**Code Example:**

```python
async def get_current_user(
    token: str = Depends(HTTPBearer())
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401)
    except JWTError:
        raise HTTPException(status_code=401)

    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=401)
    return user
```

## Security Best Practices

### 1. Secrets Management

**DO:**

```python
# Use environment variables
api_key = os.getenv("OPENAI_API_KEY")

# Use secrets manager
import boto3
sm = boto3.client('secretsmanager')
secret = sm.get_secret_value(SecretId='api-key')
```

**DON'T:**

```python
# Never hardcode secrets
API_KEY = "sk-abc123"

# Never log secrets
logger.info(f"Using key: {api_key}")

# Never put in source control
```

### 2. Error Handling

**DO:**

```python
@router.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    document = await DocumentService.get(doc_id)
    if not document:
        return JSONResponse(
            status_code=404,
            content={"detail": "Not found"}
        )
    return document
```

**DON'T:**

```python
# Never expose internal errors
@router.get("/documents/{doc_id}")
async def get_document(doc_id: int):
    try:
        # Complex query logic
    except Exception as e:
        return str(e)  # Exposes implementation!
```

### 3. Logging

**DO:**

```python
logger.info(f"User {user_id} logged in")  # OK
logger.warning(f"Document {doc_id} not found")  # OK
```

**DON'T:**

```python
logger.info(f"User {user_id} with password {password} logged in")  # NO!
logger.debug(f"Database query: {sql}")  # May expose data
```

### 4. File Upload Security

**Implemented:**

```python
# app/utils/file_handler.py
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

async def save_uploaded_file(file: UploadFile) -> str:
    # Check extension
    if not file.filename.endswith(tuple(ALLOWED_EXTENSIONS)):
        raise ValueError("Invalid file type")

    # Check size
    if file.size > MAX_FILE_SIZE:
        raise ValueError("File too large")

    # Random filename to prevent path traversal
    safe_filename = f"{uuid4()}_{file.filename}"

    # Save to safe location
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    contents = await file.read()
    with open(file_path, "wb") as f:
        f.write(contents)
```

**Recommendations for Production:**

- Store files outside web root
- Use CDN for file serving
- Implement virus scanning (ClamAV)
- Set file permissions restrictively

### 5. SQL Injection Prevention

**DO (ORM prevents injection):**

```python
# Using SQLAlchemy ORM - SAFE
user = await db.execute(
    select(User).where(User.username == username)
)
```

**DON'T (Raw SQL - vulnerable):**

```python
# DON'T do this!
user = await db.execute(
    f"SELECT * FROM users WHERE username = '{username}'"
)
```

### 6. XSS (Cross-Site Scripting) Prevention

**Frontend (React):**

```jsx
// Safe - React escapes by default
<div>{user.input}</div>

// HTML encoded automatically
<p>User: {data}</p>
```

**Backend:**

```python
# Pydantic validates input types
# Return JSON (not HTML)
# Frontend handles rendering
```

### 7. CSRF (Cross-Site Request Forgery) Prevention

**Implement if using HTML forms:**

```python
from fastapi_csrf_protect import CsrfProtect

@app.post("/action")
@CsrfProtect.csrf_token_set()
async def action(request: Request):
    # Verify CSRF token
    pass
```

## Security Checklist

### Development

- [ ] Use `.env` for secrets
- [ ] Never commit `.env` file
- [ ] Enable request logging (without secrets)
- [ ] Validate all inputs
- [ ] Use type hints
- [ ] Run linter (eslint, flake8)

### Testing

- [ ] Test authentication flows
- [ ] Test authorization checks
- [ ] Test input validation
- [ ] Fuzz test file uploads
- [ ] SQL injection tests
- [ ] XSS tests

### Deployment

- [ ] Generate strong SECRET_KEY (openssl rand -hex 32)
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS with valid certificate
- [ ] Set secure headers in Nginx
- [ ] Configure CORS properly
- [ ] Enable logging and monitoring
- [ ] Set up firewall rules
- [ ] Enable database backups
- [ ] Document incident response plan
- [ ] Regular security updates

### Operations

- [ ] Monitor logs for suspicious activity
- [ ] Regular security audits
- [ ] Keep dependencies updated
- [ ] Review access logs
- [ ] Test backup restoration
- [ ] Update security policies
- [ ] Training for team members

## Common Vulnerabilities & Fixes

### 1. Weak Passwords

**Problem:**

```python
if len(password) < 6:
    return error()  # Too weak!
```

**Solution:**

```python
import re

def validate_password(password: str):
    if len(password) < 8:
        raise ValueError("At least 8 characters")
    if not re.search(r'[A-Z]', password):
        raise ValueError("Need uppercase")
    if not re.search(r'[0-9]', password):
        raise ValueError("Need digit")
    if not re.search(r'[!@#$%^&*]', password):
        raise ValueError("Need special char")
```

### 2. Exposed API Keys

**Problem:**

```python
# In code
OPENAI_KEY = "sk-abc123"
```

**Solution:**

```python
# In .env
OPENAI_API_KEY=sk-abc123

# In code
import os
api_key = os.getenv("OPENAI_API_KEY")
```

### 3. Default Credentials

**Problem:**

```
Database: postgres / postgres
Admin: admin / admin
```

**Solution:**

- Force password change on first login
- Use strong default credentials
- Document credential rotation
- Audit access logs

### 4. Missing Rate Limiting

**Problem:** Brute force attacks possible

**Solution:**

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, credentials: LoginRequest):
    pass
```

## Monitoring & Alerting

### Suspicious Activity to Monitor

```bash
# Setup alerts for:
- Failed login attempts (> 5 per user/hour)
- Invalid tokens (many 401 responses)
- Admin account access outside business hours
- Large file uploads
- Database errors
- API errors (> 5% error rate)
- Unusual geographic access
- Rate limit triggers
```

## Incident Response

### If Breach Occurs

1. **Immediate:** Disable affected accounts
2. **Notification:** Inform affected users
3. **Investigation:** Review logs
4. **Mitigation:** Patch vulnerability
5. **Recovery:** Restore from backup if needed
6. **Documentation:** Post-mortem analysis

### Have Ready

- [ ] Incident response plan
- [ ] Contact list (security team, management, legal)
- [ ] Log retention policy (min 90 days)
- [ ] Backup restoration procedure
- [ ] Communication templates

## Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- FastAPI Security: https://fastapi.tiangolo.com/tutorial/security/
- JWT Best Practices: https://tools.ietf.org/html/rfc8725
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework

---

Security is an ongoing process. Regular audits and updates are essential.
