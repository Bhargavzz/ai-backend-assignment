from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List, Dict

class ChunkingService:
    """
    Service to chunk text using LangChain's RecursiveCharacterTextSplitter, respects semantic boundaries (paragraphs, sentences).
    """

    def __init__(self,chunk_size: int = 500, overlap: int =50) -> None:
        """
        arguments:
            chunk_size: No.of words per chunk
            overlap: No.of words to overlap b/w chunks
        """
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len # uses char length for splitting
        )
    
    def chunk_text(self, text: str, doc_id: int, user_id: int) -> List[Dict]:
        """
        arguments:
            text: full doc text
            doc_id: document id from db
            user_id: owner user id for filtering
        
        returns:
            list of dicts: [{
                'text': chunkned content,
                'doc_id':1,
                'chunk_id':0,
                'user_id':1,
                'char_count':500}, ...]  ---> list of dicts with chunk metadata
        """

        if not text or not text.strip():
            return []
        
        chunk_texts = self.splitter.split_text(text)

        # add chunk metadata

        chunks = []
        for idx, chunk_text in enumerate(chunk_texts):
            chunks.append({
                'text': chunk_text,
                'doc_id': doc_id,
                'chunk_id': idx,
                'user_id': user_id,
                'char_count': len(chunk_text)
            })
        
        return chunks
    

# Global instance
chunking_service = ChunkingService(chunk_size=2000, overlap=200) #2000 chars ~ 500 tokens

        
    