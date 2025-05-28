### `src/server/snowflake.py`
### MCP server tool for Snowflake RAG operations
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
import streamlit as st
import json
import logging
import os
import base64
from snowflake.snowpark import Session
from snowflake.connector import DictCursor
from typing import List, Dict, Any, Optional, Union
from . import mcp
from .snowrag.snowrag import create_session, fetch_tables_with_retry, drop_table_with_retry

# Setting up logger
logger = logging.getLogger(__name__)

# Setting the user agent for Snowflake
os.environ["USER_AGENT"] = "RAG-on-Snow/1.0 (contact: ben@seriousbenentertainment.org)"


@mcp.tool()
async def snowflake_create_session() -> str:
    """
    Creating a Snowflake session and returning the connection details.
    
    Returns:
        str: JSON string with session information
    """
    try:
        session = create_session()
        return json.dumps({
            "status": "success",
            "message": "Snowflake session created successfully"
        })
    except Exception as e:
        logger.error(f"Error creating Snowflake session: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def snowflake_list_tables() -> str:
    """
    Listing tables from Snowflake with retry on token expiration.
    
    Returns:
        str: JSON string with list of tables
    """
    try:
        session = create_session()
        tables = fetch_tables_with_retry(session.connection)
        
        # Filtering tables that start with LANGCHAIN
        filtered_tables = [
            {
                "name": row[1],
                "display_name": row[1].removeprefix("LANGCHAIN_").upper()
            }
            for row in tables
            if row[1].startswith("LANGCHAIN")
        ]
        
        return json.dumps({
            "status": "success",
            "tables": filtered_tables
        })
    except Exception as e:
        logger.error(f"Error listing Snowflake tables: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def snowflake_drop_table(table_name: str) -> str:
    """
    Dropping a table in Snowflake.
    
    Args:
        table_name (str): Name of the table to drop
        
    Returns:
        str: JSON string with status information
    """
    try:
        session = create_session()
        drop_table_with_retry(session.connection, table_name)
        return json.dumps({
            "status": "success",
            "message": f"Table {table_name} dropped successfully"
        })
    except Exception as e:
        logger.error(f"Error dropping Snowflake table {table_name}: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def snowflake_create_embeddings(texts: List[str], model: str = "multilingual-e5-large") -> str:
    """
    Creating embeddings for the provided texts using Snowflake.
    
    Args:
        texts (List[str]): List of texts to create embeddings for
        model (str, optional): Embedding model to use. Defaults to "multilingual-e5-large".
        
    Returns:
        str: JSON string with embeddings
    """
    try:
        session = create_session()
        cursor = session.connection.cursor(DictCursor)
        embeddings = []
        
        for text in texts:
            q = "SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_1024(?, ?) as EMBEDDING"
            cursor.execute(q, (model, text))
            result = cursor.fetchone()
            embeddings.append(result["EMBEDDING"])
        
        cursor.close()
        
        return json.dumps({
            "status": "success",
            "embeddings": embeddings
        })
    except Exception as e:
        logger.error(f"Error creating embeddings: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def snowflake_create_vector_store(table_name: str, texts: List[str], 
                                       metadatas: Optional[List[Dict[str, Any]]] = None,
                                       model: str = "multilingual-e5-large",
                                       vector_length: int = 1024) -> str:
    """
    Creating a vector store in Snowflake from the provided texts and metadata.
    
    Args:
        table_name (str): Name of the table to create
        texts (List[str]): List of texts to add to the vector store
        metadatas (Optional[List[Dict[str, Any]]], optional): List of metadata dictionaries. Defaults to None.
        model (str, optional): Embedding model to use. Defaults to "multilingual-e5-large".
        vector_length (int, optional): Vector length. Defaults to 1024.
        
    Returns:
        str: JSON string with status information
    """
    try:
        from .snowrag.embedding import SnowflakeEmbeddings
        from .snowrag.vectorstores import SnowflakeVectorStore
        
        session = create_session()
        
        embeddings = SnowflakeEmbeddings(
            connection=session.connection,
            model=model
        )
        
        # Create the vector store
        vector_store = SnowflakeVectorStore.from_texts(
            texts=texts,
            embedding=embeddings,
            metadatas=metadatas,
            table=table_name,
            connection=session.connection,
            vector_length=vector_length
        )
        
        return json.dumps({
            "status": "success",
            "message": f"Vector store created successfully in table {table_name}",
            "row_count": len(texts)
        })
    except Exception as e:
        logger.error(f"Error creating vector store: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def snowflake_similarity_search(query: str, table_name: Union[str, List[str]], 
                                     k: int = 8, model: str = "multilingual-e5-large") -> str:
    """
    Performing similarity search in Snowflake vector store.
    
    Args:
        query (str): Query text to search for
        table_name (Union[str, List[str]]): Table name(s) to search in
        k (int, optional): Number of results to return. Defaults to 8.
        model (str, optional): Embedding model to use. Defaults to "multilingual-e5-large".
        
    Returns:
        str: JSON string with search results
    """
    try:
        from .snowrag.embedding import SnowflakeEmbeddings
        from .snowrag.vectorstores import SnowflakeVectorStore
        
        session = create_session()
        
        embeddings = SnowflakeEmbeddings(
            connection=session.connection,
            model=model
        )
        
        # Create the vector store
        vector_store = SnowflakeVectorStore(
            connection=session.connection,
            embedding=embeddings,
            table=table_name
        )
        
        # Perform similarity search
        docs = vector_store.similarity_search_with_score(query, k=k)
        
        # Format results
        results = []
        for doc, score in docs:
            result = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            }
            results.append(result)
        
        return json.dumps({
            "status": "success",
            "results": results
        })
    except Exception as e:
        logger.error(f"Error performing similarity search: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def snowflake_generate_completion(prompt: str, model: str = "mistral-large") -> str:
    """
    Generating text completion using Snowflake Cortex.
    
    Args:
        prompt (str): Prompt text for completion
        model (str, optional): LLM model to use. Defaults to "mistral-large".
        
    Returns:
        str: JSON string with completion text
    """
    try:
        from .snowrag.llms import Cortex
        
        session = create_session()
        
        llm = Cortex(
            connection=session.connection,
            model=model
        )
        
        # Generate completion
        response = llm._call(prompt)
        
        return json.dumps({
            "status": "success",
            "completion": response
        })
    except Exception as e:
        logger.error(f"Error generating completion: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def snowflake_query_rag(query: str, system_prompt: str, 
                             table_name: Union[str, List[str]], 
                             model: str = "mistral-large", 
                             embedding_model: str = "multilingual-e5-large",
                             k: int = 8) -> str:
    """
    Performing a complete RAG query using Snowflake.
    
    Args:
        query (str): User query
        system_prompt (str): System prompt for the LLM
        table_name (Union[str, List[str]]): Table name(s) to search in
        model (str, optional): LLM model to use. Defaults to "mistral-large".
        embedding_model (str, optional): Embedding model to use. Defaults to "multilingual-e5-large".
        k (int, optional): Number of results to return from vector search. Defaults to 8.
        
    Returns:
        str: JSON string with RAG response and context
    """
    try:
        from .snowrag.embedding import SnowflakeEmbeddings
        from .snowrag.vectorstores import SnowflakeVectorStore
        from .snowrag.llms import Cortex
        
        session = create_session()
        
        # Create embeddings instance
        embeddings = SnowflakeEmbeddings(
            connection=session.connection,
            model=embedding_model
        )
        
        # Create vector store
        vector_store = SnowflakeVectorStore(
            connection=session.connection,
            embedding=embeddings,
            table=table_name
        )
        
        # Perform similarity search to get relevant documents
        docs = vector_store.similarity_search(query, k=k)
        
        # Create LLM instance
        llm = Cortex(
            connection=session.connection,
            model=model
        )
        
        # Prepare context from documents
        context = "\n".join([doc.page_content for doc in docs])
        
        # Create full prompt with system, context and query
        full_prompt = f"{system_prompt}\n\nContext:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        
        # Generate completion
        response = llm._call(full_prompt)
        
        # Format documents for return
        doc_results = []
        for doc in docs:
            doc_result = {
                "content": doc.page_content,
                "metadata": doc.metadata
            }
            doc_results.append(doc_result)
        
        return json.dumps({
            "status": "success",
            "answer": response,
            "context": doc_results
        })
    except Exception as e:
        logger.error(f"Error performing RAG query: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })