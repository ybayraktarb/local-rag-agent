import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document
from src.retrieval.confidence_gate import check_confidence, get_empty_response
from src.retrieval.retriever_middleware import RetrieverMiddleware
from src.config import settings

def test_confidence_gate_logic(monkeypatch):
    """
    Test confidence gate with simulated cosine distances.
    Cosine distance:
    - 0.2 distance -> 0.80 similarity (passes threshold 0.65)
    - 0.6 distance -> 0.40 similarity (fails threshold 0.65)
    """
    # Configure threshold for test stability
    monkeypatch.setattr(settings, "CONFIDENCE_THRESHOLD", 0.65)

    # 1. High similarity test (cosine distance = 0.2 -> Similarity = 0.80)
    high_sim_results = [
        (Document(page_content="Kredi başvurusu evrakları...", metadata={"source": "kredi.pdf"}), 0.2)
    ]
    passed, docs, score = check_confidence(high_sim_results)
    assert passed is True
    assert len(docs) == 1
    assert score == 0.80
    assert docs[0].page_content == "Kredi başvurusu evrakları..."

    # 2. Low similarity test (cosine distance = 0.6 -> Similarity = 0.40)
    low_sim_results = [
        (Document(page_content="Alakasız metin...", metadata={"source": "alakasiz.pdf"}), 0.6)
    ]
    passed, docs, score = check_confidence(low_sim_results)
    assert passed is False
    assert len(docs) == 0
    assert score == 0.40

    # 3. Empty results test
    passed, docs, score = check_confidence([])
    assert passed is False
    assert len(docs) == 0
    assert score == 0.0
    
    # 4. Fallback message test
    assert get_empty_response() == "İlgili dokümanlarda bu konuda yeterli bilgi bulunamadı."


def test_retrieval_middleware_blocks_llm_call_on_low_confidence(monkeypatch):
    """
    Verifies that when confidence is low, the RetrieverMiddleware blocks the call
    to the LLM completely, asserting that the LLM's invoke method is never called.
    """
    # Configure threshold
    monkeypatch.setattr(settings, "CONFIDENCE_THRESHOLD", 0.65)

    mock_vstore = MagicMock()
    # Cosine distance = 0.9 -> Similarity = 0.10 (< 0.65 threshold)
    mock_doc = Document(page_content="Alakasız veri.", metadata={"source": "test.pdf", "page": 1})
    mock_vstore.similarity_search_with_score.return_value = [(mock_doc, 0.9)]
    
    mock_llm = MagicMock()
    
    middleware = RetrieverMiddleware(vectorstore_manager=mock_vstore, llm=mock_llm)
    response = middleware.query("En sevdiğin film hangisi?")
    
    assert response["passed_gate"] is False
    assert response["answer"] == "İlgili dokümanlarda bu konuda yeterli bilgi bulunamadı."
    assert response["confidence_score"] == pytest.approx(0.10)
    
    # Assert that LLM is never invoked
    mock_llm.invoke.assert_not_called()


def test_retrieval_and_llm_failures_have_distinct_gate_and_success_flags():
    failed_store = MagicMock()
    failed_store.similarity_search_with_score.side_effect = RuntimeError("offline")
    response = RetrieverMiddleware(failed_store, llm=MagicMock()).query("soru")
    assert response["passed_gate"] is False and response["success"] is False

    doc = Document(page_content="Politika bağlamı", metadata={"source": "policy.pdf", "page": 4})
    good_store = MagicMock()
    good_store.similarity_search_with_score.return_value = [(doc, 0.1)]
    failed_llm = MagicMock(); failed_llm.invoke.side_effect = RuntimeError("offline")
    response = RetrieverMiddleware(good_store, llm=failed_llm).query("soru")
    assert response["passed_gate"] is True and response["success"] is False


def test_prompt_contains_only_retrieved_context():
    doc = Document(page_content="ONAYLI BAĞLAM", metadata={"source": "policy.pdf", "page": 2})
    store = MagicMock(); store.similarity_search_with_score.return_value = [(doc, 0.1)]
    llm = MagicMock(); llm.invoke.return_value.content = "yanıt"
    RetrieverMiddleware(store, llm=llm).query("kullanıcı sorusu")
    prompt = str(llm.invoke.call_args.args[0])
    assert "ONAYLI BAĞLAM" in prompt and "kullanıcı sorusu" in prompt
