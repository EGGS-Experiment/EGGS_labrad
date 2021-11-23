import os
import time
import datetime as datetime

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.cryovac_clients.niops03_gui import niops03_gui

class niops03_client(object):
    name = 'NIOPS03 Client'

    def __init__(self, reactor, parent=None):
        self.gui = niops03_gui()
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
        self.niops = self.cxn.niops03_server

        # get polling time
        # yield self.reg.cd(['Clients', self.name])
        # self.poll_time = yield float(self.reg.get('poll_time'))
        self.poll_time = 1.0

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

        #create and start loop to poll server for temperature
        self.poll_loop = LoopingCall(self.poll)
        from twisted.internet.reactor import callLater
        callLater(1.0, self.start_polling)

    #@inlineCallbacks
    def initializeGUI(self):
        #connect signals to slots
        self.gui.niops_lockswitch.toggled.connect(lambda: self.lock_niops())
        self.gui.niops_power.toggled.connect(lambda: self.toggle_niops())
        self.gui.niops_record.toggled.connect(lambda: self.record_pressure())

        #start up data

    #Slot functions
    @inlineCallbacks
    def record_pressure(self):
        """
        Creates a new dataset to record pressure and tells polling loop
        to add data to data vault
        """
        self.recording = self.gui.niops_record.isChecked()
        if self.recording == True:
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
            yield self.dv.new('NIOPS03 Pump', [('Elapsed time', 't')], \
                                       [('Ion Pump', 'Pressure', 'mbar')], context=self.c_record)

    @inlineCallbacks
    def toggle_niops(self):
        """
        Sets ion pump power on or off
        """
        power_status = self.gui.niops_power.isChecked()
        yield self.niops.toggle_ip(power_status)

    def lock_niops(self):
        """
        Locks power status of ion pump
        """
        lock_status = self.gui.niops_lockswitch.isChecked()
        self.gui.niops_voltage.setEnabled(lock_status)
        self.gui.niops_power.setEnabled(lock_status)

    #Polling functions
    def start_polling(self):
        self.poll_loop.start(self.poll_time)

    def stop_polling(self):
        self.poll_loop.stop()

    @inlineCallbacks
    def poll(self):
        pressure = yield self.niops.ip_pressure()
        self.gui.niops_pressure_display.setText(str(pressure))
        if self.gui.niops_power.isChecked():
            workingtime = yield self.niops.working_time()
            workingtime = workingtime[0]
            workingtime_text = str(workingtime[0]) + ':' + str(workingtime[1])
            self.gui.niops_workingtime_display.setText(workingtime_text)
        if self.recording == True:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, pressure, context=self.c_record)

    def closeEvent(self, event):
        self.cxn.disconnect()
        self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(niops03_client)
