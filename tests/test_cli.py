import pytest
from unittest.mock import MagicMock, patch
from src.cli.main import bootstrap_system

@patch("src.cli.main.DocumentRegistry")
@patch("src.cli.main.VectorStoreManager")
@patch("src.cli.main.AgentBuilder")
def test_bootstrap_system(mock_agent_builder, mock_vstore_manager, mock_registry):
    """
    Verifies that the CLI bootstrap process correctly calls registry scans and agent builds.
    """
    # Setup mock registry return values (no new changes)
    mock_reg_instance = MagicMock()
    mock_reg_instance.scan_docs_folder.return_value = {
        "added": [], "modified": [], "deleted": []
    }
    mock_registry.return_value = mock_reg_instance
    
    # Setup mock AgentBuilder
    mock_agent = MagicMock()
    mock_agent_builder.build_agent.return_value = mock_agent
    
    # Call bootstrap
    agent = bootstrap_system()
    
    # Assertions
    assert agent == mock_agent
    mock_reg_instance.scan_docs_folder.assert_called_once()
    mock_agent_builder.build_agent.assert_called_once()
