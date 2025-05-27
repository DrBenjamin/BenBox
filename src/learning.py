# `src/learning.py`
# Learning Panel for the BenBox application
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
# Modules
import wx
import src.globals as g
import subprocess
from minio.error import S3Error
from src.server.minio_utils import (
    connect_to_minio,
    upload_files
)
from src.methods import refresh_ctrls

# Method to create a new bucket
def on_create_bucket(self, event):
    dlg = wx.TextEntryDialog(self, "Bitte geben Sie den Namen für den neuen Bucket/Stage ein:", "Neuen Bucket/Stage erstellen")
    if dlg.ShowModal() == wx.ID_OK:
        new_bucket = dlg.GetValue().strip().lower()
        if new_bucket:
            try:
                result = subprocess.run([
                    "mc", "mb", f"myminio/{new_bucket}"
                ], capture_output=True, text=True)
                if result.returncode == 0:
                    # Checking with mc ls if the bucket is present
                    check_result = subprocess.run([
                        "mc", "ls", f"myminio/{new_bucket}"
                    ], capture_output=True, text=True)
                    if check_result.returncode == 0:
                        # Setting anonymous download policy
                        anon_result = subprocess.run([
                            "mc", "anonymous", "set", "download", f"myminio/{new_bucket}"
                        ], capture_output=True, text=True)
                        if anon_result.returncode == 0:
                            wx.MessageBox(f"Bucket/Stage '{new_bucket}' wurde erfolgreich erstellt und für anonymen Download freigegeben.", "Erfolg", wx.OK | wx.ICON_INFORMATION)
                        else:
                            wx.MessageBox(f"Bucket/Stage wurde erstellt, aber anonyme Freigabe fehlgeschlagen: {anon_result.stderr}", "Warnung", wx.OK | wx.ICON_WARNING)

                        # Refreshing and selecting the new bucket
                        self.refresh_learning_ctrl_with_minio(select_bucket_name=new_bucket)
                    else:
                        wx.MessageBox(f"Bucket wurde scheinbar nicht erstellt (mc ls gibt Fehler): {check_result.stderr}", "Fehler", wx.OK | wx.ICON_ERROR)
                else:
                    wx.MessageBox(f"Fehler beim Erstellen des Buckets: {result.stderr}", "Fehler", wx.OK | wx.ICON_ERROR)
            except Exception as e:
                wx.MessageBox(f"Fehler beim Ausführen von mc: {e}", "Fehler", wx.OK | wx.ICON_ERROR)
    dlg.Destroy()

# Method for deleting a bucket or stage
def on_remove_bucket(self, event):
    """
    Removing the selected MinIO bucket after user confirmation.
    """
    selected_index = self.learning_ctrl.GetFirstSelected()
    if selected_index == -1:
        wx.MessageBox(
            "Bitte wählen Sie einen Bucket/Stage zum Löschen aus.",
            "Kein Bucket/Stage ausgewählt",
            wx.OK | wx.ICON_WARNING
        )
        return

    bucket_display_name = self.learning_ctrl.GetItemText(selected_index, 0)
    bucket_name = bucket_display_name.upper()

    dlg = wx.MessageDialog(
        self,
        f"Sind Sie sicher, dass Sie den Bucket/Stage '{bucket_display_name}' und alle darin enthaltenen Objekte löschen möchten?",
        "Bucket/Stage löschen bestätigen",
        wx.YES_NO | wx.NO_DEFAULT | wx.ICON_WARNING
    )
    if dlg.ShowModal() != wx.ID_YES:
        dlg.Destroy()
        return
    dlg.Destroy()

    try:
        minio_client = connect_to_minio()
        if minio_client is None:
            wx.MessageBox(
                "MinIO-Verbindung konnte nicht hergestellt werden.",
                "Fehler",
                wx.OK | wx.ICON_ERROR
            )
            return

        # Normalizing bucket name before MinIO operations
        bucket_name = bucket_name.lower().replace(' ', '-')

        # Deleting all objects in the bucket
        objects = minio_client.list_objects(bucket_name, recursive=True)
        for obj in objects:
            minio_client.remove_object(bucket_name, obj.object_name)
        minio_client.remove_bucket(bucket_name)
        wx.MessageBox(
            f"Bucket/Stage '{bucket_display_name}' wurde erfolgreich gelöscht.",
            "Bucket/Stage gelöscht",
            wx.OK | wx.ICON_INFORMATION
        )

        # Refreshing the bucket list and restoring selection
        self.refresh_learning_ctrl_with_minio()
        item_count = self.learning_ctrl.GetItemCount()
        if item_count > 0:
            # Selecting the next logical bucket (same index or previous if last was deleted)
            new_index = selected_index if selected_index < item_count else item_count - 1
            new_bucket_display = self.learning_ctrl.GetItemText(new_index, 0)
            new_bucket_name = new_bucket_display.upper()
            self.refresh_learning_ctrl_with_minio(select_bucket_name=new_bucket_name)
        else:
            g.elearning_index = -1
            g.minio_bucket_name = ""

            refresh_ctrls(self)

    except S3Error as e:
        wx.MessageBox(
            f"Fehler beim Löschen des Buckets/Stages: {e}",
            "Fehler",
            wx.OK | wx.ICON_ERROR
        )
    except Exception as e:
        wx.MessageBox(
            f"Unerwarteter Fehler beim Löschen des Buckets/Stages: {e}",
            "Fehler",
            wx.OK | wx.ICON_ERROR
        )

