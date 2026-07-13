import os
from src.loaders.base_loader import BaseLoader
from src.loaders.pdf_loader import PDFLoader

class LoaderFactory:
    """
    Factory class to return the appropriate document loader based on file extension.
    Adheres to the Open/Closed Principle.
    """
    
    @staticmethod
    def get_loader(file_path: str) -> BaseLoader:
        """
        Returns the appropriate document loader based on the file extension.
        
        Args:
            file_path: Path to the file to load.
            
        Returns:
            BaseLoader: An instance of a class implementing BaseLoader.
            
        Raises:
            ValueError: If the file extension is not supported.
        """
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == ".pdf":
            return PDFLoader(file_path)
        else:
            raise ValueError(f"Desteklenmeyen dosya uzantısı: {ext}")
