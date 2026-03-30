# Architecture Overview

Deep dive into the system architecture of AI Workplace Copilot.

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────┐
│                   Client Layer                      │
│  ┌──────────────┐      ┌──────────────────────┐   │
│  │   Browser    │      │   Mobile/Desktop     │   │
│  │   (React)    │      │   App (future)       │   │
│  └──────────────┘      └──────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         │ HTTPS
┌─────────────────────────────────────────────────────┐
│              API Gateway / Load Balancer            │
│              (Nginx / AWS ALB)                      │
└─────────────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼────────┐  ┌────▼──────┐  ┌────▼──────┐
│   FastAPI      │  │  FastAPI  │  │  FastAPI  │
│   Backend 1    │  │ Backend 2 │  │ Backend 3 │
└────────┬───────┘  └────┬──────┘  └────┬──────┘
         │               │               │
         └───────────────┼───────────────┘
                         │
        ┌────────────────┼────────────────────┐
        │                │                    │
┌───────▼────────┐ ┌────▼──────────┐ ┌──────▼────┐
│   PostgreSQL   │ │    Redis      │ │   FAISS/  │
│   Database     │ │    Cache      │ │  Pinecone │
│                │ │               │ │  Vector   │
│ Tables:        │ │ Sessions:     │ │  Store    │
│ - users        │ │ - chat memory │ │           │
│ - documents    │ │ - query cache │ │ Vectors:  │
│ - chat msgs    │ │ - task queue  │ │ - doc     │
│ - embeddings   │ │               │ │   chunks  │
└────────────────┘ └───────────────┘ └───────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                    ┌────▼──────┐
                    │  S3/GCS   │
                    │  Storage  │
                    │           │
                    │ Files:    │
                    │ - uploads │
                    │ - logs    │
                    └───────────┘
```

## Layered Architecture

### 1. Presentation Layer (Frontend)

**Technology:** React 18, Vite, Tailwind CSS

**Components:**

- **Pages**: Login, Dashboard, Chat, Documents, Admin
- **Components**: Reusable UI (Header, Sidebar, ChatMessage, etc.)
- **Services**: API client (Axios)
- **Utils**: Helpers, constants

**Key Features:**

- SPA (Single Page Application)
- Real-time updates with SSE
- Responsive design
- Authentication guard

**Data Flow:**

```
User Interaction
    ↓
React Component
    ↓
API Service (Axios)
    ↓
Backend Endpoint
    ↓
Response → Update State
    ↓
Re-render Component
```

### 2. API Layer (FastAPI)

**Technology:** FastAPI, Uvicorn, Pydantic

**Routes:**

- `/auth` - Authentication (login, register)
- `/documents` - Document management
- `/chat` - Chat sessions and queries
- `/admin` - Admin functions
- `/agents` - AI actions

**Features:**

- Async request handling
- Request validation (Pydantic)
- Response serialization
- Error handling middleware
- CORS middleware
- Auto-documentation (Swagger)

**Request Validation Example:**

```python
class QueryRequest(BaseModel):
    session_id: int
    query: str
    document_ids: Optional[List[int]] = None

@router.post("/query")
async def query_chat(request: QueryRequest, ...):
    # Pydantic auto-validates request
    # QueryRequest fields are available
```

### 3. Service Layer (Business Logic)

**Services:**

1. **UserService** - User CRUD, authentication
2. **DocumentService** - Document management, chunking
3. **ChatService** - Session and message handling
4. **LLMService** - Language model interactions
5. **QueryService** - Query orchestration
6. **AIAgent** - Tool execution

**Separation of Concerns:**

```
Route Handler
    ↓
Service Layer
    ├── Validation
    ├── Business Logic
    ├── Error Handling
    └── Logging
    ↓
Data Access Layer
    ↓
Database
```

**Example Service:**

```python
class DocumentService:
    @staticmethod
    async def create_document(
        db: AsyncSession,
        filename: str,
        content: str,
        user_id: int
    ) -> Document:
        # Business logic here
        doc = Document(...)
        db.add(doc)
        await db.commit()
        return doc
```

### 4. RAG Pipeline Layer

**Components:**

```
Raw Document
    ↓
[Document Chunker]
├── Strategy: Overlapping chunks
├── Size: 500 characters
└── Overlap: 50 characters
    ↓
Document Chunks
    ↓
