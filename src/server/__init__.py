### `src/server/__init__.py`
### MCP server package
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
from mcp.server.fastmcp import FastMCP

# Initializing FastMCP server with prompt capabilities (SSE)
mcp = FastMCP(
    "BenBox",
    capabilities={
        "resources": {
            "subscribe": True,
            "listChanged": True
        },
        "prompts": {
            "listChanged": True
            }
        }
)

# Importing all tool modules to ensure MCP tool registration
from . import get_static_image
from . import get_variable_image
from . import review_code
from . import image_recognition
from . import get_country_name
from . import rag_on_snow
from . import minio
from . import snowflake_utils
