import os

import pytest
from langchain_ollama import OllamaEmbeddings
from reportlab.pdfgen import canvas

from src.config import settings
from src.agent.agent_builder import AgentBuilder
from src.indexing.document_registry import DocumentRegistry
from src.indexing.index_lifecycle import synchronize_index


pytestmark = pytest.mark.integration


@pytest.mark.skipif(os.getenv("RUN_OLLAMA_INTEGRATION") != "1", reason="Ollama integration is opt-in")
def test_real_ollama_embedding():
    vector = OllamaEmbeddings(model=settings.EMBED_MODEL, base_url=settings.OLLAMA_BASE_URL).embed_query(
        "yerel rag entegrasyon testi"
    )
    assert len(vector) > 0


@pytest.mark.skipif(os.getenv("RUN_OLLAMA_INTEGRATION") != "1", reason="Ollama integration is opt-in")
def test_real_pdf_index_and_sourced_answer(tmp_path, monkeypatch):
    docs = tmp_path / "docs"; docs.mkdir()
    db = tmp_path / "db"; db.mkdir()
    pdf = canvas.Canvas(str(docs / "policy.pdf"))
    pdf.drawString(72, 760, "Kurumun acil durum kodu kesin olarak MAVI-42 kodudur.")
    pdf.save()
    monkeypatch.setattr(settings, "DOCS_DIR", str(docs))
    monkeypatch.setattr(settings, "DB_DIR", str(db))
    monkeypatch.setattr(settings, "CONFIDENCE_THRESHOLD", 0.1)
    registry = DocumentRegistry(str(db / "document_registry.json"))

    _, failures = synchronize_index(registry=registry)
    response = AgentBuilder.build_agent(persist_directory=str(db)).query("Acil durum kodu nedir?")

    assert failures == []
    assert response["success"] is True and response["passed_gate"] is True
    assert response["sources"] and response["sources"][0]["source"] == "policy.pdf"
    assert "MAVI-42" in response["answer"].upper()
