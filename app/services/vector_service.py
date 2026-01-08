import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from typing import List, Tuple


class VectorService:

    def __init__(self):
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        self.dimension = 384
        
        #Create FAISS index
        self.index = faiss.IndexFlatL2(self.dimension)

        # Map FAISS IDs to mysql document IDs
        self.id_map: List[int] = []

        # File paths for saving/loading index
        self.index_path = "faiss_index.bin"
        self.id_map_path = "faiss_id_map.npy"

        #Load existing index if it exits
        self._load_index()

    def _load_index(self):
        """Load saved index from disk"""
        if os.path.exists(self.index_path) and os.path.exists(self.id_map_path):
            self.index = faiss.read_index(self.index_path)
            self.id_map = np.load(self.id_map_path).tolist()

    def _save_index(self):
        """Save current index to disk"""

        faiss.write_index(self.index, self.index_path)
        np.save(self.id_map_path, np.array(self.id_map))
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """Convert text to vector(384 numbers)"""
        if not text or not text.strip():
            return np.zeros(self.dimension, dtype=np.float32)
        
        #model converts text to numbers
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)
    
    def add_document(self, document_id: int, text:str):
        """
        Add one document to the index
        
        Steps:
        1. Convert text to embedding (vector)
        2. Add vector to FAISS
        3. Remember which FAISS ID maps to our document_id
        4. Save to disk
        """
        #check if already indexed
        if document_id in self.id_map:
            raise ValueError(f"Document ID {document_id} already indexed.")
    
        # text to vector

        embedding = self.generate_embedding(text)

        # add to FAISS (needs shape (1,384) for single vector)
        self.index.add(embedding.reshape(1,-1))
         
        # map FAISS internal ID to document_id
        self.id_map.append(document_id)

        #save index
        self._save_index()
    
    def search(self, query: str,top_k: int =5) -> List[Tuple[int,float]]:
        """
        Search for similar documents
        
        Returns: List of (document_id, distance_score)
        Lower distance = more similar
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
                doc_id = self.id_map[idx]
                results.append((doc_id, float(distance)))
            
        return results
    
# create single instance
vector_service = VectorService()

         
        
        
        
