# Phase 3: Vector Search & Semantic Retrieval

## Overview

Phase 3 implements semantic search functionality using FAISS vector database and sentence transformers for embeddings. Users can index document text and perform intelligent semantic searches that understand meaning, not just keywords.

### Key Features
- **Semantic Embeddings**: Convert document text to 384-dimensional vectors
- **FAISS Indexing**: Fast similarity search using Facebook's FAISS library
- **Persistent Storage**: Indexes saved to disk and restored on restart
- **REST API**: Two simple endpoints for indexing and searching

---

## Architecture

### How It Works

```
INDEXING:
Document Text → Sentence Transformer (embedding model) → 384-dim Vector → FAISS Index

SEARCHING:
Query Text → Embedding → Find Similar Vectors in FAISS → Fetch Docs from MySQL → Return Results
```

### Components

1. **Vector Service** (`app/services/vector_service.py`)
   - Generates embeddings using sentence-transformers
   - Manages FAISS index
   - Maps FAISS IDs to document IDs
   - Handles persistence (save/load)

2. **Search Router** (`app/routers/search.py`)
   - `/documents/index` - Index documents for search
   - `/search` - Perform semantic search

3. **Schemas** (`app/schemas.py`)
   - `IndexRequest` - List of document IDs to index
   - `SearchRequest` - Query and top_k results
   - `SearchResponse` - Results with similarity scores

---

## Installation

### 1. Install Dependencies

```bash
pip install faiss-cpu sentence-transformers
```

Or update requirements.txt:
```
faiss-cpu==1.8.0
sentence-transformers==2.2.2
```

Then install:
```bash
pip install -r requirements.txt
```

### 2. Start Server

```bash
uvicorn app.main:app --reload
```

---

## API Endpoints

### 1. Index Documents

**Endpoint:** `POST /documents/index`

**Purpose:** Index documents into FAISS for semantic search

**Request:**
```json
{
  "document_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "indexed_count": 3,
  "failed_ids": [],
  "message": "Indexed 3/3 documents"
}
```

**What Happens:**
1. Fetches documents from MySQL
2. Validates content exists
3. Generates embeddings for each document
4. Stores vectors in FAISS
5. Saves index to disk

**Error Handling:**
- Non-existent document IDs → Added to `failed_ids`
- Empty content → Skipped
- Already indexed → Counted as success

---

### 2. Search Documents

**Endpoint:** `POST /search`

**Purpose:** Perform semantic search over indexed documents

**Request:**
```json
{
  "query": "machine learning algorithms",
  "top_k": 5
}
```

**Response:**
```json
{
  "query": "machine learning algorithms",
  "results": [
    {
      "document_id": 1,
      "title": "ML Guide",
      "content": "Machine learning uses neural networks...",
      "similarity_score": 0.234
    },
    {
      "document_id": 4,
      "title": "AI Basics",
      "content": "Artificial intelligence includes...",
      "similarity_score": 0.512
    }
  ],
  "total_results": 2
}
```

**Parameters:**
- `query` (required): Search query string (1-500 characters)
- `top_k` (optional): Number of results to return (1-20, default: 5)

**What Happens:**
1. Converts query to embedding
2. Searches FAISS for similar vectors
3. Fetches full documents from MySQL
4. Returns results ranked by similarity

**Similarity Score:**
- Lower = More similar (L2 distance)
- 0.0 = Exact match (rare)
- < 1.0 = Very similar
- > 2.0 = Less relevant

---

## Testing

### Quick Test via Swagger UI

1. Open: `http://127.0.0.1:8000/docs`
2. Find `POST /documents/index` endpoint
3. Click "Try it out"
4. Enter: `{"document_ids": [1, 2, 3]}`
5. Click "Execute"

Then test search:
1. Find `POST /search` endpoint
2. Click "Try it out"
3. Enter: `{"query": "machine learning", "top_k": 3}`
4. Click "Execute"

### Via cURL

**Index documents:**
```bash
curl -X POST "http://127.0.0.1:8000/documents/index" \
  -H "Content-Type: application/json" \
  -d '{"document_ids": [1, 2, 3]}'
```

**Search:**
```bash
curl -X POST "http://127.0.0.1:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "artificial intelligence", "top_k": 5}'
```

---

## File Structure

```
app/
├── services/
│   └── vector_service.py          # Embedding & FAISS logic
├── routers/
│   └── search.py                  # Index & search endpoints
├── schemas.py                     # Request/response models
└── main.py                        # Register routes

faiss_index.bin                   # Persisted FAISS index
faiss_id_map.npy                  # Document ID mappings
```

---

## How Embeddings Work

### Sentence Transformers

We use `sentence-transformers/all-MiniLM-L6-v2`:
- **Input**: Any text (document or query)
- **Output**: 384-dimensional vector
- **Purpose**: Capture semantic meaning

**Example:**
```
"machine learning"     → [0.2, 0.8, 0.1, ...]
"artificial intelligence" → [0.25, 0.78, 0.12, ...]  (similar vectors)
"pizza recipe"         → [0.9, 0.1, 0.05, ...]       (different vector)
```

Similar meanings = Similar vectors = Found by FAISS

### FAISS (IndexFlatL2)

- **Type**: Flat brute-force search with L2 distance
- **Behavior**: Compares query against every indexed document
- **Performance**: Fast for < 100K documents
- **Accuracy**: Always finds true nearest neighbors

---

## Common Issues

### Issue 1: No Results Returned
**Cause**: Documents not indexed
**Solution**: Call `/documents/index` with document IDs first

### Issue 2: indexed_count = 0
**Cause**: Document doesn't exist or has no content
**Solution**: 
1. Check document exists: `GET /users/{user_id}/documents`
2. Verify content is not empty
3. Try indexing again

### Issue 3: Search returns wrong results
**Cause**: Semantic meaning differs from expectations
**Solution**: This is expected. Embeddings capture semantic meaning, not keyword matching. Query "neural networks" returns "deep learning" docs (semantically similar).

### Issue 4: Index lost after restart
**Cause**: Disk space or file permissions
**Solution**: Delete `faiss_index.bin` and `faiss_id_map.npy`, restart, re-index

---



---

## Limitations & Future Improvements

### Current Limitations
- No support for deleting indexed documents
- Single embedding model (can't change without re-indexing)
- In-memory index (restarts lose unsaved changes, but we auto-save)

### Future Improvements (Phase 4+)
- **Chunking**: Split long documents into paragraphs before indexing
- **Hybrid Search**: Combine semantic + keyword search
- **Batch Operations**: Re-index all documents at once
- **Advanced Models**: Use larger/specialized embedding models

---

## Integration with Other Phases

### From Phase 2 (OCR Upload)
```
Upload PDF → OCR extracts text → Save to MySQL
                                      ↓
                        (Manual) Index via /documents/index
                                      ↓
                           Vector stored in FAISS
```



---

## Environment Variables

No additional environment variables needed for Phase 3.

The service uses default paths:
- `faiss_index.bin` - Current directory
- `faiss_id_map.npy` - Current directory

---

## Summary

Phase 3 provides semantic search capabilities by:
1. Converting documents to embeddings
2. Storing embeddings in FAISS
3. Finding similar documents by query meaning
4. Returning ranked results

**Two simple endpoints:**
- Index documents for search
- Search by semantic meaning

