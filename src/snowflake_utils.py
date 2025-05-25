### `src/snowflake_utils.py`
### # Utility functions for Snowflake connection
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
## Modules
import wx
import os
import snowflake.connector
import logging
# Setting up logger
logger = logging.getLogger(__name__)
from cryptography.hazmat.primitives import serialization

# Method to connect to Snowflake
def connect_to_snowflake():
    """
    Connecting to Snowflake using credentials from Streamlit secrets.
    Returns:
        snowflake.connector.connection: Snowflake connection object
    """
    try:
        import src.globals as g
        private_key_path = g.snowflake_private_key_file

        # Reading private key file
        with open(private_key_path, "rb") as key_file:
            pkey = key_file.read()
        private_key = serialization.load_pem_private_key(
            pkey,
            password=None,
        )
        pkb = private_key.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        conn = snowflake.connector.connect(
            user=g.snowflake_user,
            private_key=pkb,
            account=g.snowflake_account,
            warehouse=g.snowflake_warehouse,
            database=g.snowflake_database,
            schema=g.snowflake_schema,
            role=g.snowflake_role
        )
        return conn
    except Exception as e:
        logger.error(f"Fehler beim Verbinden mit Snowflake: {e}")
        wx.MessageBox(f"Fehler beim Verbinden mit Snowflake: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
        return None


# Method to list all stages in the current database/schema
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
        # The stage name is in the first column ("name"), and may need to be prefixed with '@'
        stages = [f"@{row[1]}" if not row[1].startswith("@") else row[1] for row in cursor.fetchall()]
        cursor.close()
        return stages
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Stages: {e}")
        wx.MessageBox(f"Fehler beim Auflisten der Stages: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
        return []


# Method to upload files to a Snowflake stage
def upload_files_to_stage(conn, stage_name, file_paths, overwrite=True):
    """
    Uploading files to a Snowflake stage using PUT command.

    Args:
        conn: Snowflake connection object.
        stage_name: Name of the stage (e.g. '@MY_STAGE').
        file_paths: List of file paths to upload.
        overwrite: Whether to overwrite existing files (default: True).
    """
    try:
        cursor = conn.cursor()
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            stage_file = f"{stage_name}/{file_name}"
            put_sql = f"PUT file://{file_path} {stage_file} OVERWRITE={'TRUE' if overwrite else 'FALSE'}"
            logger.info(f"Uploading {file_path} to {stage_file} in Snowflake stage...")
            cursor.execute(put_sql)
        cursor.close()
    except Exception as e:
        logger.error(f"Fehler beim Hochladen in Snowflake Stage: {e}")
        wx.MessageBox(f"Fehler beim Hochladen in Snowflake Stage: {e}", "Fehler", wx.OK | wx.ICON_ERROR)


# Method to list files in a Snowflake stage
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
        print(files)
        cursor.close()
        return files
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Dateien in Snowflake Stage: {e}")
        wx.MessageBox(f"Fehler beim Auflisten der Dateien in Snowflake Stage: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
        return []


# Method to download a file from a Snowflake stage
def download_file_from_stage(conn, stage_name, file_name, local_path):
    """
    Downloading a file from a Snowflake stage using GET command.

    Args:
        conn: Snowflake connection object.
        stage_name: Name of the stage (e.g. '@MY_STAGE').
        file_name: Name of the file in the stage.
        local_path: Local path to save the downloaded file.
    """
    try:
        cursor = conn.cursor()
        get_sql = f"GET {stage_name}/{file_name} file://{local_path} OVERWRITE=TRUE"
        logger.info(f"Downloading {file_name} from {stage_name} to {local_path}...")
        cursor.execute(get_sql)
        cursor.close()
    except Exception as e:
        logger.error(f"Fehler beim Herunterladen aus Snowflake Stage: {e}")
        wx.MessageBox(f"Fehler beim Herunterladen aus Snowflake Stage: {e}", "Fehler", wx.OK | wx.ICON_ERROR)


# Method to delete a file from a Snowflake stage
def delete_file_from_stage(conn, stage_name, file_name):
    """
    Deleting a file from a Snowflake stage using REMOVE command.

    Args:
        conn: Snowflake connection object.
        stage_name: Name of the stage (e.g. '@MY_STAGE').
        file_name: Name of the file in the stage.
    """
    try:
        cursor = conn.cursor()
        remove_sql = f"REMOVE {stage_name}/{file_name}"
        logger.info(f"Deleting {file_name} from {stage_name} in Snowflake stage...")
        cursor.execute(remove_sql)
        cursor.close()
    except Exception as e:
        logger.error(f"Fehler beim Löschen aus Snowflake Stage: {e}")
        wx.MessageBox(f"Fehler beim Löschen aus Snowflake Stage: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
