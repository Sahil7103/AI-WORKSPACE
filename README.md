# 🤖 AI Workplace Copilot

A production-grade **GenAI SaaS application** that acts as an internal ChatGPT for organizations. It integrates multiple data sources (documents, Slack, email) and enables intelligent querying using advanced Retrieval-Augmented Generation (RAG).

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [API Documentation](#-api-documentation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Deployment](#-deployment)
- [Testing](#-testing)

---

## ✨ Features

### Multi-Source Data Ingestion

- 📄 Upload PDFs, DOCX, TXT files
- 🔗 Integrate Slack API (with mock support)
- 📧 Integrate Gmail API (with mock support)
- 🗄️ Automatic metadata storage in PostgreSQL
- 🔄 Document processing and chunking strategies

### Advanced RAG Pipeline

- 📐 Intelligent document chunking (overlapping chunks)
- 🔍 Semantic search using vector similarity
- 💾 FAISS or Pinecone vector database support
- 🛡️ Source citation with confidence scores
- ⚡ Context retrieval optimization

### Smart Query Processing

- 🎯 Query intent detection
- 🔀 Dynamic source routing
- 🧠 LLM-powered responses with context grounding
- 🚫 Hallucination prevention through source verification

### Conversational Intelligence

- 💬 Multi-turn conversation support
- 🔄 Redis-based session memory
- 📝 Full chat history with sources
- ⏱️ Response time tracking

### Security & Access Control

- 🔐 JWT authentication with bcrypt hashing
- 👥 Role-based access control (Admin/Employee)
- 📊 document-level access restrictions
- 🔒 Secure API endpoints

### AI Actions (Tool Use)

- 📋 Document summarization
- 📈 Report generation
- 📧 Email notifications (mock)
- 🔍 Document search and aggregation

### Real-Time Features

- 🌊 Server-Sent Events (SSE) for response streaming
- 📡 WebSocket support for live updates
- ⚡ Sub-second response times

### Administration Dashboard

- 👥 User management and role assignment
- 📊 System statistics and monitoring
- 🧹 Cache management
- 📈 Evaluation metrics tracking

---

## 🏗️ Architecture

### Clean Architecture Layers

```
┌─────────────────────────────────────┐
│     Frontend (React + Vite)         │
├─────────────────────────────────────┤
│     API Gateway (FastAPI Routes)    │
├─────────────────────────────────────┤
│   Services (Business Logic)         │
│   - UserService                     │
│   - DocumentService                 │
│   - ChatService                     │
│   - LLMService / QueryService       │
│   - AIAgent                         │
├─────────────────────────────────────┤
│   RAG Pipeline                      │
│   - Chunking Strategy               │
│   - Embeddings (HuggingFace/OpenAI) │
│   - Vector Store (FAISS/Pinecone)   │
│   - Retriever                       │
├─────────────────────────────────────┤
│   Data Access Layer                 │
│   - SQLAlchemy ORM                  │
│   - Database Models                 │
├─────────────────────────────────────┤
│   Infrastructure                    │
│   - PostgreSQL (Relational DB)      │
│   - Redis (Cache/Sessions)          │
│   - Vector DB (FAISS/Pinecone)      │
│   - File Storage                    │
└─────────────────────────────────────┘
```

### RAG Pipeline Flow

```

User Query
    ↓
[Query Embedding] ← Embedding Model
    ↓
[Vector Search] in Vector DB
    ↓
[Retrieved Chunks] with Sources
    ↓
[Context Formatting]
    ↓
[LLM Query] with System Prompt
    ↓
[Response Generation]
    ↓
[Source Attribution]
    ↓
User Response + Citations
```

---

## 🛠️ Tech Stack

### Backend

- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL (relational) + SQLAlchemy ORM
- **Cache**: Redis (sessions, conversational memory)
- **Vector DB**: FAISS or Pinecone (semantic search)
- **Embeddings**: Sentence Transformers (local) or OpenAI API
- **Auth**: JWT + bcrypt
- **Async**: AsyncIO, Uvicorn

### Frontend

- **Framework**: React 18 with Hooks
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **Notifications**: React Hot Toast

### DevOps

- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Web Server**: Nginx (reverse proxy)
- **Deployment Ready**: AWS, Render, Railway

---

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.11+, Node.js 18+
- PostgreSQL 15+
- Redis 7+

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-workplace-copilot.git
cd ai-workplace-copilot

# Create .env file
cp backend/.env.example backend/.env

# Update .env with your API keys
# - OPENAI_API_KEY (optional, for real LLM responses)
# - Database credentials
# - Redis settings

# Start all services
cd docker
bash start.sh

# Or manually:
docker-compose up -d
```

Services will be available at:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Nginx**: http://localhost:80

### Option 2: Local Development

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Update .env with your settings

# Initialize database
python -c "from app.core.database import init_db; import asyncio; asyncio.run(init_db())"

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# App will be available at http://localhost:3000
```

---

## 📁 Project Structure

```
ai-workplace-copilot/
├── backend/
│   ├── app/
│   │   ├── api/                    # API Routes
│   │   │   ├── auth.py            # Auth endpoints
│   │   │   ├── documents.py       # Document management
│   │   │   ├── chat.py            # Chat/query endpoints
│   │   │   ├── admin.py           # Admin endpoints
│   │   │   └── agents.py          # Agent action endpoints
│   │   ├── core/
│   │   │   ├── config.py          # Settings management
│   │   │   ├── security.py        # JWT, password hashing
│   │   │   └── database.py        # DB connection & setup
│   │   ├── models/
│   │   │   └── __init__.py        # SQLAlchemy ORM models
│   │   ├── schemas/
│   │   │   └── __init__.py        # Pydantic request/response schemas
│   │   ├── services/              # Business logic
│   │   │   ├── user_service.py
│   │   │   ├── document_service.py
│   │   │   ├── chat_service.py
│   │   │   ├── llm_service.py     # LLM & query processing
│   │   ├── rag/                    # RAG Pipeline
│   │   │   ├── chunking.py        # Document chunking strategies
│   │   │   ├── embeddings.py      # Embedding models
│   │   │   ├── vector_store.py    # FAISS/Pinecone wrapper
│   │   │   └── retriever.py       # RAG orchestrator
│   │   ├── agents/
│   │   │   └── __init__.py        # AI agent for actions
│   │   ├── utils/
│   │   │   ├── cache.py           # Redis cache utilities
│   │   │   ├── logger.py          # Logging configuration
│   │   │   └── file_handler.py    # File operations
│   │   └── main.py                # FastAPI app entry point
│   ├── tests/
│   │   ├── test_api.py            # API endpoint tests
│   │   └── test_rag.py            # RAG pipeline tests
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example               # Environment template
│   └── uploads/                   # Document storage

├── frontend/
│   ├── src/
│   │   ├── components/            # Reusable React components
│   │   │   ├── Header.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── ChatMessage.jsx
│   │   │   ├── DocumentCard.jsx
│   │   │   └── ProtectedRoute.jsx
│   │   ├── pages/                 # Page components
│   │   │   ├── LoginPage.jsx
│   │   │   ├── RegisterPage.jsx
│   │   │   ├── DashboardPage.jsx
│   │   │   ├── ChatPage.jsx
│   │   │   ├── DocumentsPage.jsx
│   │   │   ├── AdminPage.jsx
│   │   │   └── NotFoundPage.jsx
│   │   ├── services/
│   │   │   └── api.js            # API client with axios
│   │   ├── utils/
│   │   │   └── helpers.js        # Utility functions
│   │   ├── styles/
│   │   │   └── index.css         # Global styles
│   │   ├── App.jsx               # Main app component
│   │   └── main.jsx              # React entry point
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js            # Vite configuration
│   ├── tailwind.config.js        # Tailwind CSS configuration
│   └── postcss.config.js         # PostCSS configuration

├── docker/
│   ├── Dockerfile.backend        # Backend Docker image
│   ├── Dockerfile.frontend       # Frontend Docker image
│   ├── docker-compose.yml        # Compose orchestration
│   ├── nginx.conf                # Nginx configuration
│   └── start.sh                  # Startup script

├── docs/
│   ├── API_DOCUMENTATION.md
│   ├── DEPLOYMENT_GUIDE.md
│   ├── DEVELOPMENT_GUIDE.md
│   └── ARCHITECTURE.md

└── README.md (this file)
```

---

## 📚 API Documentation

### Authentication

#### Register

```bash
POST /auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe"
}
```

#### Login

```bash
POST /auth/login
Content-Type: application/json

{
  "username": "newuser",
  "password": "secure_password"
}

Response:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user": { ... }
}
```

### Documents

#### Upload Document

```bash
POST /documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

[file content]
```

#### List Documents

```bash
GET /documents?skip=0&limit=20
Authorization: Bearer <token>

Response:
{
  "total": 5,
  "documents": [ ... ]
}
```

#### Delete Document

```bash
DELETE /documents/{doc_id}
Authorization: Bearer <token>
```

### Chat

#### Create Session

```bash
POST /chat/sessions
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_name": "Q&A Session"
}
```

#### Send Query

```bash
POST /chat/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": 1,
  "query": "What is the company's policy on remote work?",
  "document_ids": [1, 2, 3]  // optional
}

Response:
{
  "message_id": 42,
  "session_id": 1,
  "query": "What is...",
  "response": "Based on the retrieved documents...",
  "sources": [
    {
      "doc_id": 1,
      "filename": "policies.pdf",
      "similarity": 0.95
    }
  ],
  "response_time_ms": 245
}
```

#### Stream Query Response

```bash
POST /chat/query-stream
Authorization: Bearer <token>

Streams Server-Sent Events (SSE) with response tokens
```

### Admin

#### List Users

```bash
GET /admin/users?skip=0&limit=50
Authorization: Bearer <admin_token>
```

#### Update User Role

```bash
PUT /admin/users/{user_id}/role
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "admin"  // or "employee"
}
```

#### Get System Statistics

```bash
GET /admin/stats
Authorization: Bearer <admin_token>

Response:
{
  "total_documents": 42,
  "total_processed": 40,
  "total_with_embeddings": 40,
  "total_chunks": 1205
}
```

### Agents

#### List Available Actions

```bash
GET /agents/actions
Authorization: Bearer <token>

Response:
{
  "actions": [
    {
      "name": "summarize_document",
      "description": "Generate a summary...",
      "parameters": { "doc_id": "int" }
    },
    ...
  ]
}
```

#### Execute Agent Action

```bash
POST /agents/actions/summarize_document
Authorization: Bearer <token>
Content-Type: application/json

{
  "doc_id": 1
}
```

**Full API documentation available at**: `http://localhost:8000/docs`

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_workplace_copilot
SQLALCHEMY_DB_URL=postgresql://user:password@localhost:5432/ai_workplace_copilot

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-never-use-default
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False

# OpenAI (for real LLM responses)
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small

# Vector Database
USE_FAISS=True  # or False for Pinecone
PINECONE_API_KEY=your-key
PINECONE_INDEX_NAME=ai-copilot

# App Settings
APP_NAME=AI Workplace Copilot
ENVIRONMENT=development
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Document Processing
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_FILE_SIZE_MB=50
```

### Supported Embedding Models

**Local (Recommended for development):**

- `all-MiniLM-L6-v2` (default, 384-dim)
- `all-mpnet-base-v2` (768-dim)
- `sentence-transformers/paraphrase-MiniLM-L6-v2`

**OpenAI API:**

- `text-embedding-3-small`
- `text-embedding-3-large`
- `text-embedding-ada-002`

### Database Schema

The system automatically creates these tables:

- `users` - User accounts and roles
- `documents` - Document metadata
- `document_chunks` - Chunked document content with embeddings
- `chat_sessions` - Conversation sessions
- `chat_messages` - Individual messages with sources
- `api_logs` - Request logs for monitoring
- `evaluation_metrics` - Response quality metrics
- `document_user_access` - Document access control (junction table)

---

## 🛠️ Development

### Running Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=app tests/

# Run RAG pipeline tests
pytest tests/test_rag.py -v
```

### Development Workflow

#### Backend

```bash
cd backend

# Activate virtual environment
source venv/bin/activate

# Install dev dependencies
pip install -r requirements.txt pytest pytest-asyncio

# Start with auto-reload
uvicorn app.main:app --reload

# Or with explicit configuration
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Start dev server with HMR
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Code Quality

- **Linting**: ESLint configured for React
- **Type Safety**: Pydantic for backend, optional TypeScript for frontend
- **Testing**: pytest for backend, Jest for frontend
- **Logging**: Structured logging with timestamps and levels

### Adding New Features

#### New API Endpoint

1. Create route in `app/api/your_module.py`
2. Add schemas in `app/schemas/__init__.py`
3. Implement business logic in `app/services/`
4. Test with `pytest` or API docs
5. Update frontend component

#### New Model

1. Define in `app/models/__init__.py`
2. Run alembic migration (or recreate DB)
3. Update schemas for validation
4. Create service layer

#### New RAG Feature

1. Enhance `app/rag/retriever.py`
2. Add new chunking strategy in `app/rag/chunking.py`
3. Test with `pytest tests/test_rag.py`
4. Integrate through `QueryService`

---

## 🚀 Deployment

### Docker Deployment

```bash
# Build images
docker build -f docker/Dockerfile.backend -t ai-copilot-backend .
docker build -f docker/Dockerfile.frontend -t ai-copilot-frontend .

# Run with compose
docker-compose -f docker/docker-compose.yml up -d
```

### AWS Deployment

```bash
# Setup RDS PostgreSQL
# Setup ElastiCache Redis
# Setup S3 for document storage

# Update docker-compose with AWS endpoints
# Push images to ECR
# Deploy with ECS/Fargate
```

### Render Deployment

```bash
# Backend service:
# - Runtime: Python 3.11
# - Build command: pip install -r requirements.txt
# - Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT

# Frontend service:
# - Runtime: Node 18
# - Build command: npm ci && npm run build
# - Start command: npm run preview
```

### Railway Deployment

```bash
# Connect Git repository
# Configure environment variables
# Auto-deploy on push
```

### Production Checklist

- [ ] Set strong `SECRET_KEY`
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS correctly
- [ ] Use real OpenAI API key
- [ ] Set `DEBUG=False`
- [ ] Configure PostgreSQL backups
- [ ] Set up Redis persistence
- [ ] Configure log aggregation
- [ ] Set up monitoring/alerts
- [ ] Enable rate limiting in Nginx
- [ ] Configure CDN for static assets
- [ ] Test disaster recovery

---

## 🧪 Testing

### Backend Tests

```bash
cd backend

# Test user authentication
pytest tests/test_api.py::test_user_creation -v

# Test document processing
pytest tests/test_rag.py::test_faiss_vector_store -v

# Test RAG pipeline
pytest tests/test_rag.py -v

# All tests with coverage
pytest --cov=app tests/
```

### Example Test Cases

```python
# Test password hashing
def test_password_hashing():
    password = "test123"
    hashed = hash_password(password)
    assert verify_password(password, hashed)

# Test user authentication
async def test_user_authentication():
    user = await authenticate_user(db, "username", "password")
    assert user is not None

# Test document chunking
def test_document_chunking():
    chunker = DocumentChunker(chunk_size=100)
    chunks = chunker.chunk_text("Large text...")
    assert len(chunks) > 0
```

---

## 📊 Evaluation Metrics

The system tracks:

- **Response Time**: Time from query to complete response
- **Retrieval Accuracy**: Similarity scores of retrieved documents
- **Hallucination Detection**: Whether response contains unsupported claims
- **User Satisfaction**: Optional user feedback scores
- **Query Success Rate**: Percentage of queries answered

Access metrics via admin API:

```bash
GET /admin/stats
```

---

## 🔐 Security Best Practices

### Implemented

- JWT token authentication with expiration
- bcrypt password hashing (10+ rounds)
- Role-based access control (RBAC)
- Input validation with Pydantic
- SQL injection prevention (SQLAlchemy ORM)
- CORS configuration
- Secure headers (via Nginx)
- Rate limiting (per endpoint basic implementation)
- Logging of security events

### Recommended for Production

- [ ] Enable HTTPS/TLS certificates
- [ ] Add rate limiting per user/IP
- [ ] Implement request signing for APIs
- [ ] Add WAF (Web Application Firewall)
- [ ] Enable encryption at rest for database
- [ ] Implement audit logging for all actions
- [ ] Add two-factor authentication
- [ ] Regular security audits & penetration testing
- [ ] Dependency scanning (e.g., Dependabot)
- [ ] API key rotation policies

---

## 🐛 Troubleshooting

### Common Issues

**"Connection refused" to PostgreSQL**

- Ensure PostgreSQL is running: `docker ps`
- Check `DATABASE_URL` in `.env`
- Verify credentials

**"No module named openai"**

- Install missing: `pip install openai`
- Or use mock responses (default)

**Frontend can't connect to API**

- Confirm backend is running on port 8000
- Check `CORS_ORIGINS` includes frontend URL
- Verify `VITE_API_URL` in frontend

**FAISS import error**

- For Windows: Use `faiss-cpu` (already in requirements)
- For Mac M1: `conda install -c conda-forge faiss`

**Redis connection timeout**

- Ensure Redis is running: `redis-cli ping`
- Check `REDIS_URL` format

### Logs

Backend logs:

```bash
tail -f backend/logs/app.log
docker logs ai-workplace-copilot-backend-1
```

Frontend errors:

```bash
# Browser console: F12 or Cmd+Option+I
# Network tab to debug API calls
```

---

## 📖 Documentation

- [API Documentation](docs/API_DOCUMENTATION.md)
- [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)
- [Development Guide](docs/DEVELOPMENT_GUIDE.md)
- [Architecture Details](docs/ARCHITECTURE.md)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 🙏 Acknowledgments

- OpenAI for GPT models
- Sentence Transformers for embeddings
- FAISS for vector search
- FastAPI for the web framework
- React community for frontend tools

---

## 📞 Support

For issues and questions:

- Open an issue on GitHub
- Check existing documentation
- Review example code in `/backend/tests`

---

**Happy coding! 🚀**
