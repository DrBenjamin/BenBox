### `src/methods.py`
### Various methods for the BenBox application
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
## Modules
import wx
import webbrowser
import src.globals as g
import re
from src.server.minio_utils import (
    connect_to_minio,
    list_buckets,
    list_objects
)
from src.server.snowflake_utils import (
    connect_to_snowflake,
    list_all_stages
)

# Method to refresh and display Snowflake stages or MinIO buckets in the learning_ctrl
def refresh_ctrls(self, select_bucket_name=None):
    """
    Refreshing and displaying Snowflake stages or MinIO buckets in the learning_ctrl.
    Optionally selects a bucket/stage by name after refresh.
    """
    try:
        if getattr(g, "snowflake", False):
            # Displaying all Snowflake stages
            conn = connect_to_snowflake()
            stages = list_all_stages(conn)
            display_learning(self, stages)

            # Clearing all selections before selecting the intended one
            for idx in range(self.learning_ctrl.GetItemCount()):
                self.learning_ctrl.SetItemState(idx, 0, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)

            # Setting the correct stage selection logic
            selected_idx = 0
            target_stage = None
            if select_bucket_name:
                target_stage = select_bucket_name.upper()
            elif hasattr(g, "snowflake_stage") and g.snowflake_stage:
                target_stage = g.snowflake_stage.upper()
            elif stages:
                target_stage = stages[0].upper()

            if target_stage and target_stage in [s.upper() for s in stages]:
                selected_idx = [s.upper() for s in stages].index(target_stage)
            elif stages:
                selected_idx = 0
                target_stage = stages[0]

            if stages:
                g.elearning_index = selected_idx
                g.snowflake_stage = target_stage
                self.learning_ctrl.SetItemState(
                    selected_idx,
                    wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                    wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED
                )
                self.learning_ctrl.EnsureVisible(selected_idx)
        else:
            # MinIO buckets
            if not g.minio_endpoint:
                wx.MessageBox(
                    "MinIO-Endpunkt ist nicht gesetzt. Bitte tragen Sie einen gültigen Wert in der Konfiguration ein.",
                    "Fehler",
                    wx.OK | wx.ICON_ERROR
                )
                return

            minio_client = connect_to_minio()
            if minio_client is None:
                wx.MessageBox(
                    "MinIO-Verbindung konnte nicht hergestellt werden.",
                    "Fehler",
                    wx.OK | wx.ICON_ERROR
                )
                return
            buckets = list_buckets(minio_client)
            if buckets is None:
                buckets = []
            display_learning(self, buckets)

            for idx in range(self.learning_ctrl.GetItemCount()):
                self.learning_ctrl.SetItemState(idx, 0, wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED)

            selected_idx = 0
            target_bucket = None
            if select_bucket_name:
                target_bucket = select_bucket_name.upper()
            elif g.minio_bucket_name:
                target_bucket = g.minio_bucket_name.upper()

            if target_bucket and target_bucket in buckets:
                selected_idx = buckets.index(target_bucket)
            elif buckets:
                selected_idx = 0
                target_bucket = buckets[0]

            if buckets:
                g.minio_bucket_name = target_bucket
                self.learning_ctrl.SetItemState(
                    selected_idx,
                    wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED,
                    wx.LIST_STATE_SELECTED | wx.LIST_STATE_FOCUSED
                )
                self.learning_ctrl.EnsureVisible(selected_idx)
    except Exception as e:
        wx.MessageBox(
            f"Fehler beim Laden der Buckets/Stages: {e}", "Fehler", wx.OK | wx.ICON_ERROR)

# Adding a helper to handle multi-selection and update files/webview
def on_learning_ctrl_selected(self, event):
    """
    Handling multi-selection in the learning_ctrl to show files from several
    buckets/stages.
    Always refreshes file list and reloads the webview with the selected
    buckets/stages.
    """
    # Getting all selected bucket indexes
    selected_indexes = []
    idx = self.learning_ctrl.GetFirstSelected()
    while idx != -1:
        selected_indexes.append(idx)
        idx = self.learning_ctrl.GetNextSelected(idx)

    # Getting all selected bucket names (MinIO style)
    selected_buckets = [
        self.learning_ctrl.GetItemText(i, 0).replace(' ', '-').lower()
        for i in selected_indexes
    ]

    # Setting global state for single or multi selection
    if len(selected_buckets) == 1:
        g.minio_bucket_name = selected_buckets[0]
        g.elearning_index = selected_indexes[0]
    else:
        g.minio_bucket_name = selected_buckets
        g.elearning_index = selected_indexes[0] if selected_indexes else 0

    # Updating the file list to show all files from all selected buckets
    files_combined = []
    minio_client = None
    try:
        minio_client = connect_to_minio()
    except Exception:
        pass
    if minio_client:
        for bucket in selected_buckets:
            try:
                files = list_objects(minio_client, bucket)
                if files:
                    # Prefix files with bucket name for clarity
                    files_combined.extend([f"{bucket}/{f}" for f in files])
            except Exception:
                continue

    # Setting and displaying combined files in the file_listbox
    g.file_list = files_combined
    self.file_listbox.Set(g.file_list)

    # Reloading the webview with the actual buckets query
    if hasattr(self, "tasks_ctrl") and hasattr(self, "HAS_WEBVIEW2") and self.HAS_WEBVIEW2:
        try:
            # Using the helper to load the Streamlit webview with the selected buckets
            from src.methods import load_streamlit_webview
            load_streamlit_webview(self.tasks_ctrl, selected_buckets)
        except Exception:
            pass

