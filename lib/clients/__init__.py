"""
Contains stuff useful for LabRAD clients.
"""

__all__ = ["runGUI", "runClient", "GUIClient", "RecordingClient", "connection"]

from EGGS_labrad.lib.clients.client import GUIClient, RecordingClient
from EGGS_labrad.lib.clients.connection import connection



# imports
import sys
from PyQt5.QtWidgets import QApplication


# run functions
def runGUI(client, **kwargs):
    """
    Runs a LabRAD GUI file written using PyQt5
    """
    # widgets require a QApplication to run
    app = QApplication(sys.argv)
    # instantiate gui
    gui = client(**kwargs)
    # set up UI if needed
    try:
        gui.setupUi()
    except Exception as e:
        print('No need to setup UI')
    # run GUI file
    gui.show()
    sys.exit(app.exec())

def runClient(client, **kwargs):
    """
    Runs a LabRAD client written using PyQt5
    """
    # widgets require a QApplication to run
    app = QApplication([])
    # reactor may already be installed
    try:
        import qt5reactor
        qt5reactor.install()
    except Exception as e:
        print(e)
    # instantiate client with a reactor
    from twisted.internet import reactor
    client = client(reactor, **kwargs)
    # show client
    if hasattr(client, 'show'):
        client.show()
    elif hasattr(client, 'gui') and hasattr(client.gui, 'show'):
        client.gui.show()
    # start reactor
    reactor.run()
    # close client on exit
    try:
        client.close()
    except Exception as e:
        sys.exit(app.exec())
