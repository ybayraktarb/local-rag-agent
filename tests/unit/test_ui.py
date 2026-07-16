import sys
import pytest
from unittest.mock import MagicMock, patch

def test_ui_imports():
    """
    Verify that all PySide6 window and worker classes can be imported without errors.
    """
    from src.ui.main_window import MainWindow, InitWorker, QueryWorker
    assert MainWindow is not None
    assert InitWorker is not None
    assert QueryWorker is not None

def test_query_worker_run():
    """
    Verify QueryWorker background thread execution behavior with mock objects.
    """
    from src.ui.main_window import QueryWorker
    
    mock_agent = MagicMock()
    mock_agent.query.return_value = {"answer": "Test answer", "sources": []}
    
    worker = QueryWorker(agent=mock_agent, query_text="Test query")
    
    # Mock signals
    worker.finished = MagicMock()
    worker.error_occurred = MagicMock()
    
    # Run the worker synchronously for testing
    worker.run()
    
    mock_agent.query.assert_called_once_with("Test query")
    worker.finished.emit.assert_called_once_with({"answer": "Test answer", "sources": []})
    worker.error_occurred.emit.assert_not_called()