# Method to handle the right click event
def on_right_click(self, event):
    # Creating the context menu
    menu = wx.Menu()
    open_item = menu.Append(wx.ID_ANY, "Öffnen")
    copy_path = menu.Append(wx.ID_ANY, "Kopiere Pfad")
    convert_item = menu.Append(wx.ID_ANY, "Konvertiere srt in vtt")

    # Binding handlers
    self.Bind(wx.EVT_MENU, self.on_file_activated, open_item)
    self.Bind(wx.EVT_MENU, self.on_copy_path, copy_path)

    # Showing the menu
    self.PopupMenu(menu, event.GetPosition())
    menu.Destroy()

# Method to handle the Copy Path menu item
def on_copy_path(self, event):
    if g.file_path is not None:
        # Setting protocol based on g.minio_secure
        minio_endpoint = g.minio_endpoint
        protocol = "https" if getattr(g, "minio_secure", False) else "http"
        if not minio_endpoint.startswith("http"):
            minio_endpoint = f"{protocol}://{minio_endpoint}"

        # Removing trailing slash if present
        minio_endpoint = minio_endpoint.rstrip("/")
        bucket = g.minio_bucket_name.lower().replace(" ", "-")

        # Updating to remove bucket prefix from file_path if present
        object_name = g.file_path.lstrip("/")
        if object_name.startswith(f"{bucket}/"):
            object_name = object_name[len(bucket) + 1:]

        url = f"{minio_endpoint}/{bucket}/{object_name}"
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(wx.TextDataObject(url))
        wx.TheClipboard.Close()
    else:
        wx.MessageBox("Keine Datei ausgewählt", "Error", wx.OK | wx.ICON_ERROR)

# Method to handle `Über die App` menu item
def on_about(self, event):
    # Creating a new user-defined window
    frame = wx.Frame(None, title="Über die App", size=(400, 550))
    panel = wx.Panel(frame)
    sizer = wx.BoxSizer(wx.VERTICAL)

    # Adding message
    message = (
        "Name der Anwendung:\n"
        "BenBox\n\n"
    )
    message_label = wx.StaticText(panel, label = message)
    sizer.Add(message_label, 0, wx.ALL, 10)

    # Adding logo
    logo = wx.Bitmap("_internal/images/logo.png", wx.BITMAP_TYPE_PNG)
    logo_image = wx.StaticBitmap(panel, bitmap=logo)
    sizer.Add(logo_image, 0, wx.ALL, 10)

    # Adding 2nd message
    message2 = (
        "Versionsnummer:\n"
        "0.2.0 (build 2025-05-15)\n\n"
        "**** Beschreibung ****\n"
        "Die BenBox ist eine Anwendung zur unkomplizierten Verwaltung von "
        "e-Learning-Inhalten.\n\n"
        "**** Support ****\n"
        "Bei Fragen oder technischen Problemen kontaktieren Sie bitte unseren Support.\n\n"
    )
    message_label2 = wx.StaticText(panel, label = message2)
    sizer.Add(message_label2, 0, wx.ALL, 10)

    # Adding web link to support page
    support_label = wx.StaticText(panel, label="Weitere Informationen finden Sie auf unserer Support-Seite.")
    support_label.SetForegroundColour((0, 0, 255))  # Link-Farbe (Blau)
    font = support_label.GetFont()
    font.SetUnderlined(True)  # Unterstrichen hinzufügen
    support_label.SetFont(font)

    # Adding click event for the link
    support_label.Bind(wx.EVT_LEFT_DOWN, lambda event: webbrowser.open("https://www.seriousbenentertainment.org"))
    sizer.Add(support_label, 0, wx.ALL, 10)

    # Adding message
    thanks_label = wx.StaticText(panel, label="Vielen Dank, dass Sie unsere Anwendung verwenden!")
    thanks_label.SetForegroundColour((0, 128, 0))  # Grüne Farbe für Freundlichkeit
    sizer.Add(thanks_label, 0, wx.ALL, 10)

    # Setting sizer and display window
    panel.SetSizer(sizer)
    frame.Show()

# Method to handle the Contact menu item
def on_contact(self, event):
    mailto_link = "mailto:ben@seriousbenentertainment.org?subject=Supportanfrage&body=Hallo%20Support-Team"
    wx.LaunchDefaultBrowser(mailto_link)

# Method to handle the Exit menu item
def on_exit(self, event):
    self.Close(True)

def load_streamlit_webview(tasks_ctrl, selected_buckets):
    """
    Loading the Streamlit webview with the correct MinIO protocol, endpoint, and buckets.
    Args:
        tasks_ctrl: The wx.html2.WebView instance.
        selected_buckets: List of selected bucket names (strings).
    """

    # Building the buckets query string
    buckets_query = ",".join(selected_buckets) if isinstance(selected_buckets, list) else selected_buckets

    # Removing any existing protocol from endpoint using regex
    endpoint = re.sub(r"^https?://", "", g.streamlit_endpoint, flags=re.IGNORECASE)
    protocol = "https" if g.streamlit_secure else "http"
    url = f"{protocol}://{endpoint}/?embed=true&angular=true&query=5&bucket={buckets_query}"
    tasks_ctrl.LoadURL(url)

# Method to display_learning
def display_learning(self, files):
    self.learning_ctrl.DeleteAllItems()  # only remove items
    for idx, file_name in enumerate(files, start=0):
        self.learning_ctrl.InsertItem(idx, file_name)

    # Selecting the first item if available
    if files:
        g.elearning_index = 0
        self.learning_ctrl.Select(0)
        self.learning_ctrl.EnsureVisible(0)