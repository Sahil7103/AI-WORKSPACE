# API Documentation

Complete API reference for AI Workplace Copilot.

## Base URL

- **Local Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## Authentication

All endpoints (except `/auth/*`) require JWT token in `Authorization` header:

```
Authorization: Bearer <your_jwt_token>
```

## Response Format

All responses are JSON:

### Success Response

```json
{
  "data": {...},
  "status": 200
}
```

### Error Response

```json
{
  "detail": "Error message",
  "status": 400
}
```

---

## Auth Endpoints

### POST `/auth/register`

Register a new user.

**Request:**

```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "employee",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**

- `400` - User already exists
- `422` - Validation error

---

### POST `/auth/login`

Authenticate and get JWT token.

**Request:**

```json
{
  "username": "john_doe",
  "password": "SecurePass123!"
}
```

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "john_doe",
    "email": "john@example.com",
    "role": "employee",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Errors:**

- `401` - Invalid credentials
- `422` - Validation error

---

### GET `/auth/me`

Get current authenticated user info.

**Headers:**

```
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "full_name": "John Doe",
  "role": "employee",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**

- `401` - Unauthorized
- `404` - User not found

---

## Document Endpoints

### POST `/documents/upload`

Upload a new document.

**Headers:**

```
Authorization: Bearer <token>
Content-Type: multipart/form-data
```

**Form Data:**

```
file: <binary file content>
```

**Supported formats:** PDF, DOCX, TXT (max 50MB)

**Response:** `200 OK`

```json
{
  "id": 1,
  "filename": "quarterly_report.pdf",
  "file_type": "pdf",
  "size_bytes": 2048000,
  "is_processed": true,
  "embedding_generated": true,
  "created_at": "2024-01-15T10:30:00Z",
  "uploaded_by_id": 1
}
```

**Errors:**

- `400` - File too large
- `401` - Unauthorized
- `422` - Invalid file type

---

### GET `/documents`

List user's documents with pagination.

**Headers:**

```
Authorization: Bearer <token>
```

**Query Parameters:**

- `skip` (int, default: 0) - Offset for pagination
- `limit` (int, default: 20) - Number of results

**Response:** `200 OK`

```json
{
  "total": 5,
  "skip": 0,
  "limit": 20,
  "documents": [
    {
      "id": 1,
      "filename": "quarterly_report.pdf",
      "file_type": "pdf",
      "size_bytes": 2048000,
      "is_processed": true,
      "embedding_generated": true,
      "created_at": "2024-01-15T10:30:00Z",
      "uploaded_by_id": 1
    }
  ]
}
```

**Errors:**

- `401` - Unauthorized

---

### GET `/documents/{doc_id}`

Get detailed document info with chunks.

**Headers:**

```
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "filename": "quarterly_report.pdf",
  "file_type": "pdf",
  "size_bytes": 2048000,
  "is_processed": true,
  "embedding_generated": true,
  "created_at": "2024-01-15T10:30:00Z",
  "uploaded_by_id": 1,
  "content": "Full document text...",
  "chunks": [
    {
      "id": 1,
      "chunk_text": "First 500 characters of document...",
      "chunk_index": 0,
      "document_id": 1
    }
  ]
}
```

**Errors:**

- `401` - Unauthorized
- `403` - Access denied
- `404` - Document not found

---

### DELETE `/documents/{doc_id}`

Delete a document.

**Headers:**

```
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "message": "Document deleted"
}
```

**Errors:**

- `401` - Unauthorized
- `403` - Access denied
- `404` - Document not found

---

## Chat Endpoints

### POST `/chat/sessions`

Create a new chat session.

**Headers:**

```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**

```json
{
  "session_name": "Q&A about Q4 Results"
}
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "session_name": "Q&A about Q4 Results",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Errors:**

- `401` - Unauthorized
- `422` - Validation error

---

### GET `/chat/sessions`

List user's chat sessions.

**Headers:**

```
Authorization: Bearer <token>
```

**Query Parameters:**

- `skip` (int, default: 0)
- `limit` (int, default: 20)

**Response:** `200 OK`

```json
{
  "total": 3,
  "sessions": [
    {
      "id": 1,
      "session_name": "Q&A about Q4 Results",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:45:00Z"
    }
  ]
}
```

**Errors:**

- `401` - Unauthorized

---

### GET `/chat/sessions/{session_id}`

Get session details with all messages.

**Headers:**

```
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "id": 1,
  "session_name": "Q&A about Q4 Results",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:45:00Z",
  "messages": [
    {
      "id": 1,
      "role": "user",
      "content": "What was our Q4 revenue?",
      "sources": null,
      "created_at": "2024-01-15T10:31:00Z"
    },
    {
      "id": 2,
      "role": "assistant",
      "content": "According to the Q4 report...",
      "sources": "[{\"doc_id\": 1, \"filename\": \"q4_report.pdf\", \"similarity\": 0.95}]",
      "created_at": "2024-01-15T10:31:30Z"
    }
  ]
}
```

**Errors:**

- `401` - Unauthorized
- `403` - Not your session
- `404` - Session not found

---

### POST `/chat/query`

Send a query and get a response (non-streaming).

**Headers:**

