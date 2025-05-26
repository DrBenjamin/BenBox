### `src/preferences.py`
### Preferences Panel for the BenBox application
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions
## Modules
import wx # wxPython / Phoenix
import src.globals as g

# Method to handle the Preferences menu item
def on_preferences(self, event):
    dialog = wx.PreferencesEditor()
    dialog.AddPage(PreferencesPage(self.config))
    self.preferences_dialog = dialog
    dialog.Show(self)

class PreferencesPage(wx.StockPreferencesPage):
    def __init__(self, config):
        super().__init__(wx.StockPreferencesPage.Kind_General)
        self.config = config

    def GetName(self):
        return "Einstellungen"

    def GetIcon(self):
        bitmap = wx.ArtProvider.GetBitmap(wx.ART_HELP_SIDE_PANEL, wx.ART_OTHER, (32, 32))
        return wx.BitmapBundle.FromBitmap(bitmap)

    def CreateWindow(self, parent):
        panel = wx.Panel(parent)
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Storage backend selection
        sizer.Add(wx.StaticText(panel, label="Speicher-Backend auswählen (Snowflake oder MinIO)"), 0, wx.ALL, 5)
        self.snowflake_checkbox = wx.CheckBox(panel, label="Snowflake verwenden (wenn deaktiviert: MinIO)")
        self.snowflake_checkbox.SetValue(self.config.ReadBool("snowflake", True))
        sizer.Add(self.snowflake_checkbox, 0, wx.ALL, 5)
        self.snowflake_checkbox.Bind(wx.EVT_CHECKBOX, self.on_snowflake_checkbox)

        if self.snowflake_checkbox.IsChecked():
            # Adding preference controls for Snowflake
            heading_snowflake = wx.StaticText(panel, label="Snowflake Einstellungen")
            font = heading_snowflake.GetFont()
            font.PointSize += 2
            heading_snowflake.SetFont(font)
            sizer.Add(heading_snowflake, 0, wx.ALL, 5)

            # Snowflake user
            sizer.Add(wx.StaticText(panel, label="Snowflake User"), 0, wx.ALL, 5)
            self.snowflake_user_ctrl = wx.TextCtrl(panel, value=self.config.Read("snowflake_user", ""))
            sizer.Add(self.snowflake_user_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.snowflake_user_ctrl.Bind(wx.EVT_TEXT, self.on_snowflake_user)

            # Snowflake account
            sizer.Add(wx.StaticText(panel, label="Snowflake Account"), 0, wx.ALL, 5)
            self.snowflake_account_ctrl = wx.TextCtrl(panel, value=self.config.Read("snowflake_account", ""))
            sizer.Add(self.snowflake_account_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.snowflake_account_ctrl.Bind(wx.EVT_TEXT, self.on_snowflake_account)

            # Snowflake warehouse
            sizer.Add(wx.StaticText(panel, label="Snowflake Warehouse"), 0, wx.ALL, 5)
            self.snowflake_warehouse_ctrl = wx.TextCtrl(panel, value=self.config.Read("snowflake_warehouse", ""))
            sizer.Add(self.snowflake_warehouse_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.snowflake_warehouse_ctrl.Bind(wx.EVT_TEXT, self.on_snowflake_warehouse)

            # Snowflake database
            sizer.Add(wx.StaticText(panel, label="Snowflake Database"), 0, wx.ALL, 5)
            self.snowflake_database_ctrl = wx.TextCtrl(panel, value=self.config.Read("snowflake_database", ""))
            sizer.Add(self.snowflake_database_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.snowflake_database_ctrl.Bind(wx.EVT_TEXT, self.on_snowflake_database)

            # Snowflake schema
            sizer.Add(wx.StaticText(panel, label="Snowflake Schema"), 0, wx.ALL, 5)
            self.snowflake_schema_ctrl = wx.TextCtrl(panel, value=self.config.Read("snowflake_schema", ""))
            sizer.Add(self.snowflake_schema_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.snowflake_schema_ctrl.Bind(wx.EVT_TEXT, self.on_snowflake_schema)

            # Snowflake role
            sizer.Add(wx.StaticText(panel, label="Snowflake Role"), 0, wx.ALL, 5)
            self.snowflake_role_ctrl = wx.TextCtrl(panel, value=self.config.Read("snowflake_role", ""))
            sizer.Add(self.snowflake_role_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.snowflake_role_ctrl.Bind(wx.EVT_TEXT, self.on_snowflake_role)

            # Snowflake private key file
            sizer.Add(wx.StaticText(panel, label="Snowflake Private Key File (Pfad)"), 0, wx.ALL, 5)
            self.snowflake_private_key_file_ctrl = wx.TextCtrl(panel, value=self.config.Read("snowflake_private_key_file", ""))
            sizer.Add(self.snowflake_private_key_file_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.snowflake_private_key_file_ctrl.Bind(wx.EVT_TEXT, self.on_snowflake_private_key_file)

        else:
            # Adding preference controls for MinIO
            heading_minio = wx.StaticText(panel, label="MinIO Einstellungen")
            font = heading_minio.GetFont()
            font.PointSize += 2
            heading_minio.SetFont(font)
            sizer.Add(heading_minio, 0, wx.ALL, 5)

            # MinIO endpoint
            sizer.Add(wx.StaticText(panel, label="MinIO Endpoint"), 0, wx.ALL, 5)
            self.minio_endpoint_ctrl = wx.TextCtrl(panel, value=self.config.Read("minio_endpoint", "host.docker.internal:9000"))
            sizer.Add(self.minio_endpoint_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.minio_endpoint_ctrl.Bind(wx.EVT_TEXT, self.on_minio_endpoint)

            # MinIO access key
            sizer.Add(wx.StaticText(panel, label="MinIO Access Key"), 0, wx.ALL, 5)
            self.minio_access_key_ctrl = wx.TextCtrl(panel, value=self.config.Read("minio_access_key", "<username>"))
            sizer.Add(self.minio_access_key_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.minio_access_key_ctrl.Bind(wx.EVT_TEXT, self.on_minio_access_key)

            # MinIO secret key
            sizer.Add(wx.StaticText(panel, label="MinIO Secret Key"), 0, wx.ALL, 5)
            self.minio_secret_key_ctrl = wx.TextCtrl(panel, value=self.config.Read("minio_secret_key", "<password>"), style=wx.TE_PASSWORD)
            sizer.Add(self.minio_secret_key_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.minio_secret_key_ctrl.Bind(wx.EVT_TEXT, self.on_minio_secret_key)

            # MinIO secure (http/https)
            sizer.Add(wx.StaticText(panel, label="MinIO Secure (HTTPS aktivieren)"), 0, wx.ALL, 5)
            self.minio_secure_checkbox = wx.CheckBox(panel, label="HTTPS verwenden")
            self.minio_secure_checkbox.SetValue(self.config.ReadBool("minio_secure", False))
            sizer.Add(self.minio_secure_checkbox, 0, wx.ALL, 5)
            self.minio_secure_checkbox.Bind(wx.EVT_CHECKBOX, self.on_minio_secure)

            # MinIO bucket name
            sizer.Add(wx.StaticText(panel, label="MinIO Bucket Name"), 0, wx.ALL, 5)
            self.minio_bucket_name_ctrl = wx.TextCtrl(panel, value=self.config.Read("minio_bucket_name", "<bucketname>"))
            sizer.Add(self.minio_bucket_name_ctrl, 0, wx.ALL | wx.EXPAND, 5)
            self.minio_bucket_name_ctrl.Bind(wx.EVT_TEXT, self.on_minio_bucket_name)

        # Adding Streamlit app preferences
        heading_streamlit = wx.StaticText(panel, label="Streamlit")
        font = heading_streamlit.GetFont()
        font.PointSize += 2
        heading_streamlit.SetFont(font)
        sizer.Add(heading_streamlit, 0, wx.ALL, 5)

        # Streamlit app URL for embedding
        sizer.Add(wx.StaticText(panel, label="Streamlit App URL (für Einbettung)"), 0, wx.ALL, 5)
        self.streamlit_url_ctrl = wx.TextCtrl(panel, value=self.config.Read("streamlit_url", "http://streamlit:8501"))
        sizer.Add(self.streamlit_url_ctrl, 0, wx.ALL | wx.EXPAND, 5)
        self.streamlit_url_ctrl.Bind(wx.EVT_TEXT, self.on_streamlit_url)

        # Streamlit secure (http/https)
        sizer.Add(wx.StaticText(panel, label="Streamlit Secure (HTTPS aktivieren)"), 0, wx.ALL, 5)
        self.streamlit_secure_checkbox = wx.CheckBox(panel, label="HTTPS verwenden")
        self.streamlit_secure_checkbox.SetValue(self.config.ReadBool("streamlit_secure", False))
        sizer.Add(self.streamlit_secure_checkbox, 0, wx.ALL, 5)
        self.streamlit_secure_checkbox.Bind(wx.EVT_CHECKBOX, self.on_streamlit_secure)

        # Setting the sizer for the panel
        panel.SetSizer(sizer)
        return panel

    # Snowflake handlers
    def on_snowflake_checkbox(self, event):
        self.config.WriteBool("snowflake", self.snowflake_checkbox.IsChecked())
        self.config.Flush()
        
    def on_snowflake_user(self, event):
        self.config.Write("snowflake_user", self.snowflake_user_ctrl.GetValue())
        self.config.Flush()

    def on_snowflake_account(self, event):
        self.config.Write("snowflake_account", self.snowflake_account_ctrl.GetValue())
        self.config.Flush()

    def on_snowflake_warehouse(self, event):
        self.config.Write("snowflake_warehouse", self.snowflake_warehouse_ctrl.GetValue())
        self.config.Flush()

    def on_snowflake_database(self, event):
        self.config.Write("snowflake_database", self.snowflake_database_ctrl.GetValue())
        self.config.Flush()

    def on_snowflake_schema(self, event):
        self.config.Write("snowflake_schema", self.snowflake_schema_ctrl.GetValue())
        self.config.Flush()

    def on_snowflake_role(self, event):
        self.config.Write("snowflake_role", self.snowflake_role_ctrl.GetValue())
        self.config.Flush()

    def on_snowflake_private_key_file(self, event):
        self.config.Write("snowflake_private_key_file", self.snowflake_private_key_file_ctrl.GetValue())
        self.config.Flush()

    # Adding MinIO endpoint handler
    def on_minio_endpoint(self, event):
        self.config.Write("minio_endpoint", self.minio_endpoint_ctrl.GetValue())
        self.config.Flush()

    # Adding MinIO access key handler
    def on_minio_access_key(self, event):
        self.config.Write("minio_access_key", self.minio_access_key_ctrl.GetValue())
        self.config.Flush()

    # Adding MinIO secret key handler
    def on_minio_secret_key(self, event):
        self.config.Write("minio_secret_key", self.minio_secret_key_ctrl.GetValue())
        self.config.Flush()

    # Adding MinIO secure handler
    def on_minio_secure(self, event):
        self.config.WriteBool("minio_secure", self.minio_secure_checkbox.IsChecked())
        self.config.Flush()

    # Adding MinIO bucket name handler
    def on_minio_bucket_name(self, event):
        self.config.Write("minio_bucket_name", self.minio_bucket_name_ctrl.GetValue())
        self.config.Flush()

    # Adding Streamlit app URL handler
    def on_streamlit_url(self, event):
        self.config.Write("streamlit_url", self.streamlit_url_ctrl.GetValue())
        self.config.Flush()

    # Adding Streamlit secure handler
    def on_streamlit_secure(self, event):
        self.config.WriteBool("streamlit_secure", self.streamlit_secure_checkbox.IsChecked())
        self.config.Flush()
