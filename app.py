### `app.py`
### Streamlit MCP client app
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
import streamlit as st
import base64
import threading
import asyncio
import io
import logging
import sys
import time
import os
import requests
import io
import json
import fnmatch
import logging
import warnings
import asyncio
from typing import List, Union
from PIL import Image
from src.client import MCPClient
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from langchain_core.documents import Document
from langchain_community.chat_message_histories import StreamlitChatMessageHistory
from langchain_community.document_loaders import Docx2txtLoader, CSVLoader, PyPDFLoader, TextLoader, WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
from src.server.minio_utils import (
    list_buckets,
    get_minio_client,
    list_objects
)
from src.server.snowrag.snowrag import _reset_vector_store

logging.basicConfig(stream=sys.stdout, level=logging.WARNING)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings(
    action='ignore',
    category=UserWarning,
    module='snowflake.connector'
)


# Setting the page config
st.set_page_config(
    page_title="BenBox",
    page_icon=":robot:",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Retrieving query parameters from the URL
raw_query_list = st.query_params.get_all("query")
try:
    st.session_state.query = [
                                int(q) 
                                for q in raw_query_list
                            ][0]
except:
    st.session_state.query = 0


# Setting session states
if "answer" not in st.session_state:
    st.session_state.answer = None
if "response" not in st.session_state:
    st.session_state.response = None
if "offline_resources" not in st.session_state:
    st.session_state.option_offline_resources = os.path.abspath(
        os.path.join(os.getcwd(), '..'))
if "embedding_model" not in st.session_state:
    st.session_state.option_embedding_model = "multilingual-e5-large"
if "vector_length" not in st.session_state:
    st.session_state.option_vector_length = 1024
    # Detecting iframe embedding using JS and/or 'embed' query parameter (legacy API)
if "IS_EMBED" not in st.session_state:
    try:
        st.session_state["IS_EMBED"] = bool(st.query_params.get_all("angular")[0].lower() == "true")
    except Exception as e:
        st.session_state["IS_EMBED"] = False


# Initializing a single global MCPClient and connect
_mcp_client = MCPClient()

# Setting MCP tool endpoint to the provided URL
mcp_base_url = st.secrets["MCP"]["MCP_URL"]
sse_url = f"{mcp_base_url}/sse"

# Creating persistent event loop for MCP client
_mcp_loop = asyncio.new_event_loop()


# Function to suppress async errors
def _suppress_async_errors(loop, context):
    msg = context.get("message", "")
    if "aclose(): asynchronous generator is already running" in msg or \
       "Attempted to exit cancel scope" in msg:
        return
    loop.default_exception_handler(context)


_mcp_loop.set_exception_handler(_suppress_async_errors)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("anyio").setLevel(logging.ERROR)
threading.Thread(target=_mcp_loop.run_forever, daemon=True).start()

# Connecting to SSE server on persistent loop and waiting for connection
connect_future = asyncio.run_coroutine_threadsafe(
    _mcp_client.connect_to_sse_server(server_url=sse_url),
    _mcp_loop
)
try:
    # Blocking until the MCP client session is ready
    connect_future.result(timeout=10000)
except Exception as e:
    st.error(f"Failed to connect to MCP server: {e}")


# Function to call the MCP tool
def call_mcp_tool_image_recognition(tool_input: Union[str, bytes]) -> tuple[str, bytes]:
    """Sending input to MCP via the SSE-backed session and return the description and raw image bytes."""

    # Accepting only image data here
    if isinstance(tool_input, str):
        raise RuntimeError("MCP image_recognition tool expects image bytes, received text input.")

    # Encoding binary input as base64 string for JSON serialization
    if isinstance(tool_input, (bytes, bytearray)):
        payload = base64.b64encode(tool_input).decode("utf-8")
    else:
        payload = tool_input
    async def _invoke():
        print(f"Calling MCP tool with input...")

        # Using correct parameter name matching server-side image_recognition signature
        result = await _mcp_client.session.call_tool(
            "image_recognition", {"image_bytes": payload}
        )
        print(f"Received MCP tool result!")
        return result

    # Scheduling invocation on persistent loop
    execution = asyncio.run_coroutine_threadsafe(_invoke(), _mcp_loop).result()

    # Extracting JSON text from the first TextContent in the response
    content = execution.content
    text_obj = content[0]
    json_str = getattr(text_obj, 'text', text_obj)
    parsed = json.loads(json_str)
    description = parsed.get('description', '')
    image_bytes_b64 = parsed.get('image_bytes', '')
    raw = base64.b64decode(image_bytes_b64) if isinstance(
        image_bytes_b64, str) else image_bytes_b64
    return description, raw


def call_mcp_generic(input: str, params: dict={}) -> str:
    """Calling an MCP resource or prompt by name with given parameters and return its text output."""
    async def _invoke():
        # Using `read_resource` for URIs with scheme and `get_prompt` for prompts
        if "Static image file" in input:
            result = await _mcp_client.session.read_resource("resource://Image.png")
        elif "Variable image file" in input:
            uri = f"resource://{params.get('image', '')}"
            result = await _mcp_client.session.read_resource(uri)
        else:
            result = await _mcp_client.session.get_prompt(input, params)
        return result
    execution = asyncio.run_coroutine_threadsafe(_invoke(), _mcp_loop).result()

    # Handling prompt results which have .messages instead of .content
    if hasattr(execution, "messages"):
        msgs = execution.messages
        if msgs and isinstance(msgs[0], dict):
            return msgs[0].get("content", "")
        first_msg = msgs[0]
        return getattr(first_msg, "text", str(first_msg))

    # Handling resource reads returning sequence of contents or ResourceReadResult
    contents = execution
    if hasattr(execution, "contents"):
        contents = execution.contents
    if isinstance(contents, (list, tuple)) and contents:
        first = contents[0]
        return getattr(first, "text", getattr(first, "contents", str(first)))

    # Fallback to string representation
    return str(execution)


def call_snowflake_mcp_tool(tool_name: str, params: dict = {}) -> dict:
    """Calling the Snowflake MCP tool and parsing the JSON response."""
    async def _invoke():
        result = await _mcp_client.session.call_tool(tool_name, params)
        return result
    
    try:
        execution = asyncio.run_coroutine_threadsafe(_invoke(), _mcp_loop).result()
        content = execution.content
        
        # Extract JSON from the first TextContent in the response
        if isinstance(content, (list, tuple)) and len(content) > 0:
            text_obj = content[0]
            json_str = getattr(text_obj, 'text', text_obj)
            return json.loads(json_str)
        
        return json.loads(str(content))
    except Exception as e:
        logging.error(f"Error calling Snowflake MCP tool {tool_name}: {e}")
        return {
            "status": "error", 
            "message": f"Fehler beim Aufrufen des Snowflake MCP Tools {tool_name}: {str(e)}"
        }


# Function to list all files one level up and open them
def show_open_file_button(filename, source, idx):
    # Using the MinIO or Snwoflake stage URL as the download source
    url = source
    key = f"minio-download-{filename}-{idx}"
    if url:
        if st.session_state["IS_EMBED"]:
            # Creating a direct download link for iOS/iframe users
            st.markdown(
                f'<a href="{url}" download="{filename}" target="_blank" rel="noopener" style="font-weight:bold;">'
                f'📥 Datei {filename} herunterladen</a>',
                unsafe_allow_html=True
            )
        else:
            try:
                # Downloading the file into an in-memory buffer (desktop/normal browser)
                response = requests.get(url, verify=False)
                response.raise_for_status()
                buffer = io.BytesIO(response.content)
                st.download_button(
                    label=f"📥 Datei {filename} herunterladen",
                    data=buffer,
                    file_name=filename,
                    mime=None,
                    key=key
                )
            except Exception as e:
                st.write(f"Datei: {filename}")
        return True
    return False


# Function to ensure the output key chain
def ensure_output_key_chain(result):
    """
    Ensures the chain output has an 'output' key for LangChain callbacks.
    """
    if isinstance(result, dict):
        if "output" not in result:
            # Patch: copy 'answer' to 'output' if present
            if "answer" in result:
                result["output"] = result["answer"]
            else:
                # Fallback: use first string value
                for v in result.values():
                    if isinstance(v, str):
                        result["output"] = v
                        break
    return result


# Showing menu just if not angular
if not st.session_state["IS_EMBED"]:
    func_choice = st.selectbox(
        "Select MCP function",
        (
            "🌍 Country code Lookup",
            "🌌 Static Image",
            "🏞️ Variable Image",
            "💻 Review Code",
            "🩻 Image Recognition",
            "❄️ Navigator",
            "🤖 OpenAI Agents",
            "🕹️ BenBox"
        ),
        index=st.session_state.query if st.session_state.query else 0,
    )
else:
    if st.session_state.query == 0:
        func_choice = "🌍 Country code Lookup"
    elif st.session_state.query == 1:
        func_choice = "🌌 Static Image"
    elif st.session_state.query == 2:
        func_choice = "🏞️ Variable Image"
    elif st.session_state.query == 3    :
        func_choice = "💻 Review Code"
    elif st.session_state.query == 4:
        func_choice = "🩻 Image Recognition"
    elif st.session_state.query == 5:
        func_choice = "❄️ Navigator"
    elif st.session_state.query == 6:
        func_choice = "🤖 OpenAI Agents"
    elif st.session_state.query == 7:
        func_choice = "🕹️ BenBox"
    else:
        func_choice = "🤖 OpenAI Agents"


if func_choice == "🌍 Country code Lookup":
    if not st.session_state["IS_EMBED"]:
        st.title("🌍 Country code Lookup")
    with st.form("country_code_form"):
        country_code = st.text_input("Country Code")
        submitted = st.form_submit_button("Lookup Country Code")
    if submitted:
        if not country_code:
            st.warning("Please enter a country code.")
        else:
            with st.spinner("Looking up country code via MCP..."):
                async def _invoke():
                    result = await _mcp_client.session.call_tool(
                        "get_country_name",
                        {"country_code": country_code}
                    )
                    return result
                try:
                    execution = asyncio.run_coroutine_threadsafe(_invoke(), _mcp_loop).result()
                    content = execution.content

                    # Handling both TextContent and plain string
                    if isinstance(content, (list, tuple)) and content:
                        country_name = getattr(content[0], 'text', content[0])
                        st.success(f"Der Ländername für den Ländercode '{country_code}' ist **{country_name}**.")
                    else:
                        st.warning(f"Kein Ländername für den Ländercode '{country_code}' gefunden.")
                except Exception as e:
                    st.error(f"Lookup failed: {e}")

elif func_choice == "🌌 Static Image":
    if not st.session_state["IS_EMBED"]:
        st.title("🌌 Static Image")
    if st.button("Fetch Image"):
        with st.spinner("Fetching image from MCP..."):
            response = call_mcp_generic("Static image file")

        # Parsing data URL and decode base64 to bytes, then display
        try:
            parts = response.split(",", 1)
            b64 = parts[1] if len(parts) > 1 else parts[0]
            raw_bytes = base64.b64decode(b64)
            img = Image.open(io.BytesIO(raw_bytes))
            st.image(img, caption="Image.png", use_container_width=True)
        except Exception as e:
            st.error(f"Failed to display image: {e}")

elif func_choice == "🏞️ Variable Image":
    if not st.session_state["IS_EMBED"]:
        st.title("🏞️ Variable Image")
    image_name = st.text_input("Enter image name", value="Image.png")
    if st.button("Fetch Variable Image"):
        with st.spinner("Fetching image from MCP..."):
            response = call_mcp_generic("Variable image file", {"image": image_name})

        # Parsing data URL and decode base64 to bytes, then display
        try:
            parts = response.split(",", 1)
            b64 = parts[1] if len(parts) > 1 else parts[0]
            raw_bytes = base64.b64decode(b64)
            img = Image.open(io.BytesIO(raw_bytes))
            st.image(img, caption=image_name, use_container_width=True)
        except Exception as e:
            st.error(f"Failed to display image: {e}")

elif func_choice == "💻 Review Code":
    if not st.session_state["IS_EMBED"]:
        st.title("💻 Review Code")
    code_input = st.text_area("Enter code to review")
    if st.button("Review"):
        with st.spinner("Reviewing code via MCP..."):
            feedback = call_mcp_generic("review_code", {"code": code_input})
        st.write("**Review Feedback:**")
        st.code(feedback)

elif func_choice == "🩻 Image Recognition":
    if not st.session_state["IS_EMBED"]:
        st.title("🩻 Image Recognition")
    uploaded = st.file_uploader(
        "Upload an image to thumbnail", type=["png", "jpg", "jpeg"]
    )
    if uploaded:
        img_bytes = uploaded.read()
        with st.spinner("Waiting for MCP tool response..."):
            description, raw_bytes = call_mcp_tool_image_recognition(img_bytes)
        st.write(f"**Beschreibung:** {description}")
        thumb = Image.open(io.BytesIO(raw_bytes))
        st.image(thumb, caption="Thumbnail", use_container_width=True)

elif func_choice == "❄️ Navigator":
    # Creating the Snowflake session via MCP tool
    if st.secrets["SNOWFLAKE"].lower() == "true":
        snowflake_session_response = call_snowflake_mcp_tool("snowflake_create_session")
        if snowflake_session_response.get("status") != "success":
            st.error(f"Fehler bei der Verbindung zu Snowflake: {snowflake_session_response.get('message')}")

    # Adding sidebar for options
    with st.sidebar:
        st.title("Optionen")
        st.write("Wähle die Parameter aus.")

        # Getting tables via MCP tool
        tables_response = call_snowflake_mcp_tool("snowflake_list_tables")
        if tables_response.get("status") == "success":
            raw_tables = [table["name"] for table in tables_response.get("tables", [])]
            display_names = [table["display_name"] for table in tables_response.get("tables", [])]
            name_map = dict(zip(display_names, raw_tables))
        else:
            st.error(f"Fehler beim Abrufen der Tabellen: {tables_response.get('message')}")
            raw_tables = []
            display_names = []
            name_map = {}
            
        options = ["Erstelle neue Tabelle"] + \
            display_names + ["Multi-Table-Selektion"]

        # Getting bucket list from query params (comma-separated)
        bucket_raw = st.query_params.get_all("bucket")
        if bucket_raw:
            bucket_list = [b.strip().upper() for b in bucket_raw[0].split(",") if b.strip()]
        else:
            bucket_list = []

        # Updating: mapping string bucket param to index in options
        if len(bucket_list) > 1:
            selected_index = options.index("Multi-Table-Selektion")
        else:
            bucket_param = bucket_list[0] if bucket_list else None
            if bucket_param and bucket_param in options:
                selected_index = options.index(bucket_param)
            else:
                selected_index = 1

        # Adding a selectbox for the user to select the table
        selected_disp = st.selectbox(
            "Wähle die Tabelle(n)",
            options,
            index=selected_index,
            key="selected_table",
            on_change=_reset_vector_store
        )

        # Adding db table drop function it not "Erstelle neue Tabelle" or "Multi-Table-Selektion"
        if selected_disp not in ["Erstelle neue Tabelle", "Multi-Table-Selektion"]:
            # Adding a button to drop the table
            if st.button("Tabelle löschen", key="drop_table"):
                db_table_name = name_map[selected_disp]
                # Dropping table via MCP tool
                drop_response = call_snowflake_mcp_tool(
                    "snowflake_drop_table", 
                    {"table_name": db_table_name}
                )
                if drop_response.get("status") == "success":
                    st.success(f"Tabelle {db_table_name} wurde gelöscht!")
                    st.toast(f"Tabelle {db_table_name} wurde gelöscht!", icon="✅")
                    if "vector" in st.session_state:
                        del st.session_state["vector"]
                    time.sleep(3)
                    st.rerun()
                else:
                    st.error(f"Fehler beim Löschen der Tabelle: {drop_response.get('message')}")
                    
        if selected_disp == "Erstelle neue Tabelle":
            try:
                default_table_name = st.query_params.get_all("bucket")[0].upper()
            except:
                default_table_name = "TEST"
            new_disp = st.text_input(
                "Tabellenname", value=default_table_name, on_change=_reset_vector_store)
            st.session_state.option_embedding_model = st.selectbox(
                "Wähle das Embedding-Modell", options=st.secrets["snowflake"]["embedding_models"],
                index=0, key="embedding_model"
            )
            st.session_state.option_vector_length = st.selectbox(
                "Wähle die Vektorenlänge", [768, 1024], index=1, key="vector_length", disabled=True)
            if new_disp:
                # Setting table name to all uppercase and prefixing with LANGCHAIN_ if not present
                table_name = new_disp.upper()
                if not table_name.startswith("LANGCHAIN_"):
                    table_name = f"LANGCHAIN_{table_name}"
            else:
                table_name = "LANGCHAIN_TEST"
        else:
            if selected_disp == "Multi-Table-Selektion":
                # Creating a list of valid defaults that exist in display_names
                defaults = [b for b in bucket_list if b in display_names] if bucket_list else None

                # Ensuring defaults is None if empty, to avoid Streamlit error
                if defaults and len(defaults) > 0:
                    default_multiselect = defaults
                else:
                    default_multiselect = None

                table_display_selection = st.multiselect(
                    "Wähle mindestens 2 Tabellen",
                    options=display_names,
                    default=default_multiselect,
                    key="multi_table_selection",
                    on_change=_reset_vector_store
                )
                if len(table_display_selection) < 2:
                    st.warning(
                        "Bitte wähle mindestens 2 Tabellen für die Multi-Table-Selektion.")
                    table_name = []
                else:
                    table_name = [name_map[n] for n in table_display_selection]
            else:
                table_name = name_map[selected_disp]
        st.session_state.option_table = table_name

        # Adding selectboxes for the user to select the LLM parameters
        if selected_disp != "Erstelle neue Tabelle":
            st.session_state.option_model = st.selectbox(
                "Wähle ein Sprachmodell", options=st.secrets["snowflake"]["models"],
                index=0, key="model"
            )

            # Setting system and assistant prompt
            system = st.text_input("System Instruktion", value=st.secrets["LLM"]["LLM_SYSTEM"], max_chars=500)
            system += st.text_input("System Instruktion+", value=f" {st.secrets['LLM']['LLM_SYSTEM_PLUS']}", max_chars=500)
            assistant = st.text_input("Assistant Instruktion", value=st.secrets["LLM"]["LLM_ASSISTANT"], max_chars=500)

        # Adding chat import feature to sidebar (only if chat history is empty)
        msgs_tmp = st.session_state.get("langchain_messages", None)
        msgs_empty = not msgs_tmp or not getattr(msgs_tmp, "messages", [])
        if msgs_empty:
            uploaded_chat = st.file_uploader("Importiere Chat-JSON", type=["json"], key="chat_json_import")
            if uploaded_chat is not None:
                try:
                    # Loading and parsing the uploaded JSON
                    chat_data = json.load(uploaded_chat)

                    # Creating or resetting the message history
                    msgs = StreamlitChatMessageHistory(key="langchain_messages")
                    msgs.clear()

                    # Adding messages from the imported JSON
                    for msg in chat_data:
                        msg_type = msg.get("type")
                        content = msg.get("content", "")
                        if msg_type == "ai":
                            msgs.add_ai_message(content)
                        elif msg_type == "human":
                            msgs.add_user_message(content)
                    st.toast("Chatverlauf importiert! Die Unterhaltung kann fortgesetzt werden.")
                except Exception as e:
                    st.error(f"Fehler beim Importieren des Chatverlaufs: {e}")

    # Showing the title
    if not st.session_state["IS_EMBED"]:
        st.title(st.secrets["LLM"]["LLM_CHATBOT_NAME"])

    # Creating form for user input for new table
    if selected_disp == "Erstelle neue Tabelle":
        with st.form("vector_form"):
            # Creating the MinIO client
            minio_client = get_minio_client()
            try:
                options_offline_resources = list_buckets(minio_client)
            except Exception as e:
                st.warning(f"Fehler beim Laden der MinIO Buckets: {e}")
                options_offline_resources = []

            # Creating a mapping from display name to bucket name
            bucket_display_to_real = {
                display.upper(): display.lower().replace(' ', '-')
                for display in options_offline_resources
            }

            # Adding a selectbox for the user to select the MinIO bucket (display name, UPPER)
            selected_bucket_display = st.selectbox(
                "Dokumente", [
                    d.upper()
                    for d in options_offline_resources
                ]
            )
            # Setting the actual bucket name in session state (MinIO-compliant)
            st.session_state.option_offline_resources = bucket_display_to_real.get(selected_bucket_display, selected_bucket_display)

            # Adding a text input for the user to enter the URLs
            st.session_state.online_resources = st.text_area("URLs", disabled=True)

            # Adding the documents and a text input for the user to enter URLs
            if selected_disp == "Erstelle neue Tabelle":
                rag_perform_text = "Neue Inhalte integrieren"
            else:
                rag_perform_text = "Bestehende Inhalte verbinden"
            rag_perform = st.form_submit_button(rag_perform_text)
            if rag_perform:
                with st.spinner("Dokumente werden verarbeitet..."):
                    if "vector" not in st.session_state:
                        class CustomDirectoryLoader:
                            def __init__(self, urls, bucket_name: str, minio_client, glob_pattern: str = "*.*"):
                                """
                                Initialize the loader with a MinIO bucket and a glob pattern.
                                :param bucket_name: Name of the MinIO bucket.
                                :param minio_client: MinIO client instance.
                                :param glob_pattern: Glob pattern to match files within the bucket.
                                """
                                self.urls = urls
                                self.bucket_name = bucket_name
                                self.minio_client = minio_client
                                self.glob_pattern = glob_pattern

                            def load(self) -> List[Document]:
                                """
                                Load all files matching the glob pattern in the MinIO bucket.
                                :return: List of Document objects loaded from the files.
                                """
                                import tempfile
                                documents = []
                                patterns = self.glob_pattern.split('|')

                                # Listing objects in the selected MinIO bucket
                                st.markdown("**Dokumente**")
                                object_names = list_objects(self.minio_client, self.bucket_name)
                                if not object_names:
                                    st.warning("Keine Dateien im MinIO-Bucket gefunden.")
                                    return documents

                                with tempfile.TemporaryDirectory() as tmpdir:
                                    for object_name in object_names:
                                        for pattern in patterns:
                                            if fnmatch.fnmatch(object_name, pattern):
                                                # Downloading the file from MinIO to a temp file
                                                local_path = os.path.join(tmpdir, os.path.basename(object_name))
                                                try:
                                                    self.minio_client.fget_object(self.bucket_name, object_name, local_path)
                                                except Exception as e:
                                                    st.warning(f"Fehler beim Herunterladen von MinIO: {e}")
                                                    continue

                                                # Checking file type and loading accordingly
                                                if local_path.endswith(".docx"):
                                                    loader = Docx2txtLoader(file_path=local_path)
                                                elif local_path.endswith(".csv"):
                                                    loader = CSVLoader(file_path=local_path)
                                                elif local_path.endswith(".pdf"):
                                                    loader = PyPDFLoader(file_path=local_path)
                                                elif local_path.endswith(".txt"):
                                                    if os.path.basename(local_path) == "questions.txt":
                                                        continue
                                                    loader = TextLoader(file_path=local_path)
                                                else:
                                                    continue

                                                st.markdown(f"{os.path.basename(local_path)}")
                                                docs = loader.load()  # type: ignore
                                                for d in docs:
                                                    if "page" not in d.metadata:
                                                        d.metadata["page"] = 0

                                                    # Setting MinIO URL as source
                                                    minio_url = f"{st.secrets['MinIO']['endpoint']}/{self.bucket_name}/{object_name}"
                                                    d.metadata["source"] = minio_url
                                                documents.extend(docs)

                                # Iterating over all URLs
                                st.markdown("**URLs**")
                                if len(self.urls[0]) > 0:
                                    for url in self.urls:
                                        st.write(url.strip())
                                        loader = WebBaseLoader(url.strip(), requests_kwargs={"verify": False})
                                        docs = loader.load()
                                        for d in docs:
                                            if "page" not in d.metadata:
                                                d.metadata["page"] = 0
                                        documents.extend(docs)
                                return documents

                        # Setting the start time
                        st.session_state.start = time.time()
                        
                        # Setting the online resources
                        urls = st.session_state.online_resources.split(',')
                        st.session_state.loader = CustomDirectoryLoader(
                            urls=urls,
                            bucket_name=st.session_state.option_offline_resources,
                            minio_client=minio_client,
                            glob_pattern="*.docx|*.pdf|*.csv|*.txt"
                        )

                        # Loading the documents
                        st.session_state.docs = st.session_state.loader.load()

                        # Setting the configuration for the text splitter
                        st.session_state.text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=1000, chunk_overlap=100
                        )

                        # Splitting the documents into chunks
                        st.session_state.documents = st.session_state.text_splitter.split_documents(
                            st.session_state.docs
                        )

                        # Preparing texts and metadata for the vector store
                        texts = [doc.page_content for doc in st.session_state.documents]
                        metadatas = [doc.metadata for doc in st.session_state.documents]
                        
                        # Creating the vector store via MCP tool
                        vector_store_response = call_snowflake_mcp_tool(
                            "snowflake_create_vector_store",
                            {
                                "table_name": st.session_state.option_table,
                                "texts": texts,
                                "metadatas": metadatas,
                                "model": st.session_state.option_embedding_model,
                                "vector_length": st.session_state.option_vector_length
                            }
                        )
                        
                        if vector_store_response.get("status") == "success":
                            # Set a flag to indicate we have a vector store
                            st.session_state.vector = "mcp_vector_store"
                            
                            # Showing the time taken
                            st.success(
                                f"Dokumente wurden in {int(time.time() - st.session_state.start)} Sekunden integriert!", icon="✅")
                            st.toast(
                                f"Dokumente wurden in {int(time.time() - st.session_state.start)} Sekunden integriert!", icon="✅")

                            # Waiting for 3 seconds and then reloading the page
                            time.sleep(3)
                            st.rerun()
                        else:
                            st.error(f"Fehler beim Erstellen des Vektorspeichers: {vector_store_response.get('message')}")

    # Connecting to existing vector store(s) if one or multi tables are selected (and not creating a new table)
    if 'vector' not in st.session_state and selected_disp != "Erstelle neue Tabelle":
        # Marking that we're using the MCP tool for vector store access
        st.session_state.vector = "mcp_vector_store"

    # Creating the chat interface
    if 'vector' in st.session_state:
        if isinstance(st.session_state.option_table, list) and len(st.session_state.option_table) < 2:
            st.info("Bitte wähle mindestens 2 Tabellen für die Multi-Table-Abfrage.")
        else:
            # Setting up chat message history
            msgs = StreamlitChatMessageHistory(key="langchain_messages")
            if len(msgs.messages) == 0:
                msgs.add_ai_message(assistant)
            view_messages = st.expander("View the message contents in session state")

            # Rendering chat history
            for msg in msgs.messages:
                st.chat_message(msg.type).write(msg.content)

            # Getting chat input
            user_input = st.chat_input("Frage stellen...")
            if user_input:
                st.chat_message("human").write(user_input)

                # Running RAG query via MCP tool
                st.session_state.start = time.time()
                
                # Call the snowflake_query_rag MCP tool
                rag_response = call_snowflake_mcp_tool(
                    "snowflake_query_rag",
                    {
                        "query": user_input,
                        "system_prompt": system,
                        "table_name": st.session_state.option_table,
                        "model": st.session_state.option_model,
                        "embedding_model": st.session_state.option_embedding_model,
                        "k": 8
                    }
                )
                
                if rag_response.get("status") == "success":
                    answer = rag_response.get("answer", "Keine Antwort erhalten.")
                    answer = answer.replace("Assistant: ", "").replace("\n", " ").lstrip()
                    
                    # Store response for later use
                    st.session_state.response = {
                        "output": answer,
                        "context": []
                    }
                    
                    # Converting context from JSON to document format
                    for doc_result in rag_response.get("context", []):
                        doc = Document(
                            page_content=doc_result.get("content", ""),
                            metadata=doc_result.get("metadata", {})
                        )
                        st.session_state.response["context"].append(doc)
                    
                    st.session_state.answer = answer
                    
                    # Adding the answer to chat history
                    msgs.add_user_message(user_input)
                    msgs.add_ai_message(answer)
                    
                    # Displaying the answer with processing time
                    processing_time = int(time.time() - st.session_state.start)
                    st.chat_message("ai").markdown(
                        f"```\n{answer}\n```\n\n_(verarbeitet in {processing_time} Sekunden)_"
                    )
                else:
                    error_msg = rag_response.get("message", "Ein unbekannter Fehler ist aufgetreten.")
                    st.error(f"Fehler bei der RAG-Abfrage: {error_msg}")

            # Showing similarity search results if available
            if (
                msgs.messages
                and msgs.messages[-1].type == "ai"
                and "response" in st.session_state
                and st.session_state.response
                and hasattr(st.session_state.response, "get")
                and st.session_state.response.get("context")
            ):
                with st.expander("Ähnlichkeitssuche"):
                    for idx, doc in enumerate(st.session_state.response["context"]):
                        try:
                            tbl_name = doc.metadata.get("db_table")
                            st.write(f"**DB-Tabelle**: {tbl_name.replace('LANGCHAIN_', '').upper()}")
                        except Exception:
                            if isinstance(st.session_state.option_table, list):
                                st.write(f"**DB-Tabelle**: {', '.join(st.session_state.option_table).replace('LANGCHAIN_', '').upper()}")
                            else:
                                st.write(f"**DB-Tabelle**: {st.session_state.option_table.replace('LANGCHAIN_', '').upper()}")
                        source = doc.metadata.get("source")
                        if source and isinstance(source, str) and source.startswith(("http://", "https://")):
                            filename = os.path.basename(source)
                            file_found = show_open_file_button(filename, source, idx)
                            if not file_found:
                                st.write(f"**Dateiname**: {filename}")
                        else:
                            # Showing the filename if not a valid URL
                            if source:
                                filename = os.path.basename(source)
                            else:
                                filename = "unbekannt"
                            st.write(f"**Dateiname**: {filename}")
                        st.write("**Inhalt:**")
                        st.text(doc.page_content)
                        st.write("---------------------------")

            # Drawing the messages at the end, so newly generated ones show up immediately
            with view_messages:
                # Creating a function to serialize messages
                def serialize_message(msg):
                    return {
                        "type": getattr(msg, 'type', type(msg).__name__),
                        "content": getattr(msg, 'content', str(msg)),
                        **{k: v for k, v in msg.__dict__.items() if k not in ('type', 'content')}
                    }
                messages_json = [serialize_message(m) for m in msgs.messages]

                # Showing the copy-to-clipboard code window
                st.code(json.dumps(messages_json, ensure_ascii=False, indent=2), language="json")

    else:
        if selected_disp == "Erstelle neue Tabelle":
            st.info("Bitte integriere zuerst Dokumente, um eine Vektorbank zu erstellen.")
        else:
            st.info("Verbindung zum Vektorspeicher wird hergestellt...")

