import os

from labrad.wrappers import connectAsync

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.lib.clients.trap_clients.rf_gui import rf_gui


class rf_client(object):
    name = 'RF Client'

    def __init__(self, reactor, parent=None):
        self.gui = rf_gui()
        self.reactor = reactor
        self.connect()
        self.initializeGUI()

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad
        """
        import os
        LABRADHOST = os.environ['LABRADHOST']
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        self.reg = self.cxn.registry
        self.dv = self.cxn.data_vault
        self.rf = self.cxn.rf_server
        #todo: ensure device is selected

    #@inlineCallbacks
    def initializeGUI(self):
        #connect signals to slots
        self.gui.niops_lockswitch.toggled.connect(lambda: self.lock_niops())
        self.gui.niops_power.toggled.connect(lambda: self.toggle_niops())
        self.gui.niops_record.toggled.connect(lambda: self.record_pressure())

        #start up data

    @inlineCallbacks
    def toggle_niops(self):
        """
        Sets ion pump power on or off
        """
        power_status = self.gui.niops_power.isChecked()
        yield self.niops.toggle_ip(power_status)

    def lock(self):
        """
        Locks power status of ion pump
        """
        lock_status = self.gui.niops_lockswitch.isChecked()
        self.gui.niops_voltage.setEnabled(lock_status)
        self.gui.niops_power.setEnabled(lock_status)

    def closeEvent(self, event):
        self.reactor.stop()

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(rf_client)
