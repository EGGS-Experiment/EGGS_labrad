"""
Base class for building PyQt5 GUI clients for LabRAD
"""

#imports
import os
import sys
import time
import datetime as datetime

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from PyQt5.QtWidgets import QMainWindow


__all__ = ["GUIClient", "GUITabClient"]

class GUIClient(object):
    """
    Creates a client from a single GUI.
    """
    name = None
    poll_time = None
    gui = None

    def __init__(self, reactor, parent=None):
        self.reactor = reactor
        self._connectLabrad()
        self.initializeGUI()

    # Setup functions
    @inlineCallbacks
    def _connectLabrad(self):
        """
        Creates an asynchronous connection to pump servers
        and relevant labrad servers
        """
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync('localhost', name=self.name)

        # ensure base servers are online
        try:
            self.reg = self.cxn.registry
            self.dv = self.cxn.data_vault
        except Exception as e:
            print(e)
            raise

        # get polling time
        if not self.poll_time:
            yield self.reg.cd(['Clients', self.name])
            self.poll_time = yield float(self.reg.get('poll_time'))

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

        # create loop to poll server for data
        self.poll_loop = LoopingCall(self.poll)

    # Polling functions
    def start_polling(self):
        self.poll_loop.start(self.poll_time)

    def stop_polling(self):
        self.poll_loop.stop()

    def closeEvent(self, event):
        self.reactor.stop()

    def connectLabrad(self):
        """
        To be subclassed.
        Should be used to get necessary servers and do other labrad stuff.
        """

    def initializeGUI(self):
        """
        To be subclassed.
        Called after we connect to labrad.
        Should be used to connect GUI signals to slots.
        """

    @inlineCallbacks
    def poll(self):
        """
        To be subclassed.
        Polling loop that runs continuously in the background to get data from server.
        """


class GUITabClient(QMainWindow):

    name = None