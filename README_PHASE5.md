# Phase 5: Streamlit UI with User Isolation

## Overview
Phase 5 implements a lightweight web UI using Streamlit to demonstrate document upload and AI querying capabilities. Key focus: **per-user data isolation** and **manual retry strategy** for indexing failures.

---

## Key Features

### 1. Tab-Based UI
- **Users Tab**: Create users and select active user
- **Documents Tab**: Upload documents with auto-indexing + manual retry
- **Chat Tab**: AI-powered chat with source citations

### 2. User Data Isolation
**Problem**: All users' documents were stored in a shared FAISS index, allowing cross-user data leakage.

**Solution**: Added `user_id` filtering throughout the pipeline:
- `chunking_service.chunk_text()` → includes `user_id` in chunk metadata
- `vector_service.search()` → filters results by `user_id`
- `agent_service.ask_agent()` → passes `user_id` to search
- Frontend passes `current_user_id` in all API calls

**Result**: Each user only sees their own documents in search/chat.

---

## Backend Modifications

### 1. Database Schema
**Changed**: `documents.content` column from `TEXT` (65KB limit) to `LONGTEXT` (4GB limit)
```sql
ALTER TABLE documents MODIFY content LONGTEXT;
```
**Reason**: Large PDFs with OCR text exceeded TEXT limit.

### 2. OCR Response Schema
**Added**: `document_id` field to `OCRResponse` schema
```python
class OCRResponse(BaseModel):
    document_id: int  # Added
    filename: str
    content_type: str
    extracted_text: str
```
**Reason**: Frontend needs doc ID immediately after upload for auto-indexing.

### 3. Search & Agent Schemas
**Added**: Optional `user_id` parameter
```python
class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    user_id: Optional[int] = None  # Added for filtering

class AskRequest(BaseModel):
    query: str
    user_id: Optional[int] = None  # Added for filtering
```

### 4. Intent Classification Improvement
**Changed**: Default fallback from `general` → `document_question`
```python
# Before: Always classified "What is X?" as general
# After: Defaults to searching documents unless clearly greeting/general
```
**Reason**: Too many document-related queries were misclassified as general knowledge.

---

## Manual Retry Strategy

### Decision
Rejected complex database status tracking (indexed_status field, compensating transactions) in favor of **simple manual retry**.

### Implementation
1. Upload → auto-attempts indexing
2. If indexing fails → error message + document appears in list
3. User clicks "Index" button → retries manually
4. No database schema changes required

### Benefits
- Simple to implement (~2-3 hours vs days)
- Clear user control
- No migration complexity
- Good UX with proper error messaging

---

## File Size Limit
**Frontend validation**: 10MB maximum
```python
MAX_FILE_SIZE_MB = 10 * 1024 * 1024
if file_size > MAX_FILE_SIZE_MB:
    st.error("File size exceeds 10 MB limit.")
```
Backend already validates (set in Phase 2).

---

## Known Limitations

### 1. Upload Performance
**Issue**: Even with small PDFs (0.5-1MB) take 10-30 seconds to upload and index.

**Root Cause**:
- Tesseract OCR: CPU-intensive, processes page-by-page
- Embedding generation: Sentence-transformers on CPU (not GPU)
- 50-100 chunks per document × 384-dim embedding calculation



### 2. Shared Index Storage
**Current**: All users' chunks in one `faiss_index.bin` + `chunk_metadata.json`

**Mitigation**: User-level filtering in application layer (not separate indexes per user)

**Alternative Considered**: Separate index per user (rejected due to complexity)

---

## Migration Notes

### Re-indexing Required
**After user_id changes**: All existing documents must be re-indexed.

**Steps**:
1. Delete old index files:
   ```bash
   rm faiss_index.bin chunk_metadata.json
   ```
2. Restart FastAPI server
3. Use Streamlit UI to click "Index" for each document

**Why**: Old chunks lack `user_id`, causing filter bypass.

---

## API Endpoint Usage

### Document Upload + Index
```http
POST /documents/upload
Content-Type: multipart/form-data

file: <PDF/image>
title: "document.pdf"
user_id: 1

Response: {
  "document_id": 12,
  "filename": "document.pdf",
  "content_type": "application/pdf",
  "extracted_text": "..."
}
```

### Search with User Filter
```http
POST /search
Content-Type: application/json

{
  "query": "machine learning",
  "top_k": 5,
  "user_id": 1
}
```

### AI Chat with User Filter
```http
POST /ai/ask
Content-Type: application/json

{
  "query": "What is in my documents?",
  "user_id": 1
}
```

---

## Running the Application

### Start Backend
```bash
uvicorn app.main:app --reload
```

### Start Frontend (Separate Terminal)
```bash
streamlit run streamlit_app.py
```

### Workflow
1. Open Streamlit UI (usually http://localhost:8501)
2. Configure Azure OpenAI credentials in sidebar
3. Create/select user in Users tab
4. Upload documents in Documents tab
5. Chat in Chat tab

---

## Code Organization

### Project Structure
```
d:\assignment\
├── ui/                         # Frontend UI modules
│   ├── __init__.py
│   ├── config.py              # Shared constants (API URL, limits)
│   ├── tab_users.py           # User creation/selection logic
│   ├── tab_documents.py       # Document upload/management logic
│   └── tab_chat.py            # AI chat interface logic
├── streamlit_app.py           # Main entry point (~100 lines)
└── app/                       # Backend API (existing)
    ├── routers/
    ├── services/
    └── models.py
```

### New Files (Phase 5)
- `streamlit_app.py` - Main Streamlit entry point with configuration and tab orchestration
- `ui/config.py` - Shared constants (API_BASE_URL, MAX_FILE_SIZE_MB, API_VERSION)
- `ui/tab_users.py` - User management tab (~50 lines)
- `ui/tab_documents.py` - Document upload/indexing tab (~130 lines)
- `ui/tab_chat.py` - AI chat interface tab (~100 lines)

### Modified Backend Files
- `app/models.py` - Changed Text → LONGTEXT
- `app/schemas.py` - Added document_id, user_id fields
- `app/routers/documents.py` - Fixed response to include document_id
- `app/routers/search.py` - Pass user_id to vector search
- `app/routers/ai.py` - Pass user_id to agent
- `app/services/chunking_service.py` - Include user_id in chunks
- `app/services/vector_service.py` - Filter by user_id
- `app/services/agent_service.py` - Updated state + improved classification

### Design Benefits
- **Separation of Concerns**: Each tab in its own module
- **Maintainability**: Easy to locate and modify specific features
- **Reusability**: Shared config prevents duplication
- **Scalability**: Simple to add new tabs or features


---

## Key Takeaways

1. **User isolation**: Application-layer filtering effective for multi-tenancy
2. **Schema evolution**: Database changes require re-indexing
3. **Performance trade-offs**: OCR + CPU embeddings = acceptable slowness for demo


