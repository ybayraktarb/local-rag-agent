from src.config import settings
from src.indexing.vectorstore_manager import VectorStoreManager
from src.retrieval.retriever_middleware import RetrieverMiddleware

class AgentBuilder:
    """
    Builder class that constructs and wires together the RAG agent pipeline.
    Adheres to Dependency Inversion by using configuration-based instantiation.
    """
    
    @staticmethod
    def build_agent(persist_directory: str = None) -> RetrieverMiddleware:
        """
        Builds and returns the configured RAG middleware pipeline.
        
        Args:
            persist_directory: Directory for the vector database.
            
        Returns:
            RetrieverMiddleware: The ready-to-query RAG middleware.
        """
        db_dir = persist_directory or settings.DB_DIR
        # Instantiate dependencies
        vstore_manager = VectorStoreManager(persist_directory=db_dir)
        middleware = RetrieverMiddleware(vectorstore_manager=vstore_manager)
        return middleware
