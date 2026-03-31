# Quick Start Guide

Get AI Workplace Copilot running in 5 minutes.

## Prerequisites

Choose your setup method based on your needs:

### Option 1: Docker (Recommended - 2 min)

**Requirements:**

- Docker & Docker Compose installed
- 4GB RAM, 25GB disk space

### Option 2: Local Development (5 min)

**Requirements:**

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (optional)
- Redis 7+ (optional)

### Option 3: Cloud (Render/Railway)

**Requirements:**

- GitHub account
- Credit card (usually free tier available)

---

## 🚀 Quick Start with Docker (Easiest)

### 1. Clone or Download

```bash
cd c:\AI-WORKSPACE COPILOT
```

### 2. Configure Environment

```bash
# Copy example environment file
copy backend\.env.example backend\.env

# Edit with your settings (notepad or VS Code)
notepad backend\.env
```

Minimum required:

```env
SECRET_KEY=your-secret-key-at-least-32-chars-long
DATABASE_URL=postgresql://aiuser:aipass@postgres:5432/ai_workplace_copilot
REDIS_URL=redis://redis:6379
ENVIRONMENT=development
DEBUG=True
```

### 3. Start Services

```bash
cd docker
docker-compose up -d

# Wait 30 seconds for services to start...

# Verify all services running
docker-compose ps
```

You should see:

```
NAME              STATUS
ai-postgres       Up (healthy)
ai-redis          Up (healthy)
ai-backend        Up (healthy)
ai-frontend       Up (healthy)
ai-nginx          Up
```

### 4. Access the Application

**Frontend:** http://localhost:3000
**API Docs:** http://localhost:8000/docs
**Health Check:** http://localhost:8000/health

### 5. Create First User

Register at http://localhost:3000/register:

- **Username:** testuser
- **Email:** test@example.com
- **Password:** SecurePassword123!

### 6. Try a Document Upload

1. Login with credentials above
2. Go to "Documents"
3. Upload a `.pdf`, `.docx`, or `.txt` file (max 50MB)
4. Wait for processing

### 7. Try Chat

1. Go to "Chat"
2. Create new session
3. Ask questions about your documents

---

## 🛠️ Local Development Setup

### Backend Setup

**Terminal 1: Backend**

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Mac/Linux: source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
copy .env.example .env

# Default local config uses SQLite.
# PostgreSQL/Redis are optional for local development.

# Initialize database
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# Run server
uvicorn app.main:app --reload
# Server runs on http://localhost:8000
```

### Frontend Setup

**Terminal 2: Frontend**

```bash
cd frontend

# Install dependencies
npm install

# Create config (optional)
echo VITE_API_URL=http://localhost:8000 > .env.local

# Start dev server
npm run dev
# App runs on http://localhost:3000
```

### Optional Database/Cache Setup

**Terminal 3: Services**

```bash
# Start PostgreSQL (Docker, optional)
docker run -d \
  --name ai-postgres \
  -e POSTGRES_PASSWORD=aipass \
  -e POSTGRES_DB=ai_workplace_copilot \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis (Docker, optional)
docker run -d \
  --name ai-redis \
  -p 6379:6379 \
  redis:7-alpine

# Verify
psql -h localhost -U postgres -d ai_workplace_copilot
redis-cli PING
```

---

## ☁️ Cloud Deployment (Render)

### Deploy Backend (2 min)

1. Push code to GitHub
2. Go to https://render.com
3. Click "New +"
4. Select "Web Service"
5. Connect GitHub repo
6. Configure:
   ```
   Name: ai-copilot-backend
   Environment: Python 3.11
   Build: pip install -r backend/requirements.txt
   Start: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
7. Add Environment Variables:
   ```
   DATABASE_URL=postgresql://...
   REDIS_URL=redis://...
   SECRET_KEY=<generated>
   OPENAI_API_KEY=sk-...
   ```

### Deploy Frontend (2 min)

1. Go to Render Dashboard
2. Click "New +"
3. Select "Static Site"
4. Connect GitHub repo
5. Configure:
   ```
   Build: cd frontend && npm ci && npm run build
   Publish: frontend/dist
   ```

---

## 🔐 First Login

1. **Register New Account**
   - Go to http://localhost:3000/register
   - Fill in details
   - Click "Register"

2. **Login**
   - Go to http://localhost:3000/login
   - Enter credentials
   - Click "Login"

