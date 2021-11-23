import os
import time
import datetime as datetime

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.cryovac_clients.twistorr74_gui import twistorr74_gui

class twistorr74_client(object):
    name = 'Twistorr74 Client'

    def __init__(self, reactor, parent=None):
        self.gui = twistorr74_gui()
        self.reactor = reactor
        self.connect()
        self.initializeGUI()

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to pump servers
        and relevant labrad servers
        """
        import os
        LABRADHOST = os.environ['LABRADHOST']
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(LABRADHOST, name=self.name)
        try:
            self.reg = self.cxn.registry
            self.dv = self.cxn.data_vault
            self.tt = self.cxn.twistorr74_server
        except Exception as e:
            print(e)
            raise

        # get polling time
        # yield self.reg.cd(['Clients', self.name])
        # self.poll_time = yield float(self.reg.get('poll_time'))
        self.poll_time = 2.0

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
        self.recording = self.gui.twistorr_record.isChecked()
        if self.recording:
            self.starttime = time.time()
            date = datetime.datetime.now()
            year = str(date.year)
            month = '%02d' % date.month  # Padded with a zero if one digit
            day = '%02d' % date.day  # Padded with a zero if one digit
            hour = '%02d' % date.hour  # Padded with a zero if one digit
            minute = '%02d' % date.minute  # Padded with a zero if one digit

            trunk1 = year + '_' + month + '_' + day
            trunk2 = self.name + '_' + hour + ':' + minute
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
            yield self.dv.new('Twistorr 74 Pump Controller', [('Elapsed time', 't')], [('Pump Pressure', 'Pressure', 'mbar')], context=self.c_record)

    @inlineCallbacks
    def toggle_twistorr(self):
        """
        Sets pump power on or off
        """
        power_status = self.gui.twistorr_power.isChecked()
        yield self.tt.toggle(power_status)

    def lock_twistorr(self):
        """
        Locks power status of pump
        """
        lock_status = self.gui.twistorr_lockswitch.isChecked()
        self.gui.twistorr_power.setEnabled(lock_status)

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

    def close(self):
        self.cxn.disconnect()
        self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(twistorr74_client)
