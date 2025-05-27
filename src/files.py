### `src/files.py`
### Files Panel for the BenBox application
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
## Modules
import wx
import os
import tempfile
import shutil
import subprocess
import platform
import src.globals as g
from minio.error import S3Error
from src.server.minio_utils import (
    connect_to_minio,
    upload_files,
    delete_object_from_bucket
)
from src.server.snowflake_utils import (
    connect_to_snowflake,
    upload_files_to_stage,
    download_file_from_stage,
    delete_file_from_stage
)
from src.methods import (
    refresh_ctrls
)

# Method to upload file
def on_upload_file(self, event):
    wildcard = "Alle Dateien (*.*)|*.*" 
    dialog = wx.FileDialog(self, "Bitte wählen Sie eine oder mehrere Datei(en) aus:",
        wildcard=wildcard,
        style=wx.FD_OPEN | wx.FD_MULTIPLE
    )
    if dialog.ShowModal() == wx.ID_OK:
        file_paths = dialog.GetPaths()
        dialog.Destroy()

        if getattr(g, "snowflake", False):
            # Using Snowflake stage upload
            conn = connect_to_snowflake()
            stage_name = getattr(g, "snowflake_stage", "@GOOGLE_CLOUD")
            try:
                upload_files_to_stage(conn, stage_name, file_paths)
                wx.MessageBox(f"{len(file_paths)} Datei(en) erfolgreich in die Snowflake Stage '{stage_name}' hochgeladen.", "Upload abgeschlossen", wx.OK | wx.ICON_INFORMATION)

                # Optionally refresh file list if you have a Snowflake file list control
            except Exception as e:
                wx.MessageBox(f"Fehler beim Hochladen in Snowflake Stage: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
        else:
            # Upload to selected MinIO bucket
            minio_client = connect_to_minio()
            if minio_client is None:
                wx.MessageBox("MinIO-Verbindung konnte nicht hergestellt werden.", "Fehler", wx.OK | wx.ICON_ERROR)
                return
            bucket_name = g.minio_bucket_name
            if not bucket_name:
                wx.MessageBox("Kein Bucket ausgewählt.", "Fehler", wx.OK | wx.ICON_ERROR)
                return
            try:
                upload_files(minio_client, bucket_name, file_paths)
                wx.MessageBox(f"{len(file_paths)} Datei(en) erfolgreich in den Bucket '{bucket_name}' hochgeladen.", "Upload abgeschlossen", wx.OK | wx.ICON_INFORMATION)

                # Refreshing file list and restoring bucket selection
                refresh_ctrls(self)

                # Restoring bucket selection in learning_ctrl if available
                if hasattr(self, "learning_ctrl"):
                    for idx in range(self.learning_ctrl.GetItemCount()):
                        display_name = self.learning_ctrl.GetItemText(idx, 0)
                        if display_name.replace(' ', '-').lower() == bucket_name:
                            self.learning_ctrl.Select(idx)
                            self.learning_ctrl.EnsureVisible(idx)
                            g.elearning_index = idx
                            break
            except Exception as e:
                wx.MessageBox(f"Fehler beim Hochladen zu MinIO: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
    else:
        dialog.Destroy()


# Method to delete the selected file (object) from the selected MinIO bucket
def on_delete_file(self, event):
    bucket_name = g.minio_bucket_name
    object_name = g.file_path
    if not bucket_name or not object_name:
        wx.MessageBox("Kein Bucket oder keine Datei ausgewählt.", "Fehler", wx.OK | wx.ICON_ERROR)
        return
    dlg = wx.MessageDialog(self, f"Soll die Datei '{object_name}' wirklich gelöscht werden?", "Datei löschen", wx.YES_NO | wx.ICON_WARNING)
    if dlg.ShowModal() == wx.ID_YES:
        try:
            if getattr(g, "snowflake", False):
                # Using Snowflake stage delete
                conn = connect_to_snowflake()
                stage_name = getattr(g, "snowflake_stage", "@GOOGLE_CLOUD")
                # If object_name is prefixed with stage, remove it
                if object_name.startswith(f"{stage_name}/"):
                    file_name = object_name[len(stage_name) + 1:]
                else:
                    file_name = object_name
                delete_file_from_stage(conn, stage_name, file_name)
                wx.MessageBox(f"Datei '{file_name}' wurde aus der Snowflake Stage '{stage_name}' gelöscht.", "Erfolg", wx.OK | wx.ICON_INFORMATION)

                # Optionally refresh file list if you have a Snowflake file list control
            else:
                minio_client = connect_to_minio()
                if minio_client is None:
                    wx.MessageBox("MinIO-Verbindung konnte nicht hergestellt werden.", "Fehler", wx.OK | wx.ICON_ERROR)
                    return

                # Using the helper to delete the object from the bucket
                delete_object_from_bucket(minio_client, bucket_name, object_name)
                wx.MessageBox(f"Datei '{object_name}' wurde gelöscht.", "Erfolg", wx.OK | wx.ICON_INFORMATION)

                # Refreshing file list
                refresh_ctrls(self)
        except Exception as e:
            wx.MessageBox(f"Fehler beim Löschen der Datei: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
    dlg.Destroy()

# Method to handle selected file
def on_file_selected(self, event):
    file_index = event.GetSelection()
    file_path = self.file_listbox.GetString(file_index)
    g.file_path = file_path

# Method to handle the list control item activated event
def on_file_activated(self, event):
    # Downloading the file from MinIO to a buffer and open it with the default application
    try:
        if getattr(g, "snowflake", False):
            # Downloading from Snowflake stage
            conn = connect_to_snowflake()
            stage_name = getattr(g, "snowflake_stage", "@GOOGLE_CLOUD")
            object_name = g.file_path
            # If object_name is prefixed with stage, remove it
            if object_name.startswith(f"{stage_name}/"):
                file_name = object_name[len(stage_name) + 1:]
            elif "/" in object_name:
                # If format is stage/file
                _, file_name = object_name.split("/", 1)
            else:
                file_name = object_name
            # Download to temp file
            suffix = os.path.splitext(file_name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file_path = tmp_file.name
            download_file_from_stage(conn, stage_name, file_name, tmp_file_path)
            # Opening the file with the default application
            if platform.system() == "Windows":
                os.startfile(tmp_file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", tmp_file_path])
            else:  # Linux
                subprocess.call(["xdg-open", tmp_file_path])
        else:
            minio_client = connect_to_minio()
            if minio_client is None:
                wx.MessageBox("MinIO-Verbindung konnte nicht hergestellt werden.", "Fehler", wx.OK | wx.ICON_ERROR)
                return

            # Handling multi-selection: g.minio_bucket_name may be a list
            bucket_name = g.minio_bucket_name
            object_name = g.file_path

            # If bucket_name is a list, extract from file_path prefix
            if isinstance(bucket_name, list):
                # Expecting file_path in format "bucket/file"
                if "/" in object_name:
                    bucket_name, object_name = object_name.split("/", 1)
                else:
                    wx.MessageBox("Dateipfad ungültig für Multi-Bucket-Auswahl.", "Fehler", wx.OK | wx.ICON_ERROR)
                    return

            # Ensuring bucket_name is valid (MinIO expects lowercase, hyphenated)
            bucket_name = bucket_name.lower().replace(' ', '-')

            # Avoiding double prefix in object_name (e.g. test/test/file.pdf)
            if object_name.startswith(f"{bucket_name}/"):
                object_name = object_name[len(bucket_name) + 1 :]

            # Getting the object from MinIO
            try:
                response = minio_client.get_object(bucket_name, object_name)
            except S3Error as e:
                wx.MessageBox(
                    f"Datei konnte nicht geöffnet oder heruntergeladen werden: {e}\n\nbucket_name: {bucket_name}, object_name: {object_name}",
                    "Error", wx.OK | wx.ICON_ERROR
                )
                return

            # Saving to a temporary file
            suffix = os.path.splitext(object_name)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                shutil.copyfileobj(response, tmp_file)
                tmp_file_path = tmp_file.name
            response.close()
            response.release_conn()

            # Opening the file with the default application
            if platform.system() == "Windows":
                os.startfile(tmp_file_path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.call(["open", tmp_file_path])
            else:  # Linux
                subprocess.call(["xdg-open", tmp_file_path])
    except Exception as e:
        wx.MessageBox(f"Datei konnte nicht geöffnet oder heruntergeladen werden: {e}", "Error", wx.OK | wx.ICON_ERROR)
