import os
import time

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.SLS_client.sls_gui import SLS_gui

class SLS_client(SLS_gui):

    name = 'SLS Client'
    poll_time = 2.0

    def __init__(self, reactor, parent=None):
        self.gui = SLS_gui()
        self.reactor = reactor
        self.connect()
        self.initializeGUI()

        #create and start loop to poll server for temperature
        # self.temp_loop = LoopingCall(self.poll)
        # self.start_polling()

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to pump servers
        and relevant labrad servers
        """
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync('localhost', name='SLS Client')

        #ensure all necessary servers are online
        try:
            self.reg = self.cxn.registry
            self.dv = self.cxn.data_vault
            self.tt = self.cxn.twistorr74_server
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

        #create and start loop to poll server for temperature
        self.poll_loop = LoopingCall(self.poll)
        from twisted.internet.reactor import callLater
        callLater(2.0, self.start_polling)

    #@inlineCallbacks
    def initializeGUI(self):
        #connect signals to slots
        # self.twistorr_lockswitch.toggled.connect(lambda: self.lock_twistorr())
        # self.twistorr_power.toggled.connect(lambda: self.toggle_twistorr())
        # self.twistorr_record.toggled.connect(lambda: self.record_pressure())

        #start up data
        self.setupUi()

    #Slot functions
    @inlineCallbacks
    def record_pressure(self):
        """
        Creates a new dataset to record pressure and tells polling loop
        to add data to data vault
        """
        self.recording = self.press_record.isChecked()
        if self.recording == True:
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context = self.c_press)
            yield self.dv.new('Twistorr 74 Pump Controller', [('Elapsed time', 't')], [('Pump Pressure', 'Pressure', 'mbar')], context=self.c_press)

    @inlineCallbacks
    def toggle_twistorr(self):
        """
        Sets pump power on or off
        """
        power_status = self.twistorr_power.isChecked()
        yield self.pump.toggle(power_status)

    def lock_twistorr(self):
        """
        Locks power status of pump
        """
        lock_status = self.twistorr_lockswitch.isChecked()
        self.twistorr_power.setEnabled(lock_status)

    #Polling functions
    def start_polling(self):
        self.poll_loop.start(self.poll_time)

    def stop_polling(self):
        self.poll_loop.stop()

    @inlineCallbacks
    def poll(self):
        pressure = yield self.tt.read_pressure()
        self.gui.twistorr_display.setText(str(pressure))
        if self.recording == True:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, pressure, context=self.c_record)

    def closeEvent(self, event):
        self.reactor.stop()

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(SLS_client)
