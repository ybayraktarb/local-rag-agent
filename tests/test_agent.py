import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document
from src.retrieval.retriever_middleware import RetrieverMiddleware

def test_retriever_middleware_isolated_pass():
    """
    Test RetrieverMiddleware when confidence check passes.
    The query must go to the LLM, and the correct answer and sources must be returned.
    """
    # 1. Mock Vector Store Manager
    mock_vstore = MagicMock()
    # Mock similarity search returning results that pass the confidence gate
    # Cosine distance = 0.2 -> Similarity = 0.80 (>= 0.65 threshold)
    mock_doc = Document(
        page_content="Kredi limiti aylık gelirin en fazla 4 katı olmalıdır.",
        metadata={"source": "politika.pdf", "page": 2}
    )
    mock_vstore.similarity_search_with_score.return_value = [(mock_doc, 0.2)]

    # 2. Mock ChatOllama LLM
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = " Kredi kartı limitinin aylık gelirin en fazla 4 katı olarak belirlenmesi önerilir. "
    mock_llm.invoke.return_value = mock_response

    # 3. Instantiate Middleware and test
    middleware = RetrieverMiddleware(vectorstore_manager=mock_vstore, llm=mock_llm)
    response = middleware.query("Kredi kartı limiti nasıl belirlenir?")

    # 4. Assertions
    assert response["passed_gate"] is True
    assert "en fazla 4 katı" in response["answer"]
    assert response["sources"] == [{"source": "politika.pdf", "page": 2}]
    assert response["confidence_score"] == pytest.approx(0.80)
    
    # Verify LLM was invoked
    mock_llm.invoke.assert_called_once()
    mock_vstore.similarity_search_with_score.assert_called_once_with("Kredi kartı limiti nasıl belirlenir?", k=3)

def test_retriever_middleware_isolated_fail():
    """
    Test RetrieverMiddleware when confidence check fails.
    The query must be blocked at the confidence gate, and LLM must not be called.
    """
    # 1. Mock Vector Store Manager
    mock_vstore = MagicMock()
    # Cosine distance = 0.8 -> Similarity = 0.20 (< 0.65 threshold)
    mock_doc = Document(page_content="Alakasız içerik.", metadata={"source": "alakasiz.pdf", "page": 1})
    mock_vstore.similarity_search_with_score.return_value = [(mock_doc, 0.8)]

    # 2. Mock ChatOllama LLM (should not be called)
    mock_llm = MagicMock()

    # 3. Instantiate Middleware and test
    middleware = RetrieverMiddleware(vectorstore_manager=mock_vstore, llm=mock_llm)
    response = middleware.query("Uzay gemisi yakıtı nedir?")

    # 4. Assertions
    assert response["passed_gate"] is False
    assert response["answer"] == "İlgili dokümanlarda bu konuda yeterli bilgi bulunamadı."
    assert response["sources"] == []
    assert response["confidence_score"] == pytest.approx(0.20)
    
    # Verify LLM was NOT invoked
    mock_llm.invoke.assert_not_called()
    mock_vstore.similarity_search_with_score.assert_called_once_with("Uzay gemisi yakıtı nedir?", k=3)
