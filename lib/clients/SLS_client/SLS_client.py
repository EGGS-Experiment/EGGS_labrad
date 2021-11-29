import os
import time

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.SLS_client.SLS_gui import SLS_gui

class SLS_client(SLS_gui):

    name = 'SLS Client'
    poll_time = 2.0

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.reactor = reactor
        self.connect()
        self.initializeGUI()

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad.
        """
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        try:
            self.sls = yield self.cxn.sls_server
        except Exception as e:
            print(e)
            raise

        return self.cxn

    #@inlineCallbacks
    def initializeGUI(self):
        #connect signals to slots
        # self.twistorr_lockswitch.toggled.connect(lambda: self.lock_twistorr())
        # self.twistorr_power.toggled.connect(lambda: self.toggle_twistorr())
        # self.twistorr_record.toggled.connect(lambda: self.record_pressure())
        #self.sls = self.cxn.artiq_server
        #start up data
        self.gui.setupUi()


    def closeEvent(self, x):
        self.cxn.disconnect()
        self.reactor.stop()

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(SLS_client)
