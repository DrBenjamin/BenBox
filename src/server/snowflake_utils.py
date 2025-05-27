### `src/server/snowflake_utils.py`
### Utility functions for Snowflake connection
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
import os
import logging
import snowflake.connector
from cryptography.hazmat.primitives import serialization
from src.server.error_handler import error_mgr, error_handler

# Setting up logger
logger = logging.getLogger(__name__)

# Function to connect to Snowflake
@error_handler
def connect_to_snowflake():
    """
    Connecting to Snowflake using credentials from Streamlit secrets.
    Returns:
        snowflake.connector.connection: Snowflake connection object
    """
    try:
        # Import streamlit here to avoid import errors when not in Streamlit context
        import streamlit as st
        
        conn = snowflake.connector.connect(**st.secrets.snowflake)
        return conn
    except Exception as e:
        error_mgr.error(f"Error connecting to Snowflake: {e}")
        return None


# Function to list all stages in the current database/schema
@error_handler
def list_all_stages(conn):
    """
    Listing all stages in the current database/schema using SHOW STAGES command.

    Args:
        conn: Snowflake connection object.
    Returns:
        List of stage names (with @ prefix).
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SHOW STAGES")
        stages = [f"@{row[1]}" if not row[1].startswith("@") else row[1] for row in cursor.fetchall()]
        cursor.close()
        return stages
    except Exception as e:
        error_mgr.error(f"Error listing stages: {e}")
        return []


# Function to upload files to a Snowflake stage
@error_handler
def upload_files_to_stage(conn, stage_name, file_paths, overwrite=True):
    """
    Uploading files to a Snowflake stage using PUT command.

    Args:
        conn: Snowflake connection object.
        stage_name: Name of the stage (e.g. '@MY_STAGE').
        file_paths: List of file paths to upload.
        overwrite: Whether to overwrite existing files (default: True).
    """
    cursor = conn.cursor()
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        stage_file = f"{stage_name}/{file_name}"
        put_sql = f"PUT file://{file_path} {stage_file} OVERWRITE={'TRUE' if overwrite else 'FALSE'}"
        logger.info(f"Uploading {file_path} to {stage_file} in Snowflake stage...")
        cursor.execute(put_sql)
    cursor.close()

# Function to list files in a Snowflake stage
@error_handler
def list_stage_files(conn, stage_name):
    """
    Listing files in a Snowflake stage using LIST command.

    Args:
        conn: Snowflake connection object.
        stage_name: Name of the stage (e.g. '@MY_STAGE').
    Returns:
        List of file names in the stage.
    """
    try:
        cursor = conn.cursor()
        list_sql = f"LIST {stage_name}"
        cursor.execute(list_sql)
        files = [
            row[0]
            for row in cursor.fetchall()
        ]
        cursor.close()
        return files
    except Exception as e:
        error_mgr.error(f"Error listing files in Snowflake Stage: {e}")
        return []


# Function to download a file from a Snowflake stage
@error_handler
def download_file_from_stage(conn, stage_name, file_name, local_path):
    """
    Downloading a file from a Snowflake stage using GET command.

    Args:
        conn: Snowflake connection object.
        stage_name: Name of the stage (e.g. '@MY_STAGE').
        file_name: Name of the file in the stage.
        local_path: Local path to save the downloaded file.
    """
    cursor = conn.cursor()
    get_sql = f"GET {stage_name}/{file_name} file://{local_path} OVERWRITE=TRUE"
    logger.info(f"Downloading {file_name} from {stage_name} to {local_path}...")
    cursor.execute(get_sql)
    cursor.close()


# Function to delete a file from a Snowflake stage
@error_handler
def delete_file_from_stage(conn, stage_name, file_name):
    """
    Deleting a file from a Snowflake stage using REMOVE command.

    Args:
        conn: Snowflake connection object.
        stage_name: Name of the stage (e.g. '@MY_STAGE').
        file_name: Name of the file in the stage.
    """
    cursor = conn.cursor()
    remove_sql = f"REMOVE {stage_name}/{file_name}"
    logger.info(f"Deleting {file_name} from {stage_name} in Snowflake stage...")
    cursor.execute(remove_sql)
    cursor.close()
