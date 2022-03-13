"""
Contains stuff useful for LabRAD clients.
"""

__all__ = ["runGUI", "runClient"]


# imports
import os
from PyQt5.QtWidgets import QApplication


# run functions
def runGUI(client, *args, **kwargs):
    """
    Runs a LabRAD GUI file written using PyQt5
    """
    # widgets require a QApplication to run
    app = QApplication([])
    # instantiate gui
    gui = client(*args, **kwargs)
    # set up UI if needed
    try:
        gui.setupUi()
    except Exception as e:
        print('No need to setup UI')
    # run GUI file
    gui.show()
    os._exit(app.exec())


def runClient(client, *args, **kwargs):
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
    client_tmp = client(reactor, *args, **kwargs)
    # show client
    if hasattr(client_tmp, 'show'):
        client_tmp.show()
    elif hasattr(client_tmp, 'gui'):
        gui_tmp = client_tmp.gui
        if hasattr(gui_tmp, 'show'):
            client_tmp.gui.show()
    # start reactor
    reactor.callWhenRunning(app.exec)
    reactor.addSystemEventTrigger('after', 'shutdown', client_tmp.close)
    reactor.runReturn()
    # close client on exit
    try:
        client_tmp.close()
    except Exception as e:
        print(e)
