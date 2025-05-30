### `src/server/minio.py`
### MCP server tool for MinIO operations
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
import json
import logging
from typing import List, Optional
from . import mcp
from .minio_utils import (
    get_minio_client,
    connect_to_minio,
    create_bucket,
    upload_files,
    list_buckets,
    list_objects,
    delete_object_from_bucket
)

# Setting up logger
logger = logging.getLogger(__name__)


@mcp.tool()
async def minio_list_buckets() -> str:
    """
    Listing all buckets in MinIO.

    Returns:
        str: JSON string with list of bucket names or error message
    """
    try:
        minio_client = get_minio_client()
        if not minio_client:
            return json.dumps({
                "status": "error",
                "message": "Failed to connect to MinIO"
            })

        buckets = list_buckets(minio_client)
        if buckets is None:
            return json.dumps({
                "status": "error", 
                "message": "Failed to list buckets"
            })

        return json.dumps({
            "status": "success",
            "buckets": buckets
        })
    except Exception as e:
        logger.error(f"Error listing MinIO buckets: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def minio_create_bucket(bucket_name: str) -> str:
    """
    Creating a MinIO bucket if it doesn't exist.

    Args:
        bucket_name: Name of the bucket to create

    Returns:
        str: JSON string with operation result
    """
    try:
        minio_client = get_minio_client()
        if not minio_client:
            return json.dumps({
                "status": "error",
                "message": "Failed to connect to MinIO"
            })

        result = create_bucket(minio_client, bucket_name)
        if result:
            return json.dumps({
                "status": "success",
                "message": f"Bucket '{bucket_name}' created or already exists"
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to create bucket '{bucket_name}'"
            })
    except Exception as e:
        logger.error(f"Error creating MinIO bucket: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def minio_list_objects(bucket_name: str) -> str:
    """
    Listing objects in a MinIO bucket.

    Args:
        bucket_name: Name of the bucket to list objects from

    Returns:
        str: JSON string with list of object names or error message
    """
    try:
        minio_client = get_minio_client()
        if not minio_client:
            return json.dumps({
                "status": "error",
                "message": "Failed to connect to MinIO"
            })

        objects = list_objects(minio_client, bucket_name)
        if objects is None:
            return json.dumps({
                "status": "error",
                "message": f"Failed to list objects in bucket '{bucket_name}'"
            })

        return json.dumps({
            "status": "success",
            "bucket": bucket_name,
            "objects": objects
        })
    except Exception as e:
        logger.error(f"Error listing MinIO objects: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def minio_upload_files(bucket_name: str, file_paths: List[str]) -> str:
    """
    Uploading files to a MinIO bucket.

    Args:
        bucket_name: Name of the bucket to upload to
        file_paths: List of file paths to upload

    Returns:
        str: JSON string with operation result
    """
    try:
        minio_client = get_minio_client()
        if not minio_client:
            return json.dumps({
                "status": "error",
                "message": "Failed to connect to MinIO"
            })

        result = upload_files(minio_client, bucket_name, file_paths)
        if result:
            return json.dumps({
                "status": "success",
                "message": f"Successfully uploaded {len(file_paths)} files to '{bucket_name}'"
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to upload files to '{bucket_name}'"
            })
    except Exception as e:
        logger.error(f"Error uploading files to MinIO: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })


@mcp.tool()
async def minio_delete_object(bucket_name: str, object_name: str) -> str:
    """
    Deleting an object from a MinIO bucket.

    Args:
        bucket_name: Name of the bucket
        object_name: Name of the object to delete

    Returns:
        str: JSON string with operation result
    """
    try:
        minio_client = get_minio_client()
        if not minio_client:
            return json.dumps({
                "status": "error",
                "message": "Failed to connect to MinIO"
            })

        result = delete_object_from_bucket(minio_client, bucket_name, object_name)
        if result:
            return json.dumps({
                "status": "success",
                "message": f"Successfully deleted '{object_name}' from '{bucket_name}'"
            })
        else:
            return json.dumps({
                "status": "error",
                "message": f"Failed to delete '{object_name}' from '{bucket_name}'"
            })
    except Exception as e:
        logger.error(f"Error deleting MinIO object: {e}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })