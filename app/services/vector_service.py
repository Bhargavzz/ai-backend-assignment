import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple, Dict
import json


class VectorService:
    """
    UPDATED:vector serivce for chunk based semantic search.

    Previously in phase 3,we indexed whole documents as single vectors.
    Now,we chunk documents into smaller parts and index each chunk separately.
    """

    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.dimension = 384
        
        #Create FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)

        # Map FAISS IDs to chunk metadata
        self.chunk_metadata: List[Dict] = []

        # File paths for saving/loading index
        self.index_path = "faiss_index.bin"
        self.metadata_path = "chunk_metadata.json"

        #Load existing index if it exits
        self._load_index()

    def _load_index(self):
        """Load saved index & metadata from disk"""
        if os.path.exists(self.index_path) and os.path.exists(self.metadata_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'r', encoding = 'utf-8') as f:
                self.chunk_metadata = json.load(f)

    def _save_index(self):
        """Save current index & metadata to disk"""

        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'w', encoding = 'utf-8') as f:
            json.dump(self.chunk_metadata, f, ensure_ascii=False, indent=4)
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Convert text to vector(384 numbers)"""
        if not text or not text.strip():
            return np.zeros(self.dimension, dtype=np.float32)
        
        #model converts text to numbers
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)
    
    def add_chunks(self, chunks: List[Dict]):
        """
        Add multiple chunks to the index.
        
        arguments:
            chunks: List of chunk dicts from chunking_service
                    [{text: "...", doc_id: 1, chunk_id: 0}, ...]
        
        This replaces add_document() from Phase 3.
        Now we index chunks, not full documents.
        """
        if not chunks:
            return
        
        # generate embeddings for all chunks
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.model.encode(texts, convert_to_numpy=True).astype(np.float32)

        # add to FAISS
        self.index.add(embeddings)

        # store metadata for each chunk

        for chunk in chunks:
            self.chunk_metadata.append({
                'doc_id': chunk['doc_id'],
                'chunk_id': chunk['chunk_id'],
                'text': chunk['text']
            })

        # save index
        self._save_index()
    
    def search(self, query: str,top_k: int =5) -> List[Dict]:
        """
        Search for similar chunks.
        
        Returns: List of chunk results with metadata
        [
            {
                'doc_id': 1,
                'chunk_id': 0,
                'text': 'chunk content...',
                'similarity_score': 0.42
            },
            ...
        ]
        """
        #no docs indexed yet
        if self.index.ntotal == 0:
            return []
        
        #query to vector
        query_embedding = self.generate_embedding(query).reshape(1,-1)

        #search in FAISS and it returns distances and internal IDs
        distances, indices = self.index.search(query_embedding,min(top_k,self.index.ntotal))

        #convert faiss IDs to document IDs
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx != -1: #-1 refers to empty slot
                meta = self.chunk_metadata[idx]
                results.append({
                    'doc_id': meta['doc_id'],
                    'chunk_id': meta['chunk_id'],
                    'text': meta['text'],
                    'similarity_score': float(distance)
                })
            
        return results
    
# create single instance
vector_service = VectorService()

         
        
        
        
