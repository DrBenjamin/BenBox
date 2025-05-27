### `src/minio_utils.py`
### # Utility functions for MinIO connection
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
## Modules
import wx
import src.globals as g
import os
import re
from minio import Minio
from minio.error import S3Error
from io import BytesIO

# Method to connect to Minio
def connect_to_minio():
    try:
        # Removing protocol and any path from endpoint (only host:port allowed)
        endpoint = re.sub(r"^https?://", "", g.minio_endpoint, flags=re.IGNORECASE)
        endpoint = endpoint.split("/")[0]  # keeping only host:port, remove any path
        client = Minio(
            endpoint,
            access_key=g.minio_access_key,
            secret_key=g.minio_secret_key,
            secure=g.minio_secure,  # Using HTTP or HTTPS
            cert_check=False
        )
        return client
    except S3Error as e:
        wx.MessageBox(
            f"Fehler beim aufbauen der MinIO-Verbindung: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
    return None

# Method to upload files to MinIO bucket
def upload_files(minio_client, bucket_name, file_paths):
    """
    Uploading files to the specified MinIO bucket.

    Args:
        minio_client: Minio client instance.
        bucket_name: Name of the bucket (str).
        file_paths: List of file paths to upload.
    """
    # Normalizing bucket name before use
    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_data = f.read()
            minio_client.put_object(
                bucket_name.lower().replace(' ', '-'),
                file_name,
                BytesIO(file_data),
                len(file_data)
            )

# Method to list buckets
def list_buckets(minio_client):
    try:
        buckets = minio_client.list_buckets()
        return [
            bucket.name.upper()
            for bucket in buckets
        ]
    except S3Error as e:
        wx.MessageBox(
            f"Fehler beim auflisten der MinIO-Buckets: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
    return

# Method to list objects in a bucket
def list_objects(minio_client, bucket_name):
    bucket_name = bucket_name.lower().replace(' ', '-')
    try:
        objects = minio_client.list_objects(bucket_name, recursive=True)
        return [
            obj.object_name
            for obj in objects
        ]
    except S3Error as e:
        wx.MessageBox(
            f"Fehler beim auflisten der MinIO-Dateien: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
    return

# Adding a helper to delete an object from a bucket
def delete_object_from_bucket(minio_client, bucket_name, object_name):
    """
    Deleting an object from the specified MinIO bucket.

    Args:
        minio_client: Minio client instance.
        bucket_name: Name of the bucket (str).
        object_name: Name of the object to delete (str).
    """
    # Normalizing bucket name before use
    bucket_name_norm = bucket_name.lower().replace(' ', '-')

    # Avoiding double prefix in object_name (e.g. test/test/file.pdf)
    if object_name.startswith(f"{bucket_name_norm}/"):
        object_name = object_name[len(bucket_name_norm) + 1:]
    minio_client.remove_object(bucket_name_norm, object_name)