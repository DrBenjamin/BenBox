### `src/server/error_handler.py`
### Unified Error Handler for different UI frameworks
### Open-Source, hosted on https://github.com/DrBenjamin/BenBox
### Please reach out to ben@seriousbenentertainment.org for any questions

from enum import Enum
import functools
import logging
import sys
import traceback

# Setting up logger
logger = logging.getLogger(__name__)

class UIFramework(Enum):
    """Enum for UI frameworks supported by the unified error handler."""
    STREAMLIT = "streamlit"
    WXPYTHON = "wxpython"
    CONSOLE = "console"
    AUTO = "auto"

class UnifiedErrorHandler:
    """
    Unified error handler for different UI frameworks.
    
    This class provides methods for displaying errors, warnings, info,
    and success messages in a consistent way across different UI frameworks
    (Streamlit, wxPython, or console).
    
    It automatically detects the UI framework being used, or can be explicitly
    configured to use a specific framework.
    """
    
    def __init__(self, framework: UIFramework = UIFramework.AUTO):
        """
        Initialize the unified error handler.
        
        Args:
            framework: The UI framework to use. Default is AUTO, which attempts
                      to detect the framework based on imported modules.
        """
        self.framework = framework
        if framework == UIFramework.AUTO:
            self.detect_framework()
    
    def detect_framework(self):
        """Detect which UI framework is being used."""
        try:
            # Check if streamlit is imported and accessible
            import streamlit as st
            if 'streamlit.runtime.scriptrunner' in sys.modules:
                self.framework = UIFramework.STREAMLIT
                return
        except (ImportError, AttributeError):
            pass
        
        try:
            # Check if wx is imported and has an App instance
            import wx
            if wx.GetApp() is not None:
                self.framework = UIFramework.WXPYTHON
                return
        except (ImportError, AttributeError):
            pass
        
        # Default to console if no UI framework is detected
        self.framework = UIFramework.CONSOLE
    
    def error(self, message: str, title: str = "Error", log: bool = True):
        """
        Display an error message using the detected UI framework.
        
        Args:
            message: The error message to display.
            title: The title for the error (used in wxPython).
            log: Whether to log the error message.
        """
        if log:
            logger.error(f"{title}: {message}")
        
        if self.framework == UIFramework.STREAMLIT:
            try:
                import streamlit as st
                st.error(message)
            except (ImportError, AttributeError):
                print(f"ERROR - {title}: {message}", file=sys.stderr)
        
        elif self.framework == UIFramework.WXPYTHON:
            try:
                import wx
                wx.MessageBox(message, title, wx.OK | wx.ICON_ERROR)
            except (ImportError, AttributeError):
                print(f"ERROR - {title}: {message}", file=sys.stderr)
        
        else:  # CONSOLE
            print(f"ERROR - {title}: {message}", file=sys.stderr)
    
    def warning(self, message: str, title: str = "Warning", log: bool = True):
        """
        Display a warning message using the detected UI framework.
        
        Args:
            message: The warning message to display.
            title: The title for the warning (used in wxPython).
            log: Whether to log the warning message.
        """
        if log:
            logger.warning(f"{title}: {message}")
        
        if self.framework == UIFramework.STREAMLIT:
            try:
                import streamlit as st
                st.warning(message)
            except (ImportError, AttributeError):
                print(f"WARNING - {title}: {message}")
        
        elif self.framework == UIFramework.WXPYTHON:
            try:
                import wx
                wx.MessageBox(message, title, wx.OK | wx.ICON_WARNING)
            except (ImportError, AttributeError):
                print(f"WARNING - {title}: {message}")
        
        else:  # CONSOLE
            print(f"WARNING - {title}: {message}")
    
    def info(self, message: str, title: str = "Info", log: bool = True):
        """
        Display an info message using the detected UI framework.
        
        Args:
            message: The info message to display.
            title: The title for the info (used in wxPython).
            log: Whether to log the info message.
        """
        if log:
            logger.info(f"{title}: {message}")
        
        if self.framework == UIFramework.STREAMLIT:
            try:
                import streamlit as st
                st.info(message)
            except (ImportError, AttributeError):
                print(f"INFO - {title}: {message}")
        
        elif self.framework == UIFramework.WXPYTHON:
            try:
                import wx
                wx.MessageBox(message, title, wx.OK | wx.ICON_INFORMATION)
            except (ImportError, AttributeError):
                print(f"INFO - {title}: {message}")
        
        else:  # CONSOLE
            print(f"INFO - {title}: {message}")
    
    def success(self, message: str, title: str = "Success", log: bool = True):
        """
        Display a success message using the detected UI framework.
        
        Args:
            message: The success message to display.
            title: The title for the success message (used in wxPython).
            log: Whether to log the success message.
        """
        if log:
            logger.info(f"{title}: {message}")
        
        if self.framework == UIFramework.STREAMLIT:
            try:
                import streamlit as st
                st.success(message)
            except (ImportError, AttributeError):
                print(f"SUCCESS - {title}: {message}")
        
        elif self.framework == UIFramework.WXPYTHON:
            try:
                import wx
                wx.MessageBox(message, title, wx.OK | wx.ICON_INFORMATION)
            except (ImportError, AttributeError):
                print(f"SUCCESS - {title}: {message}")
        
        else:  # CONSOLE
            print(f"SUCCESS - {title}: {message}")

def error_handler(func):
    """
    Decorator for handling exceptions in functions.
    
    This decorator catches exceptions thrown by the decorated function,
    displays an error message using the UnifiedErrorHandler, and re-raises
    the exception.
    
    Example:
        @error_handler
        def my_function():
            # function code
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = f"An error occurred in {func.__name__}: {str(e)}"
            handler = UnifiedErrorHandler()
            handler.error(error_msg)
            logger.error(f"Exception details: {traceback.format_exc()}")
            raise
    return wrapper

# Creating a global instance for easy access
error_mgr = UnifiedErrorHandler()