```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**

```json
{
  "session_id": 1,
  "query": "What were the key challenges mentioned?",
  "document_ids": [1, 2]
}
```

**Response:** `200 OK`

```json
{
  "message_id": 42,
  "session_id": 1,
  "query": "What were the key challenges mentioned?",
  "response": "Based on the retrieved documents, the key challenges mentioned include...",
  "sources": [
    {
      "doc_id": 1,
      "filename": "quarterly_report.pdf",
      "chunk_index": 3,
      "similarity": 0.94
    },
    {
      "doc_id": 2,
      "filename": "management_notes.docx",
      "chunk_index": 1,
      "similarity": 0.87
    }
  ],
  "response_time_ms": 245,
  "streaming": false
}
```

**Errors:**

- `401` - Unauthorized
- `403` - Not your session or no document access
- `404` - Session not found
- `500` - LLM error

---

### POST `/chat/query-stream`

Send a query and stream the response (Server-Sent Events).

**Headers:**

```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request:**

```json
{
  "session_id": 1,
  "query": "Summarize the main points"
}
```

**Response:** `200 OK` (SSE Stream)

```
data: {"token": "Based"}
data: {"token": " on"}
data: {"token": " the"}
data: {"token": " documents"}
...
```

Client example (JavaScript):

```javascript
const response = await fetch("/chat/query-stream", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ session_id: 1, query: "Your question" }),
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const text = decoder.decode(value);
  const lines = text.split("\n");

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const data = JSON.parse(line.slice(6));
      console.log("Token:", data.token);
    }
  }
}
```

---

### DELETE `/chat/sessions/{session_id}`

Delete a chat session.

**Headers:**

```
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "message": "Session deleted"
}
```

**Errors:**

- `401` - Unauthorized
- `403` - Not your session
- `404` - Session not found

---

## Admin Endpoints

⚠️ **Requires `role: "admin"`**

### GET `/admin/users`

List all users (admin only).

**Headers:**

```
Authorization: Bearer <admin_token>
```

**Query Parameters:**

- `skip` (int, default: 0)
- `limit` (int, default: 50)

**Response:** `200 OK`

```json
{
  "total": 15,
  "users": [
    {
      "id": 1,
      "username": "admin_user",
      "email": "admin@example.com",
      "full_name": "Admin User",
      "role": "admin",
      "is_active": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Errors:**

- `401` - Unauthorized
- `403` - Not admin

---

### PUT `/admin/users/{user_id}/role`

Update user role.

**Headers:**

```
Authorization: Bearer <admin_token>
Content-Type: application/json
```

**Request:**

```json
{
  "role": "admin"
}
```

**Allowed roles:** `"admin"`, `"employee"`

**Response:** `200 OK`

```json
{
  "id": 2,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "admin",
  "is_active": true
}
```

**Errors:**

- `400` - Invalid role
- `401` - Unauthorized
- `403` - Not admin
- `404` - User not found

---

### GET `/admin/stats`

Get system statistics.

**Headers:**

```
Authorization: Bearer <admin_token>
```

**Response:** `200 OK`

```json
{
  "total_documents": 42,
  "total_processed": 40,
  "total_with_embeddings": 40,
  "total_chunks": 1205
}
```

**Errors:**

- `401` - Unauthorized
- `403` - Not admin

---

### POST `/admin/cache/clear`

Clear all Redis cache.

**Headers:**

```
Authorization: Bearer <admin_token>
```

**Response:** `200 OK`

```json
{
  "message": "Cache cleared"
}
```

**Errors:**

- `401` - Unauthorized
- `403` - Not admin

---

## Agent Endpoints

### GET `/agents/actions`

List available agent actions.

**Headers:**

```
Authorization: Bearer <token>
```

**Response:** `200 OK`

```json
{
  "actions": [
    {
      "name": "summarize_document",
      "description": "Generate a summary of a document",
      "parameters": {
        "doc_id": "int"
      }
    },
    {
      "name": "generate_report",
      "description": "Generate a report from multiple documents",
      "parameters": {
        "doc_ids": "List[int]",
        "report_type": "str"
      }
    }
  ]
}
```

---

### POST `/agents/actions/{action_name}`

Execute an agent action.

**Headers:**

```
Authorization: Bearer <token>
Content-Type: application/json
```

**Request Example (summarize):**

```json
{
  "doc_id": 1
}
```

**Response:** `200 OK`

```json
{
  "status": "success",
  "action": "summarize_document",
  "result": {
    "action": "summarize",
    "doc_id": 1,
    "summary": "This document discusses..."
  }
}
```

**Errors:**

- `400` - Invalid parameters
- `401` - Unauthorized
- `500` - Execution error

---

## Health Endpoint

### GET `/health`

Check API health.

**Response:** `200 OK`

```json
{
  "status": "healthy",
  "environment": "production"
}
```

---

## Error Codes

| Code | Meaning                              |
| ---- | ------------------------------------ |
| 200  | Success                              |
| 400  | Bad Request                          |
| 401  | Unauthorized (invalid/missing token) |
| 403  | Forbidden (insufficient permissions) |
| 404  | Not Found                            |
| 422  | Validation Error                     |
| 500  | Internal Server Error                |

---

## Rate Limiting

Currently implemented at basic level. In production:

- 100 requests per minute per user
- 10 large document uploads per day

---

## Pagination

List endpoints support pagination:

```
GET /endpoint?skip=0&limit=20
```

Response format:

```json
{
  "total": 100,
  "skip": 0,
  "limit": 20,
  "items": [...]
}
```

---

For interactive documentation, visit `/docs` after starting the server.
