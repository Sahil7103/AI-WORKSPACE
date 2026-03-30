# Development Guide

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your settings
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file (optional)
echo "VITE_API_URL=http://localhost:8000" > .env.local
```

### Database Setup

```bash
# Start PostgreSQL (Docker recommended)
docker run -d \
  --name ai-copilot-postgres \
  -e POSTGRES_PASSWORD=aipassword \
  -e POSTGRES_DB=ai_workplace_copilot \
  -p 5432:5432 \
  postgres:15-alpine

# Start Redis
docker run -d \
  --name ai-copilot-redis \
  -p 6379:6379 \
  redis:7-alpine

# Verify connections
psql -h localhost -U postgres -d ai_workplace_copilot
redis-cli ping
```

## Running Locally

### Terminal 1: Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
# Server runs on http://localhost:8000
# Docs on http://localhost:8000/docs
```

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
# App runs on http://localhost:3000
```

### Terminal 3 (Optional): Redis/PostgreSQL monitoring

```bash
docker ps
```

## Code Structure Overview

### Backend (`backend/app/`)

1. **core/** - Configuration & infrastructure
   - `config.py` - Settings from environment
   - `security.py` - JWT, hashing, auth
   - `database.py` - DB connection setup

2. **models/** - Database models
   - User, Document, ChatSession, ChatMessage
   - DocumentChunk, ApiLog, EvaluationMetric

3. **schemas/** - Request/response validation
   - Pydantic models for API
   - Type hints and doc strings

4. **services/** - Business logic
   - UserService - user operations
   - DocumentService - document management
   - ChatService - session & message handling
   - LLMService/QueryService - AI interactions

5. **rag/** - RAG pipeline
   - chunking.py - Text splitting strategies
   - embeddings.py - Embedding models
   - vector_store.py - FAISS/Pinecone wrapper
   - retriever.py - RAG orchestration

6. **api/** - REST endpoints
   - auth.py - Login/register
   - documents.py - Upload/manage
   - chat.py - Query/sessions
   - admin.py - User management
   - agents.py - AI actions

7. **utils/** - Helpers
   - cache.py - Redis operations
   - logger.py - Logging setup
   - file_handler.py - File operations

### Frontend (`frontend/src/`)

1. **pages/** - Page components
   - LoginPage / RegisterPage
   - DashboardPage
   - ChatPage
   - DocumentsPage
   - AdminPage

2. **components/** - Reusable UI
   - Header - Top navigation
   - Sidebar - Left menu
   - ProtectedRoute - Auth guard
   - ChatMessage - Message display
   - DocumentCard - Document preview

3. **services/** - API client
   - api.js - Axios instance & endpoints

4. **utils/** - Helpers
   - helpers.js - Date formatting, etc.

5. **styles/** - Global CSS
   - Tailwind + custom styles

## Development Workflow

### Adding an API Endpoint

1. **Define the schema** in `app/schemas/__init__.py`:

```python
class NewResourceCreate(BaseModel):
    name: str
    description: Optional[str] = None

class NewResourceResponse(BaseModel):
    id: int
    name: str
    ...
```

2. **Add the model** in `app/models/__init__.py`:

```python
class NewResource(Base):
    __tablename__ = "new_resources"
    id = Column(Integer, primary_key=True)
    # ... columns
```

3. **Create service** in `app/services/new_resource_service.py`:

```python
class NewResourceService:
    @staticmethod
    async def create(db: AsyncSession, data: NewResourceCreate):
        # business logic
        pass
```

4. **Add route** in `app/api/resources.py`:

```python
@router.post("/resources", response_model=NewResourceResponse)
async def create_resource(
    data: NewResourceCreate,
    db: AsyncSession = Depends(get_db),
):
    resource = await NewResourceService.create(db, data)
    return resource
```

5. **Include router** in `app/main.py`:

```python
from app.api import resources
app.include_router(resources.router)
```

6. **Test it**:

```bash
curl -X POST http://localhost:8000/resources \
  -H "Content-Type: application/json" \
  -d '{"name": "Test"}'
```

### Adding a React Component

1. **Create the component**:

```jsx
// src/components/MyComponent.jsx
export default function MyComponent({ data, onAction }) {
  return <div className="card">{/* JSX */}</div>;
}
```

2. **Use in a page**:

```jsx
import MyComponent from '../components/MyComponent'

export default function MyPage() {
  const [data, setData] = useState([])

  useEffect(() => {
    // Fetch data
  }, [])

  return <MyComponent data={data} onAction={...} />
}
```

3. **Add API call** in `services/api.js`:

```javascript
export const myAPI = {
  get: (id) => api.get(`/my-endpoint/${id}`),
  create: (data) => api.post("/my-endpoint", data),
};
```

## Testing

### Backend Tests

```bash
cd backend

# Run all tests
pytest

# Run specific test
pytest tests/test_api.py::test_user_creation

# Run with coverage
pytest --cov=app tests/

# Run in watch mode
pytest-watch
```

### Frontend Tests (Optional)

```bash
cd frontend

# Run tests
npm test

# Watch mode
npm test -- --watch
```

### Example Test

```python
# tests/test_my_feature.py
import pytest
from app.services.my_service import MyService
from app.schemas import MyRequest

@pytest.mark.asyncio
async def test_my_feature(test_db):
    """Test my feature."""
    data = MyRequest(name="test")
    result = await MyService.create(test_db, data)

    assert result.id is not None
    assert result.name == "test"
```

## Debugging

### Backend

**Using pdb:**

```python
import pdb; pdb.set_trace()  # In code
```

**Using VS Code Debugger:**
Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend"
    }
  ]
}
```

### Frontend

**Browser DevTools:**

- F12 to open
- Console tab for errors
- Network tab for API calls
- React DevTools extension

**VS Code Debugger:**
Install "Debugger for Chrome" extension

## Database Migrations

For production, use Alembic:

```bash
cd backend

# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

For development, you can recreate the database:

```bash
# Delete and recreate
python -c "
from app.core.database import init_db, engine
import asyncio

async def setup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(setup())
"
```

## Performance Optimization

### RAG Pipeline

- Adjust `CHUNK_SIZE` for your documents
- Use `similarity_threshold` to filter low-quality results
- Cache embeddings computations

### Queries

- Add database indexes on frequently searched columns
- Use Redis caching for expensive operations
- Implement pagination

### Frontend

- Code splitting with React.lazy()
- Image optimization
- CSS/JS minification (Vite handles this)

## Environment Variables Reference

```env
# Essential
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
SECRET_KEY=your-secret

# Optional (mock by default)
OPENAI_API_KEY=sk-...

# Customization
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_FILE_SIZE_MB=50
```

## Common Commands

```bash
# Backend
cd backend
source venv/bin/activate          # Activate venv
pip install -r requirements.txt   # Install deps
uvicorn app.main:app --reload    # Start dev server
pytest                            # Run tests

# Frontend
cd frontend
npm install                       # Install deps
npm run dev                      # Start dev server
npm run build                    # Build for prod
npm run preview                  # Preview build

# Docker
docker-compose -f docker/docker-compose.yml up -d    # Start all
docker-compose -f docker/docker-compose.yml down      # Stop all
docker-compose -f docker/docker-compose.yml logs backend  # View logs
```

---

Happy coding! 🎉
