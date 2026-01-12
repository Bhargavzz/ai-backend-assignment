from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.services.vector_service import vector_service
from app.services.chunking_service import chunking_service

router = APIRouter()

@router.post("/documents/index", response_model=schemas.IndexResponse)
def index_documents(
    request: schemas.IndexRequest,
    db: Session = Depends(get_db)
):
    """Updated: Index docs with chunking(efficient for large docs)

    1. retrieve docs from db
    2. chunk doc into smaller pieces
    3. index all chunks in faiss with metadata
    4. save to disk
    
    """
    indexed_count = 0
    failed_ids = []
    
    for doc_id in request.document_ids:
        # Get document
        document = db.query(models.Document).filter(
            models.Document.id == doc_id
        ).first()
        
        #print(f"DEBUG: Doc {doc_id} - Found: {document is not None}")
        
        if not document:
            print(f"DEBUG: Doc {doc_id} - Not found")
            failed_ids.append(doc_id)
            continue
        
        #print(f"DEBUG: Doc {doc_id} - Content length: {len(document.content) if document.content else 0}")
        
        if not document.content or not document.content.strip():
            #print(f"DEBUG: Doc {doc_id} - No content")
            failed_ids.append(doc_id)
            continue
        
        try:
            #1. Chunk the document
            chunks = chunking_service.chunk_text(document.content, doc_id, document.user_id)

            if not chunks:
                #print(f"DEBUG: Doc {doc_id} - No chunks created")
                failed_ids.append(doc_id)
                continue
            #2. Index all chunks
            vector_service.add_chunks(chunks)
            indexed_count += 1
        
        except Exception as e:
            #print(f"DEBUG: Doc {doc_id} - Indexing failed: {str(e)}")
            failed_ids.append(doc_id)
            
    
    
    return {
        "indexed_count": indexed_count,
        "failed_ids": failed_ids,
        "message": f"Indexed {indexed_count}/{len(request.document_ids)} documents"
    }

@router.post("/search", response_model=schemas.SearchResponse)
def search_documents(
    request: schemas.SearchRequest,
    db: Session = Depends(get_db)
):
    """
   Search relvant doc chunks by semantic similarity

   this returns chunks(not full docs as in previous version) with metadata
    """
    # Search FAISS for similar document IDs (filter by user_id if provided)
    user_id = getattr(request, 'user_id', None)
    chunk_results : list[dict] = vector_service.search(request.query, top_k=request.top_k, user_id=user_id)

    if not chunk_results:
        return {
            "query": request.query,
            "results": [],
            "total_results": 0
        }
    
    # Get unique document IDs to fetch titles
    doc_ids = list(set([chunk['doc_id'] for chunk in chunk_results]))

    # Fetch full documents from DB
    documents = db.query(models.Document).filter(
        models.Document.id.in_(doc_ids)
    ).all()

    # Create lookup map
    doc_map: dict = {doc.id: doc for doc in documents}

    # Build results with chunk data
    results = []
    for chunk in chunk_results:
        doc = doc_map.get(chunk['doc_id'])
        if doc:
            results.append(schemas.SearchResult(
                document_id=chunk['doc_id'],
                chunk_id=chunk['chunk_id'],
                title=doc.title,
                content=chunk['text'], # (updated to chunk text, not full doc)
                similarity_score=chunk['similarity_score']
            ))
    
    return {
        "query": request.query,
        "results": results,
        "total_results": len(results)
    }
