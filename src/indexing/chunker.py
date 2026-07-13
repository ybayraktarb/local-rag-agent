from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.config import settings

class DocumentChunker:
    """
    Splitter that breaks documents down into chunk-sized pieces
    while trying to maintain logical structure (like tables) by prioritizing double newlines.
    """
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """
        Initializes the chunker with size and overlap configuration.
        """
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        
        # Use separators that preserve paragraphs and tables first before breaking down to lines or words
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", " ", ""]
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Splits a list of documents into chunks.
        
        Args:
            documents: List of LangChain Document objects.
            
        Returns:
            List[Document]: List of split document chunks.
        """
        return self.splitter.split_documents(documents)