# Method to handle the selection of an item in the learning_ctrl
def on_elearning_item_selected(self, event):
    g.elearning_index = event.GetIndex()
    selected_name = self.learning_ctrl.GetItemText(g.elearning_index, 0)
    if getattr(g, "snowflake", False):
        # Setting the selected stage for Snowflake and refresh files for this stage
        g.snowflake_stage = selected_name
        refresh_ctrls(self, stage_name=selected_name)
    else:
        g.minio_bucket_name = selected_name.upper()
        refresh_ctrls(self)

# Method to handle the activation of an item in the learning_ctrl
def on_elearning_item_activated(self, event):
    item_index = event.GetIndex()
    item_text = self.learning_ctrl.GetItemText(item_index, 0)

# Method to upload file(s) to MinIO via wx dialog
def on_upload_file_to_minio(self, event):
    """
    Handling file selection and uploading to MinIO bucket.
    """
    wildcard = "Alle Dateien (*.*)|*.*"
    dialog = wx.FileDialog(
        self,
        "Bitte wählen Sie eine oder mehrere Dateien zum Hochladen aus:",
        wildcard=wildcard,
        style=wx.FD_OPEN | wx.FD_MULTIPLE
    )
    if dialog.ShowModal() == wx.ID_OK:
        file_paths = dialog.GetPaths()
        try:
            # Connecting to MinIO
            minio_client = connect_to_minio()
            if not g.minio_bucket_name:
                wx.MessageBox(
                    "MinIO-Bucket ist nicht gesetzt. Bitte prüfen Sie die Konfiguration.",
                    "Fehler",
                    wx.OK | wx.ICON_ERROR
                )
                return
            if minio_client is None:
                wx.MessageBox(
                    "MinIO-Verbindung konnte nicht hergestellt werden.",
                    "Fehler",
                    wx.OK | wx.ICON_ERROR
                )
                return

            # Creating bucket if it does not exist
            if not minio_client.bucket_exists(g.minio_bucket_name):
                minio_client.make_bucket(g.minio_bucket_name)

            # Uploading files using the helper
            upload_files(minio_client, g.minio_bucket_name, file_paths)

            wx.MessageBox(
                f"{len(file_paths)} Datei(en) erfolgreich hochgeladen.",
                "Upload abgeschlossen",
                wx.OK | wx.ICON_INFORMATION
            )

            # Refreshing the learning control and keeping the current bucket selected
            self.refresh_learning_ctrl_with_minio(select_bucket_name=g.minio_bucket_name)
        except Exception as e:
            wx.MessageBox(
                f"Fehler beim Hochladen zu MinIO: {e}",
                "Fehler",
                wx.OK | wx.ICON_ERROR
            )
    dialog.Destroy()