[Embedding Model]
├── Local: Sentence Transformers
└── Cloud: OpenAI API
    ↓
Vector Embeddings (384/1536-dim)
    ↓
[Vector Store]
├── FAISS (local)
└── Pinecone (cloud)
    ↓
Vector Index Store
```

**RAG Query Flow:**

```
User Query
    ↓
[1. Encode Query]
   └→ Generate embedding
    ↓
[2. Search Vector Store]
   └→ Find K nearest chunks
    ↓
[3. Filter & Rank]
   └→ Apply similarity threshold
    ↓
[4. Format Context]
   └→ Build system prompt
    ↓
[5. Call LLM]
   └→ Generate response
    ↓
[6. Extract Sources]
   └→ Cite referenced documents
    ↓
Response with Citations
```

### 5. Data Access Layer (ORM)

**Technology:** SQLAlchemy, Async support

**Models:**

- User, Document, DocumentChunk
- ChatSession, ChatMessage
- ApiLog, EvaluationMetric

**Features:**

- Relationship definitions
- Cascade deletes
- Automatic timestamps
- Type hints

**Example Model:**

```python
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255))
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    chunks = relationship("DocumentChunk", cascade="all, delete-orphan")
    uploaded_by = relationship("User")
```

### 6. Infrastructure Layer

**Database (PostgreSQL):**

- Schema: Users, Documents, Chat, Logs
- Connections: Connection pooling
- Transactions: ACID compliance

**Cache (Redis):**

- Session memory: Conversation history
- Query cache: Recent results
- Rate limiting: Token bucket

**Vector Store (FAISS/Pinecone):**

- Approximate nearest neighbor search
- Fast similarity matching
- Scalable storage

**File Storage (Local/S3):**

- Document uploads
- Temporary files
- Application logs

## Data Models

### ER Diagram (Simplified)

```
┌─────────────┐
│    User     │
├─────────────┤
│ id (PK)     │
│ username    │
│ email       │
│ role        │◀─────┐
│ is_active   │      │
└─────────────┘      │
      │              │
      │ uploads      │ views/edits
      │              │
      ▼              │
┌──────────────────────────┐
│      Document            │
├──────────────────────────┤
│ id (PK)                  │
│ filename                 │
│ uploaded_by_id (FK)      │──────→ User
│ is_processed             │
│ embedding_generated      │
└──────────────────────────┘
      │                    │
      │ contains           │ creates
      │                    │
      ▼                    ▼
┌──────────────┐    ┌────────────────────┐
│Document      │    │   ChatSession      │
│Chunk         │    ├────────────────────┤
├──────────────┤    │ id (PK)            │
│ id (PK)      │    │ user_id (FK)       │
│ doc_id (FK)  │    │ session_name       │
│ text         │    │ created_at         │
│ embedding    │    │ updated_at         │
│ chunk_index  │    └────────────────────┘
└──────────────┘           │
                           │ contains
                           │
                           ▼
                    ┌────────────────────┐
                    │   ChatMessage      │
                    ├────────────────────┤
                    │ id (PK)            │
                    │ session_id (FK)    │
                    │ role               │
                    │ content            │
                    │ sources            │
                    │ created_at         │
                    └────────────────────┘
```

## Request/Response Cycle

### Document Upload Flow

```
1. Browser
   ↓ File selected
   POST /documents/upload
   (multipart/form-data)

2. API Handler (documents.py)
   ├── Validate file size, type
   ├── Save to disk
   └── Create Document record

3. DocumentService.create_document()
   ├── Insert into DB
   └── Return Document object

4. Background Task (or sync)
   ├── Read file content
   ├── Chunk document
   ├── Generate embeddings
   ├── Store in vector DB
   └── Update Document status

5. Response
   ├── Status: 200 OK
   └── Body: DocumentResponse (JSON)

6. Frontend
   ├── Receive response
   ├── Update UI
   └── Show success toast
```

### Query Flow

```
1. User enters query in chat
   ↓
2. POST /chat/query
   {
     "session_id": 1,
     "query": "What is...",
     "document_ids": [1, 2, 3]
   }

3. ChatPage (REACT Handler)
   ├── Validate session access
   ├── Fetch conversation history
   └── Call QueryService

4. QueryService
   ├── Get RAG Retriever
   ├── Retrieve relevant chunks
   │  ├── Encode query
   │  ├── Search vector store
   │  └── Filter by similarity
   └── Call LLMService

