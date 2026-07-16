from pathlib import Path
from unittest.mock import MagicMock

from src.config import settings
from src.indexing.document_registry import DocumentRegistry
from src.indexing.index_lifecycle import synchronize_index
from langchain_core.documents import Document


class FakeLoader:
    def load(self):
        return [Document(page_content="yeterince uzun örnek içerik", metadata={"page": 1})]


def test_failed_index_does_not_commit_registry(tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    db = tmp_path / "db"; db.mkdir()
    (docs / "broken.pdf").write_bytes(b"not a pdf")
    monkeypatch.setattr(settings, "DOCS_DIR", str(docs))
    registry = DocumentRegistry(str(db / "registry.json"))
    store = MagicMock()

    _, failures = synchronize_index(registry=registry, vectorstore=store)

    assert failures == ["broken.pdf"]
    assert registry.data == {}
    store.add_documents.assert_not_called()


def test_deleted_document_is_removed_after_vector_cleanup(tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    db = tmp_path / "db"; db.mkdir()
    monkeypatch.setattr(settings, "DOCS_DIR", str(docs))
    registry = DocumentRegistry(str(db / "registry.json"))
    registry.data["gone.pdf"] = {"filename": "gone.pdf", "hash": "abc", "status": "active"}
    registry.save()
    store = MagicMock()

    _, failures = synchronize_index(registry=registry, vectorstore=store)

    assert failures == []
    store.delete_document_chunks.assert_called_once_with("gone.pdf")
    assert "gone.pdf" not in registry.data


def test_noop_audit_needs_no_key(monkeypatch):
    from src.audit import NoOpAuditLogger, create_audit_logger
    monkeypatch.setattr(settings, "AUDIT_ENABLED", False)
    monkeypatch.setattr(settings, "AUDIT_DB_KEY", "")
    assert isinstance(create_audit_logger(), NoOpAuditLogger)


def test_modified_document_switches_generation_before_cleanup(tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    db = tmp_path / "db"; db.mkdir()
    path = docs / "policy.pdf"; path.write_bytes(b"new")
    monkeypatch.setattr(settings, "DOCS_DIR", str(docs))
    monkeypatch.setattr("src.indexing.index_lifecycle.LoaderFactory.get_loader", lambda _: FakeLoader())
    registry = DocumentRegistry(str(db / "registry.json"))
    registry.data["policy.pdf"] = {"filename": "policy.pdf", "hash": "old", "status": "active",
                                   "index_generation": "old-generation"}
    registry.save()
    store = MagicMock()

    _, failures = synchronize_index(registry=registry, vectorstore=store)

    assert failures == []
    generation = registry.data["policy.pdf"]["index_generation"]
    assert generation != "old-generation"
    added = store.add_documents.call_args.args[0]
    assert {chunk.metadata["index_generation"] for chunk in added} == {generation}
    store.delete_generation.assert_called_once_with("policy.pdf", "old-generation")
    assert [call[0] for call in store.method_calls].index("add_documents") < [
        call[0] for call in store.method_calls
    ].index("delete_generation")


def test_registry_commit_failure_rolls_back_new_generation(tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    db = tmp_path / "db"; db.mkdir()
    (docs / "policy.pdf").write_bytes(b"new")
    monkeypatch.setattr(settings, "DOCS_DIR", str(docs))
    monkeypatch.setattr("src.indexing.index_lifecycle.LoaderFactory.get_loader", lambda _: FakeLoader())
    registry = DocumentRegistry(str(db / "registry.json"))
    old = {"filename": "policy.pdf", "hash": "old", "status": "active", "index_generation": "old"}
    registry.data["policy.pdf"] = old.copy()
    store = MagicMock()
    monkeypatch.setattr(registry, "save", MagicMock(side_effect=OSError("disk full")))

    _, failures = synchronize_index(registry=registry, vectorstore=store)

    assert failures == ["policy.pdf"]
    assert registry.data["policy.pdf"] == old
    new_generation = store.add_documents.call_args.args[0][0].metadata["index_generation"]
    store.delete_generation.assert_called_once_with("policy.pdf", new_generation)


def test_legacy_registry_is_readable_and_migrated(tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    db = tmp_path / "db"; db.mkdir()
    path = docs / "legacy.pdf"; path.write_bytes(b"changed")
    monkeypatch.setattr(settings, "DOCS_DIR", str(docs))
    monkeypatch.setattr("src.indexing.index_lifecycle.LoaderFactory.get_loader", lambda _: FakeLoader())
    registry = DocumentRegistry(str(db / "registry.json"))
    registry.data["legacy.pdf"] = {"filename": "legacy.pdf", "hash": "old", "status": "active"}
    assert registry.get_active_indexes() == [{"source": "legacy.pdf", "index_generation": None}]
    store = MagicMock(); store.db._collection = MagicMock()

    synchronize_index(registry=registry, vectorstore=store)

    assert registry.data["legacy.pdf"]["index_generation"]
