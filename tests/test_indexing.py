import os
import pytest
from langchain_core.documents import Document
from src.config import settings
from src.indexing.chunker import DocumentChunker
from src.indexing.document_registry import DocumentRegistry
from src.indexing.vectorstore_manager import VectorStoreManager

TEST_DOCS_DIR = os.path.join(settings.BASE_DIR, "docs_test")
TEST_DB_DIR = os.path.join(settings.BASE_DIR, "db_test")
TEST_REGISTRY_PATH = os.path.join(TEST_DB_DIR, "test_registry.json")

@pytest.fixture(scope="function")
def clean_test_env():
    """
    Clean up and override test document and database directories.
    """
    import shutil
    # Keep track of original settings
    orig_docs_dir = settings.DOCS_DIR
    orig_db_dir = settings.DB_DIR
    
    # Apply overrides
    settings.DOCS_DIR = TEST_DOCS_DIR
    settings.DB_DIR = TEST_DB_DIR

    # Cleanup any leftovers
    if os.path.exists(TEST_DB_DIR):
        shutil.rmtree(TEST_DB_DIR, ignore_errors=True)
    if os.path.exists(TEST_DOCS_DIR):
        shutil.rmtree(TEST_DOCS_DIR, ignore_errors=True)
        
    os.makedirs(TEST_DB_DIR, exist_ok=True)
    os.makedirs(TEST_DOCS_DIR, exist_ok=True)
    
    yield
    
    # Cleanup after test run
    if os.path.exists(TEST_DB_DIR):
        shutil.rmtree(TEST_DB_DIR, ignore_errors=True)
    if os.path.exists(TEST_DOCS_DIR):
        shutil.rmtree(TEST_DOCS_DIR, ignore_errors=True)
        
    # Restore original settings
    settings.DOCS_DIR = orig_docs_dir
    settings.DB_DIR = orig_db_dir

def test_document_chunker():
    """
    Verify chunker splits documents and respects configuration size.
    """
    chunker = DocumentChunker(chunk_size=100, chunk_overlap=10)
    docs = [
        Document(
            page_content="Bu birinci paragraf. Oldukça uzun bir metin içeriyor.\n\nBu ikinci paragraf. Bu da farklı bir konudan bahsediyor.",
            metadata={"source": "test.pdf"}
        )
    ]
    chunks = chunker.split_documents(docs)
    
    assert len(chunks) >= 2
    for chunk in chunks:
        assert len(chunk.page_content) <= 100
        assert chunk.metadata["source"] == "test.pdf"

def test_document_registry(clean_test_env):
    """
    Verify registry loads, saves, and updates document statuses.
    """
    registry = DocumentRegistry(registry_path=TEST_REGISTRY_PATH)
    
    # Empty scan
    changes = registry.scan_docs_folder()
    assert len(changes["added"]) == 0
    
    # Manual insertion mock
    registry.data["doc1.pdf"] = {
        "filename": "doc1.pdf",
        "hash": "abc123hash",
        "status": "active",
        "added_at": "2026-07-12T00:00:00",
        "updated_at": "2026-07-12T00:00:00"
    }
    registry.save()
    
    # Load registry in a new instance and verify
    new_registry = DocumentRegistry(registry_path=TEST_REGISTRY_PATH)
    assert "doc1.pdf" in new_registry.data
    assert new_registry.data["doc1.pdf"]["hash"] == "abc123hash"
    
    # Verify active status
    active_docs = new_registry.get_active_documents()
    assert "doc1.pdf" in active_docs
    
    # Set passive status and verify
    new_registry.set_status("doc1.pdf", "passive")
    assert new_registry.data["doc1.pdf"]["status"] == "passive"
    assert "doc1.pdf" not in new_registry.get_active_documents()