5. LLMService
   ├── Format context
   ├── Build system prompt
   ├── Call OpenAI API (or mock)
   └── Return response with time

6. ChatService
   ├── Save user message
   ├── Save assistant message
   └── Update session timestamp

7. Response
   {
     "message_id": 42,
     "response": "Based on...",
     "sources": [...],
     "response_time_ms": 245
   }

8. Frontend
   ├── Display response
   ├── Show sources
   └── Add to chat history
```

## Performance Considerations

### Query Optimization

```python
# Problem: N+1 queries
documents = await db.execute(select(Document))
for doc in documents:
    chunks = await db.get_document_chunks(doc.id)  # Query per doc!

# Solution: Eager loading
documents = await db.execute(
    select(Document).options(selectinload(Document.chunks))
)
```

### Caching Strategy

```python
# Cache hierarchy
1. Redis cache (hot data)
   - Session memory (expires 24h)
   - Query results (expires 1h)

2. Vector store cache (embeddings)
   - Computed embeddings (persistent)

3. Application cache
   - User objects (expires 30m)
   - Document stats (expires 1h)
```

### Batch Operations

```python
# Instead of individual inserts
chunks = [...]
for chunk in chunks:
    db.add(chunk)
    await db.commit()  # Slow!

# Do batch insert
db.add_all(chunks)
await db.commit()  #Fast!
```

## Security Architecture

### Authentication Flow

```
1. User submits login
2. Backend verifies password (bcrypt)
3. Server creates JWT token
   {
     "sub": "user_id",
     "role": "employee",
     "exp": 1705318200
   }
4. Token sent to client (localStorage)
5. Client sends token in header
   Authorization: Bearer <token>
6. Server validates token
7. Route executes with user context
```

### Access Control

```
Route Auth Flow:

GET /documents
  ↓
@router.get()
  ↓
current_user = get_current_user(token)
  ↓
Decode JWT, verify expiry
  ↓
Extract user_id and role
  ↓
Return user_id to route handler
  ↓
Handler uses user_id to filter data
  ↓
Query: SELECT * FROM documents WHERE uploaded_by_id = {user_id}
```

### Role-Based Access

```python
# Employee can only access their own data
GET /documents/1
  ├── Check: document owner == current user
  └── OR: current user is admin
       └── Allow

# Admin endpoints
GET /admin/users
  ├── Check: current_user.role == "admin"
  └── If not: 403 Forbidden
```

## Scalability Patterns

### Horizontal Scaling

```
Load Balancer
    ├─ Backend 1:8001
    ├─ Backend 2:8002
    ├─ Backend 3:8003
    └─ Backend N:800N

All share:
- PostgreSQL (connection pooling)
- Redis
- Vector Store
```

### Caching Layers

```
User Request
    ↓
[L1] Redis Cache (milliseconds)
    ├ Hit → Return
    └ Miss → L2
         ↓
    [L2] Database Query
         ├ Result → Cache in L1
         └ Return
```

### Async Processing

```
Heavy Operation Request
    ↓
Add to Redis Queue
    ↓
Return: "Processing..."
    ↓
Background Worker
(Celery/RQ task)
    ├ Process
    └ Store result
        ↓
Client polls endpoint
    ↓
Result ready → Return
```

## Monitoring & Observability

### Metrics Collection

```
Application
├── API Response Times
│   └ Endpoint: /chat/query
│      └ P50: 150ms, P95: 500ms, P99: 2s
├── Error Rates
│   └ 5xx: 0.1%
│   └ 4xx: 2%
└── Resource Usage
    ├── CPU: 45%
    ├── Memory: 2.1GB
    └── Disk: 50GB

Database
├── Query Times
├── Connection Pool
└── Replication Lag

Vector Store
├── Search Latency
└── Index Size
```

### Logging

```
Structure:
timestamp | level | service | message | user_id | request_id

Example:
2024-01-15T10:30:45.123Z | INFO | api | Document uploaded | user_id=1 | req_abc123
2024-01-15T10:30:46.456Z | Error | llm | OpenAI timeout | user_id=2 | req_abc124
```

---

This architecture is designed for:

- ✅ Scalability (horizontal scaling)
- ✅ Maintainability (clean layers)
- ✅ Security (auth, RBAC, validation)
- ✅ Performance (caching, indexing)
- ✅ Reliability (error handling, logging)
- ✅ Flexibility (pluggable components)
