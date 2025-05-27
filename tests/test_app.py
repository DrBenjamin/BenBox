import streamlit as st
import importlib
import os
import sys
# Adding the parent directory to sys.path to import app.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importing the app module
app = importlib.import_module('app')

# def test_app_imports():
#     """Test that app.py imports without errors."""
#     assert isinstance(app, types.ModuleType)

def test_session_state_defaults():
    """Test that session state keys are set with default values."""
    # Simulating Streamlit session state
    keys = [
        "answer", "response", "option_offline_resources", "option_embedding_model",
        "option_vector_length", "IS_EMBED"
    ]
    for key in keys:
        assert key in st.session_state

def test_mcp_client_exists():
    """Test that the MCPClient is initialized."""
    assert hasattr(app, '_mcp_client')
    assert app._mcp_client is not None
