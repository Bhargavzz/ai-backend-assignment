from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.services.vector_service import vector_service

router = APIRouter()

@router.post("/documents/index", response_model=schemas.IndexResponse)
def index_documents(
    request: schemas.IndexRequest,
    db: Session = Depends(get_db)
):
    """Index documents for search"""
    indexed_count = 0
    failed_ids = []
    
    for doc_id in request.document_ids:
        # Get document
        document = db.query(models.Document).filter(
            models.Document.id == doc_id
        ).first()
        
        print(f"DEBUG: Doc {doc_id} - Found: {document is not None}")
        
        if not document:
            print(f"DEBUG: Doc {doc_id} - Not found")
            failed_ids.append(doc_id)
            continue
        
        print(f"DEBUG: Doc {doc_id} - Content length: {len(document.content) if document.content else 0}")
        
        if not document.content or not document.content.strip():
            print(f"DEBUG: Doc {doc_id} - No content")
            failed_ids.append(doc_id)
            continue
        
        try:
            print(f"DEBUG: Doc {doc_id} - Indexing...")
            vector_service.add_document(doc_id, document.content)
            indexed_count += 1
            print(f"DEBUG: Doc {doc_id} - Success")
        except ValueError as e:
            print(f"DEBUG: Doc {doc_id} - Already indexed: {e}")
            indexed_count += 1
        except Exception as e:
            print(f"DEBUG: Doc {doc_id} - Error: {e}")
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
   Search documents by semantic similarity
    """
    # Search FAISS for similar document IDs

    faiss_results = vector_service.search(request.query, top_k=request.top_k)

    if not faiss_results:
        return {
            "query": request.query,
            "results": [],
            "total_results": 0
        }
    
    # Get document IDs
    doc_ids = [doc_id for doc_id,_ in faiss_results]

    # Fetch full documents from DB
    documents = db.query(models.Document).filter(
        models.Document.id.in_(doc_ids)
    ).all()

    # Create lookup map
    doc_map: dict = {doc.id: doc for doc in documents}

    # Build results (wrt faiss order)
    results = []
    for doc_id, similarity_score in faiss_results:
        doc = doc_map.get(doc_id)
        if doc:
            results.append({
                "document_id": doc.id,
                "title":doc.title,
                "content":doc.content[:150] + "..." if len(doc.content) > 150 else doc.content,
                "similarity_score": similarity_score
            })
    
    return {
        "query": request.query,
        "results": results,
        "total_results": len(results)
    }
