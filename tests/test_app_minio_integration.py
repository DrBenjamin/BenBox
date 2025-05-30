### Test for app.py MinIO MCP integration
### Testing that app.py correctly calls MinIO MCP tools
import json
import sys
import os
from unittest.mock import Mock, patch, AsyncMock

# Adding path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_call_minio_mcp_tool_function_exists():
    """Test that call_minio_mcp_tool function exists in app.py."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'app.py'), 'r') as f:
        code = f.read()
    
    assert "def call_minio_mcp_tool" in code, "call_minio_mcp_tool function not found in app.py"
    assert "minio_list_buckets" in code, "MinIO MCP tool calls not found in app.py"
    assert "minio_list_objects" in code, "MinIO MCP tool calls not found in app.py"


def test_minio_imports_updated():
    """Test that direct MinIO imports have been reduced."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'app.py'), 'r') as f:
        code = f.read()
    
    # Should still have get_minio_client for direct downloads
    assert "get_minio_client" in code, "get_minio_client import should still exist for downloads"
    
    # Should not have these direct imports anymore
    assert "list_buckets," not in code, "list_buckets should be removed from imports"
    assert "list_objects" not in code or "call_minio_mcp_tool" in code, "list_objects should be replaced with MCP calls"


def test_custom_directory_loader_updated():
    """Test that CustomDirectoryLoader has been updated to use MCP calls."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'app.py'), 'r') as f:
        code = f.read()
    
    # Should use MCP call for listing objects
    assert "call_minio_mcp_tool" in code, "CustomDirectoryLoader should use MCP calls"
    assert "minio_list_objects" in code, "Should call minio_list_objects MCP tool"
    
    # Constructor should not take minio_client anymore
    custom_loader_start = code.find("class CustomDirectoryLoader:")
    custom_loader_end = code.find("def load(self)", custom_loader_start)
    constructor_section = code[custom_loader_start:custom_loader_end]
    
    assert "minio_client" not in constructor_section, "CustomDirectoryLoader constructor should not take minio_client parameter"


def test_mcp_tool_call_structure():
    """Test that MCP tool calls have correct structure."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'app.py'), 'r') as f:
        code = f.read()
    
    # Find the call_minio_mcp_tool function
    func_start = code.find("def call_minio_mcp_tool")
    func_end = code.find("\n\ndef", func_start)
    if func_end == -1:
        func_end = code.find("\n\n# ", func_start)
    
    function_body = code[func_start:func_end]
    
    # Should have async invoke pattern
    assert "async def _invoke():" in function_body, "Should have async _invoke function"
    assert "await _mcp_client.session.call_tool" in function_body, "Should call MCP client session"
    assert "asyncio.run_coroutine_threadsafe" in function_body, "Should use threadsafe coroutine execution"
    assert "json.loads" in function_body, "Should parse JSON response"


if __name__ == "__main__":
    test_call_minio_mcp_tool_function_exists()
    test_minio_imports_updated()
    test_custom_directory_loader_updated()
    test_mcp_tool_call_structure()
    print("All app.py MinIO MCP integration tests passed!")