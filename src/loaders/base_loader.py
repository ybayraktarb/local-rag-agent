from abc import ABC, abstractmethod
from typing import List
from langchain_core.documents import Document

class BaseLoader(ABC):
    """
    Base loader interface that all specific document loaders must implement.
    """
    
    def __init__(self, file_path: str):
        """
        Initializes the loader with a file path.
        
        Args:
            file_path: Path to the document file.
        """
        self.file_path = file_path

    @abstractmethod
    def load(self) -> List[Document]:
        """
        Loads and parses the document file.
        
        Returns:
            List[Document]: A list of parsed LangChain Document objects.
        """
        pass
