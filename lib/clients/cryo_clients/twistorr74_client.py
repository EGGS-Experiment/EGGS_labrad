import os, socket

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from EGGS_labrad.lib.clients.cryo_clients.twistorr74_gui import twistorr74_gui

from EGGS_labrad.lib.clients.connection import connection

class twistorr74_client(QWidget):
    #todo: make connections inheritable
    name = 'Twistorr74 Client'
    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, parent=None):
        super(twistorr74_client, self).__init__()
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
        #from labrad.wrappers import connectAsync
        #self.cxn = yield connectAsync('localhost', name = 'Pump Client', password = self.LABRADPASSWORD)
        self.cxn = connection(name=self.name)
        yield self.cxn.connect()
        self.context = yield self.cxn.context()
        self.reg = yield self.cxn.get_server('Registry')
        self.dv = yield self.cxn.get_server('Data Vault')
        #self.turbo = yield self.cxn.get_server('twistorr_74_server')

        # get polling time
        yield self.reg.cd(['Clients', self.name])
        self.poll_time = yield float(self.reg.get('poll_time'))

        # set recording stuff
        self.c_press = self.cxn.context()
        self.recording = False

    #@inlineCallbacks
    def initializeGUI(self):
        #initialize main GUI
        layout = QGridLayout()
        self.gui = twistorr74_gui(parent = self)
        layout.addWidget(self.gui)
        self.setLayout(layout)
        self.setWindowTitle(self.name)

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
        self.recording = self.gui.press_record.isChecked()
        if self.recording == True:
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context = self.c_press)
            yield self.dv.new('Twistorr 74 Pump Controller', [('Elapsed time', 't')], [('Pump Pressure', 'Pressure', 'mbar')], context=self.c_press)

    @inlineCallbacks
    def toggle_twistorr(self):
        """
        Sets pump power on or off
        """
        power_status = self.gui.twistorr_power.isChecked()
        yield self.pump.toggle(power_status)

    def lock_twistorr(self):
        """
        Locks power status of pump
        """
        lock_status = self.gui.twistorr_lockswitch.isChecked()
        self.gui.twistorr_power.setEnabled(lock_status)

    #Polling functions
    def start_polling(self):
        self.press_loop.start(self.poll_time)

    def stop_polling(self):
        self.press_loop.stop()

    def poll(self):
        pressure = yield self.pump.read_pressure()
        self.gui.press_display.setText(str(pressure))
        if self.recording == True:
            yield self.dv.add(elapsedtime, pressure, context=self.c_press)

    def closeEvent(self, event):
        self.reactor.stop()

if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    twistorr_interface = twistorr74_client(reactor)
    twistorr_interface.show()
    reactor.run()
