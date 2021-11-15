"""
Base class for building PyQt5 GUI clients for LabRAD
"""

#imports
import os
import sys

from PyQt5.QtWidgets import QWidget, QMainWindow
from twisted.internet.defer import inlineCallbacks, returnValue


__all__ = ["GUIClient", "GUITabClient"]

class GUIClient(GUI):
    """
    Creates a client from a single GUI
    """

    name = None
    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, parent=None):
        super(GUIClient, self).__init__()
        self.reactor = reactor
        self.connect()
        self.initializeGUI()


    #Subclassed functions
    def initClient(self, **kwargs):
        """
        Initialize Client.

        Called after registering settings and creating a client
        connection to labrad, but before we start serving requests.
        """

    @inlineCallbacks
    def connectServers(self):
        """
        Creates an asynchronous connection to lakeshore server
        and relevant labrad servers
        """

    def closeEvent(self, x):
        self.reactor.stop()

class GUITabClient(QMainWindow):

    name = 'EGGS GUI'
    LABRADPASSWORD = os.environ['LABRADPASSWORD']