3. **Update Profile** (Optional)
   - Click your email in top-right
   - Update profile information

---

## 📄 Upload Documents

1. Go to "Documents" tab
2. Click "Choose Files" or drag-drop
3. Supported formats:
   - PDF (.pdf)
   - Word (.docx)
   - Text (.txt)
4. Max file size: 50MB
5. Wait for "Processed ✓" status

---

## 💬 Start Chatting

1. Go to "Chat" tab
2. Click "New Session"
3. Enter session name (e.g., "Q&A")
4. Select documents (optional)
5. Type your question
6. Press Enter or click Send
7. Get AI response with sources

---

## 👨‍💼 Admin Features

If your account is admin role:

1. Go to "Admin" tab
2. View statistics:
   - Total documents
   - Total users
   - System health
3. Manage users:
   - Promote to admin
   - View activity
4. Clear cache

**Make admin:** Ask a current admin to promote you

---

## 🐛 Troubleshooting

### "Cannot connect to database"

```bash
# Default local setup uses backend/ai_workplace_copilot.db (SQLite).
# If you changed DATABASE_URL to PostgreSQL, check that PostgreSQL is running.

# Check PostgreSQL running
docker ps | grep postgres

# Test connection
psql -h localhost -U postgres -d ai_workplace_copilot
```

### "Cannot connect to Redis"

The app can still start without Redis in local development. Redis only enables cache/session storage.

```bash
# Check Redis running
docker ps | grep redis

# Test connection
redis-cli PING  # Should return PONG
```

### "Frontend not loading"

```bash
# Check frontend running
http://localhost:3000

# Check build
cd frontend
npm run build

# Check logs
npm run dev
```

### "API returning 401 errors"

- Token expired → Logout and login again
- Invalid token → Clear localStorage:
  ```javascript
  localStorage.clear();
  location.reload();
  ```

### "Document upload fails"

- File too large? (> 50MB, reduce file size)
- Invalid type? (Use PDF, DOCX, or TXT)
- Disk space? (Need 25GB available)

### "Chat not responding"

- API up? Check http://localhost:8000/docs
- Token valid? Try logging in again
- No documents? Upload one first
- OPENAI_API_KEY set? (Or use mocks)

---

## ✅ Full System Test

Test workflow:

```bash
# 1. Frontend loads
http://localhost:3000

# 2. Register/Login
Create account

# 3. Upload document
Documents tab → Choose file

# 4. View document
Click on uploaded document

# 5. Create chat session
Chat tab → New Session

# 6. Ask question
Type question in chat

# 7. Get response
AI generates answer with sources

# 8. Admin features
Go to Admin tab (if admin)
```

All working? ✅ System is ready to use!

---

## 📚 Next Steps

### Explore Features

- Upload multiple documents
- Create multiple chat sessions
- Try different question types
- Review response sources

### Customize

- Adjust chunk size: `CHUNK_SIZE` in .env
- Change model: `OPENAI_MODEL` in .env
- Configure embeddings: `EMBEDDING_MODEL` in .env

### Integrate

- Connect real Slack account
- Connect real Gmail account
- Add custom integrations
- Implement webhooks

### Deploy

- Deploy to AWS using guide
- Deploy to Railway
- Deploy to your own server

### Extend

- Add new features
- Modify UI
- Add new document types
- Implement new AI actions

---

## 🆘 Getting Help

- **Documentation:** See docs/ folder
- **API Docs:** http://localhost:8000/docs
- **Issues:** Check TROUBLESHOOTING in README
- **Code:** Review files in backend/ and frontend/

---

## 📊 What's Installed

### Backend

- FastAPI (Python web framework)
- SQLAlchemy (Database ORM)
- Redis (Cache/sessions)
- OpenAI API (LLM)
- FAISS (Vector search)
- Sentence Transformers (Embeddings)

### Frontend

- React 18 (UI framework)
- Vite (Build tool)
- Tailwind CSS (Styling)
- Axios (HTTP client)
- React Router (Navigation)

### Infrastructure

- PostgreSQL (Database)
- Redis (Cache)
- Nginx (Reverse proxy)
- Docker (Containerization)

---

Congratulations! You now have a production-ready AI SaaS application. 🎉

For detailed guides, see:

- [README.md](../README.md) - Full documentation
- [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development setup
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - API reference
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Production deployment
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [SECURITY_GUIDE.md](SECURITY_GUIDE.md) - Security best practices
