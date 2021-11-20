import os

from labrad.wrappers import connectAsync

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.lib.clients.trap_clients.rf_gui import rf_gui

class rf_client(object):
    name = 'RF Client'
    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, parent=None):
        self.gui = rf_gui()
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
        self.cxn = yield connectAsync('localhost', name='RF Client', password=self.LABRADPASSWORD)
        self.context = self.cxn.context()
        self.reg = self.cxn.registry
        self.dv = self.cxn.data_vault
        #self.rf = yield self.cxn.rf_server

        # get polling time
        # yield self.reg.cd(['Clients', self.name])
        # self.poll_time = yield float(self.reg.get('poll_time'))
        self.poll_time = 1.0

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

    #@inlineCallbacks
    def initializeGUI(self):
        #connect signals to slots
        self.gui.twistorr_lockswitch.toggled.connect(lambda: self.lock_twistorr())
        self.gui.twistorr_power.toggled.connect(lambda: self.toggle_twistorr())
        self.gui.twistorr_record.toggled.connect(lambda: self.record_pressure())

        #start up data

    #Slot functions
    @inlineCallbacks
    def record_pressure(self):
        """
        Creates a new dataset to record pressure and tells polling loop
        to add data to data vault
        """
        self.recording = self.press_record.isChecked()
        if self.recording == True:
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_press)
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
        self.press_loop.start(self.poll_time)

    def stop_polling(self):
        self.press_loop.stop()

    def poll(self):
        pressure = yield self.pump.read_pressure()
        self.press_display.setText(str(pressure))
        if self.recording == True:
            yield self.dv.add(elapsedtime, pressure, context=self.c_press)

    def closeEvent(self, event):
        self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(rf_client)