elif func_choice == "🤖 OpenAI Agents":
    if not st.session_state["IS_EMBED"]:
        st.title("🤖 OpenAI Agents")

    user_input_1 = st.text_input("Agent 1: Enter your message", value="Hello, please get the country name for 'DE'")
    user_input_2 = st.text_input("Agent 2: Enter your message", value="What is the weather in London?")

    if st.button("Send to both agents"):
        # Setting up Azure AIProjectClient
        project_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str="swedencentral.api.azureml.ms;fe22c842-64d1-4cb3-b434-bf57d79bf16f;elearning;benbox-agent"
        )
        # = ToolSet()
        #mcp_openapi_url = f"{st.secrets['MCP']['MCP_URL']}/openapi.json"
        #try:
        #    response = requests.get(mcp_openapi_url)
        #    response.raise_for_status()
        #    mcp_openapi_spec = response.json()
        #except Exception as e:
        #    st.error(f"Failed to load MCP OpenAPI spec: {e}")

        #mcp_openapi_tool = OpenApiTool(
        #    name="mcp_tools",
        #    spec=mcp_openapi_spec,
        #    description="MCP tools",
        #    auth=OpenApiAnonymousAuthDetails()
        #)
        #toolset.add(mcp_openapi_tool)

        # Creating Agent 1
        agent1 = project_client.agents.create_agent(
            model="gpt-4o-mini",
            name="Agent One",
            instructions="You are Agent One. Don't use the MCP tools provided via OpenAPI.",
            #toolset=toolset,
        )
        st.toast(f"Created agent 1, ID: {agent1.id}")

        # Creating Agent 2
        agent2 = project_client.agents.create_agent(
            model="gpt-4o-mini",
            name="Agent Two",
            instructions="You are Agent Two. Use only the MCP tools provided via OpenAPI.",
            #toolset=toolset,
        )
        st.toast(f"Created agent 2, ID: {agent2.id}")

        # Creating threads for both agents
        thread1 = project_client.agents.create_thread()
        thread2 = project_client.agents.create_thread()
        st.toast(f"Created threads: {thread1.id}, {thread2.id}")

        # Sending messages to both agents
        message1 = project_client.agents.create_message(
            thread_id=thread1.id,
            role="user",
            content=user_input_1
        )
        message2 = project_client.agents.create_message(
            thread_id=thread2.id,
            role="user",
            content=user_input_2
        )

        # Running both agents
        run1 = project_client.agents.create_and_process_run(
            thread_id=thread1.id,
            agent_id=agent1.id
        )
        run2 = project_client.agents.create_and_process_run(
            thread_id=thread2.id,
            agent_id=agent2.id
        )
        st.toast(f"Runs finished: {run1.status}, {run2.status}")

        # Cleaning up agents
        project_client.agents.delete_agent(agent1.id)
        project_client.agents.delete_agent(agent2.id)

        # Listing all messages in both threads
        messages1 = project_client.agents.list_messages(thread_id=thread1.id)
        messages2 = project_client.agents.list_messages(thread_id=thread2.id)
        st.subheader("Agent 1 Response")
        st.json([msg.as_dict() for msg in messages1.text_messages])
        st.subheader("Agent 2 Response")
        st.json([msg.as_dict() for msg in messages2.text_messages])

elif func_choice == "🕹️ BenBox":
    # Showing embed iframe on `212.227.102.172:6080?autoconnect=1`
    st.title("🕹️ BenBox")
    st.markdown(
        """
        <iframe src="http://212.227.102.172:6080?autoconnect=1" width="100%" height="600px"></iframe>
        """,
        unsafe_allow_html=True
    )