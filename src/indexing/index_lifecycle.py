import os
import uuid

from src.config import settings
from src.indexing.chunker import DocumentChunker
from src.indexing.document_registry import DocumentRegistry
from src.indexing.vectorstore_manager import VectorStoreManager
from src.loaders.loader_factory import LoaderFactory


def synchronize_index(registry=None, vectorstore=None, progress=None):
    """Apply file-system deltas transactionally from the registry's perspective."""
    registry = registry or DocumentRegistry()
    changes = registry.scan_docs_folder()
    if not any(changes.values()):
        return changes, []
    vectorstore = vectorstore or VectorStoreManager()
    chunker = DocumentChunker()
    failures = []

    for filename in changes["deleted"]:
        try:
            vectorstore.delete_document_chunks(filename)
            registry.remove(filename)
        except Exception:
            failures.append(filename)

    for filename in changes["added"] + changes["modified"]:
        path = os.path.join(settings.DOCS_DIR, filename)
        try:
            if progress:
                progress(filename)
            docs = LoaderFactory.get_loader(path).load()
            chunks = chunker.split_documents(docs)
            if not chunks:
                raise ValueError("PDF içinde indekslenebilir metin bulunamadı")
            generation = uuid.uuid4().hex
            for chunk in chunks:
                chunk.metadata["source"] = filename
                chunk.metadata["index_generation"] = generation
            old_generation = registry.data.get(filename, {}).get("index_generation")
            vectorstore.add_documents(chunks)
            try:
                registry.mark_indexed(filename, path, index_generation=generation)
            except Exception:
                vectorstore.delete_generation(filename, generation)
                raise
            # Registry now exclusively selects the new generation. Cleanup is best-effort.
            try:
                if old_generation:
                    vectorstore.delete_generation(filename, old_generation)
                elif filename in changes["modified"]:
                    # Legacy chunks have no generation and are no longer queryable.
                    vectorstore.db._collection.delete(where={"$and": [
                        {"source": filename}, {"index_generation": {"$ne": generation}}
                    ]})
            except Exception:
                pass
        except Exception:
            failures.append(filename)
    return changes, failures
