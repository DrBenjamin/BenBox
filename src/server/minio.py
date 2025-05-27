### `src/server/minio.py`
### Utility functions for MinIO connection
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
import streamlit as st
import logging
import os
import re
from minio import Minio
from minio.error import S3Error
from io import BytesIO

# Setting up logger
logger = logging.getLogger(__name__)

# Function to set up MinIO client from Streamlit secrets
def get_minio_client():
    """Creating and returning a MinIO client using Streamlit secrets."""
    try:
        # Removing protocol and any path from endpoint (only host:port allowed)
        endpoint = re.sub(r"^https?://", "", st.secrets["MinIO"]["endpoint"], flags=re.IGNORECASE)
        endpoint = endpoint.split("/")[0]  # keeping only host:port, remove any path
        
        return Minio(
            endpoint,
            access_key=st.secrets["MinIO"]["access_key"],
            secret_key=st.secrets["MinIO"]["secret_key"],
            secure=st.secrets["MinIO"].get("secure", False),  # Using HTTP or HTTPS
            cert_check=False
        )
    except Exception as e:
        logger.error(f"Error connecting to MinIO: {e}")
        st.error(f"Error connecting to MinIO: {e}")
        return None

# Function to create a bucket if it doesn't exist
def create_bucket(minio_client, bucket_name):
    """
    Creating a MinIO bucket if it doesn't exist.
    
    Args:
        minio_client: MinIO client instance
        bucket_name: Name of the bucket to create
    Returns:
        bool: True if bucket was created or already exists, False otherwise
    """
    try:
        # Normalizing bucket name before use
        bucket_name = bucket_name.lower().replace(' ', '-')
        
        # Checking if the bucket exists
        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)
            logger.info(f"Bucket '{bucket_name}' created successfully")
        return True
    except S3Error as e:
        logger.error(f"Error creating bucket: {e}")
        st.error(f"Error creating bucket: {e}")
        return False

# Function to upload files to MinIO bucket
def upload_files(minio_client, bucket_name, file_paths):
    """
    Uploading files to the specified MinIO bucket.

    Args:
        minio_client: MinIO client instance.
        bucket_name: Name of the bucket (str).
        file_paths: List of file paths to upload.
    """
    try:
        # Normalizing bucket name before use
        bucket_name = bucket_name.lower().replace(' ', '-')
        
        # Creating the bucket if it doesn't exist
        create_bucket(minio_client, bucket_name)
        
        # Uploading each file
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            with open(file_path, "rb") as f:
                file_data = f.read()
                minio_client.put_object(
                    bucket_name,
                    file_name,
                    BytesIO(file_data),
                    len(file_data)
                )
        return True
    except Exception as e:
        logger.error(f"Error uploading files to MinIO: {e}")
        st.error(f"Error uploading files to MinIO: {e}")
        return False

# Function to list buckets
def list_buckets(minio_client):
    """
    Listing all buckets in MinIO.
    
    Args:
        minio_client: MinIO client instance
    Returns:
        list: List of bucket names or None on error
    """
    try:
        buckets = minio_client.list_buckets()
        # Returning bucket names as lowercase and hyphenated for MinIO compatibility
        return [
            bucket.name.lower().replace(' ', '-')
            for bucket in buckets
        ]
    except S3Error as e:
        logger.error(f"Error listing buckets: {e}")
        st.error(f"Error listing buckets: {e}")
    return None

# Function to list objects in a bucket
def list_objects(minio_client, bucket_name):
    """
    Listing objects in a MinIO bucket.
    
    Args:
        minio_client: MinIO client instance
        bucket_name: Name of the bucket to list objects from
    Returns:
        list: List of object names or None on error
    """
    try:
        # Normalizing bucket name before use
        bucket_name = bucket_name.lower().replace(' ', '-')
        
        objects = minio_client.list_objects(bucket_name, recursive=True)
        return [
            obj.object_name
            for obj in objects
        ]
    except S3Error as e:
        logger.error(f"Error listing objects in bucket: {e}")
        st.error(f"Error listing objects in bucket: {e}")
    return None

# Function to delete an object from a bucket
def delete_object_from_bucket(minio_client, bucket_name, object_name):
    """
    Deleting an object from the specified MinIO bucket.

    Args:
        minio_client: Minio client instance.
        bucket_name: Name of the bucket (str).
        object_name: Name of the object to delete (str).
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    try:
        # Normalizing bucket name before use
        bucket_name_norm = bucket_name.lower().replace(' ', '-')

        # Avoiding double prefix in object_name (e.g. test/test/file.pdf)
        if object_name.startswith(f"{bucket_name_norm}/"):
            object_name = object_name[len(bucket_name_norm) + 1:]
            
        minio_client.remove_object(bucket_name_norm, object_name)
        return True
    except Exception as e:
        logger.error(f"Error deleting object from bucket: {e}")
        st.error(f"Error deleting object from bucket: {e}")
        return False
