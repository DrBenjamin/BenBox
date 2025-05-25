# Copilot Instructions for BenBox

Dearest Copilot,
this project is an Agent AI app utilizing
MCP (Model Context Protocol) tools. A full description of the project
you will find here [PROJECT.md](#file:PROJECT.md).

The agent system uses the approaches from:

- [Agents Using Azure AI Foundry](https://github.com/Azure-Samples/get-started-with-ai-agents)
- [Agent Development Kit](https://google.github.io/adk-docs/)
- [A Practical Guide to Building Agents](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)

**The backend:**

A Streamlit app that serves as a client to
the MCP server tools. It has an inbuild RAG (retrieval-augmented generation)
system to store and retrieve documents as vectors for similarity search.

**The frontend is a two-part system:**

1. An Angular mobile app is also included which utilizes the Streamlit client
application (as iframe embedded) and collects app metrics.

2. A desktop app which manages the files and works with Cloud blob storage.
It can be run locally or in the cloud.

**DevOps/DataOps:**

The project includes DevOps and DataOps tools for
- Docker: [docker-compose.yml](#file:docker-compose.yml), [Dockerfile](#file:Dockerfile), [Dockerfile_Streamlit](#file:Dockerfile_Streamlit), 
  [Dockerfile_MCP](#file:Dockerfile_MCP)
- Jenkins: [Jenkinsfile](#file:Jenkinsfile)
- Pytest: [tests/test_app.py](#file:tests/test_app.py)
- dbt: [dbt_project.yml](#file:dbt_project.yml)

When generating code snippets or explanations, please follow these guidelines:

1. Output always in Markdown.
2. When referring to a file in this repo, link using `#file:<relative_path>`.
   - Angular mobile app: [src/app/app.components.ts](#file:src/app/app.components.ts)
   - Phoenix desktop app: [BenBox.py](#file:BenBox.py)
   - Streamlit client app: [app.py](#file:app.py)
   - MCPClient class: [src/client.py](#file:src/client.py)
   - MCP server [src/server.py](#file:src/server.py)
   - MCP server tools: [src/server/*](#file:src/server/*)
   - Assets folder: [src/assets/*](#file:src/assets/*)
3. Code‑block format for changes or new files:
   ````python
   // filepath: #file:<relative_path>
   # ...existing code...
   def my_new_function(...):
       ...
   # ...existing code...
   ````
4. Comments format:
   - Use `#` for comments
   - Start comments with 'Setting', 'Creating', 'Adding', 'Updating' etc.
     (always the gerund form) and before it add an empty line if not the
     beginning of a code block or function.
5. Adhere to PEP 8:
   - 4‑space indentation, snake_case names
   - Imports at the top of the file
   - Docstrings in Google or NumPy style
6. Preserve existing patterns:
   - Use `@st.cache_resource` for expensive initializations
   - Store and retrieve state via `st.session_state.get("key", default)`
7. File I/O:
   - Use `os.path.join(...)` and `os.makedirs(..., exist_ok=True)`
   - Handle missing directories before writing files
8. Error handling & logging:
   - Import and configure `logger = logging.getLogger(__name__)`
   - Raise clear exceptions on invalid inputs
9. Testing:
   - Add or update tests under `tests/`
   - Use `pytest` fixtures to mock `st.session_state`
