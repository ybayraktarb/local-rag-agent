import os
import logging
from typing import List, Tuple
from langchain_chroma import Chroma
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.documents import Document
from src.config import settings

logger = logging.getLogger(__name__)

class VectorStoreManager:
    """
    Manages connection to the Chroma Vector Database.
    Exposes APIs to save, delete, and query document embeddings using Ollama.
    """
    
    def __init__(self, persist_directory: str = None, collection_name: str = "rag_qa_collection"):
        """
        Initializes the VectorStoreManager and connects to Chroma.
        Verifies embedding model compatibility.
        """
        self.persist_directory = persist_directory or settings.DB_DIR
        self.collection_name = collection_name
        
        # Initialize LangChain OllamaEmbeddings
        self.embeddings = OllamaEmbeddings(
            model=settings.EMBED_MODEL,
            base_url="http://localhost:11434"
        )
        
        self.meta_file = os.path.join(self.persist_directory, "embedding_model.meta")
        self._check_embedding_model_compatibility()

        self.db = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.persist_directory,
            collection_metadata={"hnsw:space": "cosine"}
        )

    def _check_embedding_model_compatibility(self):
        """
        Checks if the saved vector store was generated using the same embedding model.
        Logs a warning if a mismatch is found to prompt re-indexing.
        """
        os.makedirs(self.persist_directory, exist_ok=True)
        current_model = settings.EMBED_MODEL
        
        if os.path.exists(self.meta_file):
            try:
                with open(self.meta_file, "r", encoding="utf-8") as f:
                    saved_model = f.read().strip()
                if saved_model != current_model:
                    logger.warning(
                        f"UYARI: Mevcut embedding modeli '{current_model}', "
                        f"veritabanında kayıtlı modelden '{saved_model}' farklı! "
                        f"Veritabanının yeniden indekslenmesi önerilir."
                    )
            except Exception as e:
                logger.error(f"Meta dosyası okunurken hata: {e}")
        else:
            try:
                with open(self.meta_file, "w", encoding="utf-8") as f:
                    f.write(current_model)
            except Exception as e:
                logger.error(f"Meta dosyası yazılırken hata: {e}")

    def update_meta_model(self):
        """
        Updates the model metadata file to match the current configured model.
        """
        try:
            with open(self.meta_file, "w", encoding="utf-8") as f:
                f.write(settings.EMBED_MODEL)
            logger.info(f"Model meta verisi güncellendi: {settings.EMBED_MODEL}")
        except Exception as e:
            logger.error(f"Meta dosyası güncellenirken hata: {e}")

    def add_documents(self, documents: List[Document]):
        """
        Saves document chunks to the Chroma database.
        
        Args:
            documents: List of LangChain Document objects representing the chunks.
        """
        if documents:
            self.db.add_documents(documents)
            logger.info(f"Vectorstore veritabanına {len(documents)} adet chunk eklendi.")

    def delete_document_chunks(self, filename: str):
        """
        Deletes all document chunks belonging to a specific file from the vector store.
        Uses underlying Chroma collection deletion filter.
        
        Args:
            filename: Base name of the file to remove.
        """
        try:
            self.db._collection.delete(where={"source": filename})
            logger.info(f"'{filename}' dosyasına ait tüm chunk'lar vectorstore'dan temizlendi.")
        except Exception as e:
            logger.error(f"'{filename}' silinirken Chroma hatası oluştu: {e}")

    def similarity_search_with_score(self, query: str, k: int = None) -> List[Tuple[Document, float]]:
        """
        Searches the vector store for similar chunks and returns them with L2 distances.
        
        Args:
            query: The search query string.
            k: The number of documents to retrieve.
            
        Returns:
            List[Tuple[Document, float]]: List of tuples containing Document and distance score.
        """
        k = k or settings.RETRIEVAL_K
        return self.db.similarity_search_with_score(query, k=k)
