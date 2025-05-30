### Test for MinIO MCP tools
### Testing MinIO tool functionality
import json
import sys
import os

# Adding path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


def test_minio_tool_compilation():
    """Test that MinIO MCP tool compiles without syntax errors."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'server', 'minio_tool.py'), 'r') as f:
        code = f.read()
        try:
            compile(code, 'minio_tool.py', 'exec')
            assert True, "MinIO MCP tool compiled successfully"
        except SyntaxError as e:
            assert False, f"Syntax error in MinIO MCP tool: {e}"


def test_minio_tool_functions():
    """Test that all expected MinIO functions are defined in the tool."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'server', 'minio_tool.py'), 'r') as f:
        code = f.read()
        
    # Check that all expected MCP tool functions are defined
    expected_functions = [
        'minio_list_buckets',
        'minio_create_bucket', 
        'minio_list_objects',
        'minio_upload_files',
        'minio_delete_object'
    ]
    
    for func_name in expected_functions:
        assert f"async def {func_name}" in code, f"Function {func_name} not found in MinIO tool"
        # Check for @mcp.tool() decorator before the function
        func_position = code.find(f"async def {func_name}")
        if func_position != -1:
            code_before_func = code[:func_position]
            assert "@mcp.tool()" in code_before_func[-100:], f"Function {func_name} not decorated with @mcp.tool()"


def test_minio_tool_imports():
    """Test that MinIO tool has correct imports."""
    with open(os.path.join(os.path.dirname(__file__), '..', 'src', 'server', 'minio_tool.py'), 'r') as f:
        code = f.read()
        
    # Check for required imports
    assert "from . import mcp" in code, "Missing MCP import"
    assert "from .minio_utils import" in code, "Missing minio_utils import"
    assert "import json" in code, "Missing json import"
    assert "import logging" in code, "Missing logging import"


if __name__ == "__main__":
    test_minio_tool_compilation()
    test_minio_tool_functions()
    test_minio_tool_imports()
    print("All MinIO MCP tool tests passed!")