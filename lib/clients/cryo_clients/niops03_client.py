import os

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from EGGS_labrad.lib.clients.cryo_clients.niops03_gui import niops03_gui

from EGGS_labrad.lib.clients.connection import connection

class niops03_client(niops03_gui):
    name = 'NIOPS03 Client'
    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, parent=None):
        super(niops03_client, self).__init__()
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
        Creates an asynchronous connection to labrad
        """
        #from labrad.wrappers import connectAsync
        #self.cxn = yield connectAsync('localhost', name = 'NIOPS03 Client', password = self.LABRADPASSWORD)
        self.cxn = connection(name = self.name)
        yield self.cxn.connect()
        self.context = yield self.cxn.context()
        self.reg = yield self.cxn.get_server('Registry')
        self.dv = yield self.cxn.get_server('Data Vault')
        #self.niops = yield self.cxn.get_server('niops03_server')

        # get polling time
        yield self.reg.cd(['Clients', self.name])
        self.poll_time = yield float(self.reg.get('poll_time'))

        # set recording stuff
        self.c_press = self.cxn.context()
        self.recording = False

    #@inlineCallbacks
    def initializeGUI(self):
        #connect signals to slots
        self.niops_lockswitch.toggled.connect(lambda: self.lock_niops())
        self.niops_power.toggled.connect(lambda: self.toggle_niops())
        self.niops_record.toggled.connect(lambda: self.record_pressure())

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
            yield self.dv.new('NIOPS 03 Pump', [('Elapsed time', 't')], [('IP Pressure', 'Pressure', 'mbar')], context=self.c_press)

    @inlineCallbacks
    def toggle_niops(self):
        """
        Sets ion pump power on or off
        """
        power_status = self.niops_power.isChecked()
        yield self.niops.toggle_ip(power_status)

    def lock_niops(self):
        """
        Locks power status of ion pump
        """
        lock_status = self.niops_lockswitch.isChecked()
        self.niops_voltage.setEnabled(lock_status)
        self.niops_power.setEnabled(lock_status)

    #Polling functions
    def start_polling(self):
        self.press_loop.start(self.poll_time)

    def stop_polling(self):
        self.press_loop.stop()

    def poll(self):
        pressure = yield self.niops.get_pressure_ip()
        if self.niops_power.isChecked():
            workingtime = yield self.niops.working_time()
            time = str(workingtime[0]) + ':' + str(workingtime[1])
            self.niops_workingtime_display.setText(time)
        self.press_display.setText(str(pressure))
        if self.recording == True:
            yield self.dv.add(elapsedtime, pressure, context=self.c_press)

    def closeEvent(self, event):
        self.reactor.stop()

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(niops03_client)
