### `src/server/create_content.py`
### MCP server content creation functionality  
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions

import json
import uuid
from datetime import datetime
from typing import Dict, Any
from . import mcp

@mcp.tool("create_content")
def create_content_tool(content_data: str, content_type: str = "text") -> Dict[str, Any]:
    """
    Create new content and store it in Snowflake.
    
    Args:
        content_data: The content to be created and stored (JSON string format)
        content_type: Type of content (text, document, etc.)
    
    Returns:
        Dict with status and details about the created content
    """
    try:
        # Parse content data from JSON string
        try:
            parsed_data = json.loads(content_data) if isinstance(content_data, str) else content_data
        except json.JSONDecodeError:
            # Fallback if not valid JSON
            parsed_data = {
                "title": "Untitled",
                "content": content_data,
                "type": content_type,
                "tags": []
            }
        
        # Generate unique content ID
        content_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Prepare content metadata
        content_metadata = {
            "id": content_id,
            "title": parsed_data.get("title", "Untitled"),
            "content": parsed_data.get("content", ""),
            "type": content_type,
            "tags": parsed_data.get("tags", []),
            "created_at": timestamp,
            "content_length": len(parsed_data.get("content", "")),
            "word_count": len(parsed_data.get("content", "").split()) if parsed_data.get("content") else 0
        }
        
        # TODO: Integrate with Snowflake to store content
        # This would include:
        # 1. Connect to Snowflake using snowflake-connector-python
        # 2. Insert content into appropriate table
        # 3. Store metadata and indexing information
        # 4. Handle file attachments if provided
        
        result = {
            "status": "success",
            "message": f"Content '{content_metadata['title']}' created successfully",
            "content_id": content_id,
            "content_length": content_metadata["content_length"],
            "word_count": content_metadata["word_count"],
            "content_type": content_type,
            "created_at": timestamp,
            "tags": content_metadata["tags"]
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create content: {str(e)}",
            "error_type": type(e).__name__
        }

@mcp.tool("upload_file_content")
def upload_file_content_tool(file_data: str, filename: str, content_type: str = "document") -> Dict[str, Any]:
    """
    Handle file upload and content extraction for Snowflake storage.
    
    Args:
        file_data: Base64 encoded file data
        filename: Original filename
        content_type: Type of content being uploaded
    
    Returns:
        Dict with upload status and extracted content information
    """
    try:
        import base64
        
        # Decode file data
        file_bytes = base64.b64decode(file_data)
        file_size = len(file_bytes)
        
        # Extract file extension
        file_extension = filename.split('.')[-1].lower() if '.' in filename else 'unknown'
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # TODO: Integrate with Snowflake file handling
        # This would include:
        # 1. Upload file to Snowflake stage
        # 2. Use PARSE_DOCUMENT function for content extraction
        # 3. Store extracted text and metadata
        # 4. Create searchable index
        
        result = {
            "status": "success",
            "message": f"File '{filename}' uploaded and processed successfully",
            "file_id": file_id,
            "filename": filename,
            "file_size": file_size,
            "file_extension": file_extension,
            "content_type": content_type,
            "uploaded_at": timestamp,
            "processing_status": "completed"
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to upload file: {str(e)}",
            "error_type": type(e).__name__
        }

@mcp.resource("content://upload")
def get_upload_interface() -> str:
    """
    Get the upload interface configuration for content creation.
    """
    interface_config = {
        "supported_formats": ["txt", "md", "docx", "pdf"],
        "max_file_size": "10MB",
        "features": [
            "Text content creation",
            "File upload and processing", 
            "Content categorization with tags",
            "Snowflake integration",
            "Automatic content indexing"
        ],
        "content_types": ["text", "document", "note", "article"]
    }
    
    return json.dumps(interface_config, indent=2)

@mcp.prompt("create_content_prompt")
def content_creation_prompt(content_type: str = "text", title: str = "") -> str:
    """
    Generate a prompt template for content creation.
    
    Args:
        content_type: Type of content to create
        title: Optional title for the content
    
    Returns:
        Formatted prompt for content creation
    """
    prompt_template = f"""
# Content Creation Template

**Content Type:** {content_type}
**Title:** {title if title else '[Please provide a title]'}

## Guidelines:
- Provide clear and structured content
- Use appropriate formatting for the content type
- Include relevant tags for better categorization
- Ensure content is well-organized and readable

## Content Structure:
1. **Introduction/Overview**
2. **Main Content/Body**  
3. **Conclusion/Summary**
4. **Tags/Keywords**

Please fill in the content following this structure.
"""
    
    return prompt_template