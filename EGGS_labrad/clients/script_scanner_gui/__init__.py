"""
Script Scanner GUI can be broken into 2 parts: the TreeView and Scripting.
TreeView comprises everything that involves experimental parameters.
Scripting comprises everything that involves scripts and experimental sequences.

"Views" contains all the GUI files (stores as .ui types).
"connect.py" is a wrapper for a LabRAD connection that additionally managers server
    and client connections, as well as context-related stuff.
"""

from .script_scanner_gui import script_scanner_gui
