import os, socket

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from EGGS_labrad.lib.clients.twistorr_client.twistorr_gui import twistorr_gui

from common.lib.clients.connection import connection

class twistorr_client(QWidget):

    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, parent=None):
        super(twistorr_client, self).__init__()
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
        Creates an asynchronous connection to Twistorr server
        and relevant labrad servers
        """
        #from labrad.wrappers import connectAsync
        #self.cxn = yield connectAsync('localhost', name = 'Twistorr 74 Client', password = self.LABRADPASSWORD)
        self.cxn = connection(name = 'Twistorr 74 Client')
        yield self.cxn.connect()
        self.context = yield self.cxn.context()
        self.reg = yield self.cxn.get_server('Registry')
        self.dv = yield self.cxn.get_server('Data Vault')
        #self.ls = yield self.cxn.twistorr_74_server

        # get polling time
        yield self.reg.cd(['Clients', 'Twistorr 74 Client'])
        self.poll_time = yield self.reg.get('poll_time')
        self.poll_time = float(self.poll_time)

        # set recording stuff
        self.c_temp = self.cxn.context()
        self.recording = False

    #@inlineCallbacks
    def initializeGUI(self):
        #initialize main GUI
        layout = QGridLayout()
        self.gui = twistorr_gui(parent = self)
        layout.addWidget(self.gui)
        self.setLayout(layout)
        self.setWindowTitle('Twistorr 74 Client')

        #connect signals to slots
            #lock heater settings
        self.gui.heatAll_lockswitch.toggled.connect(lambda: self.lock_heaters())

            #mode changed
        self.gui.heat1_mode.currentIndexChanged.connect(lambda: self.heater_mode_changed(chan = 1))

        #start up data

    #Slot functions
    @inlineCallbacks
    def record_temp(self):
        """

        """


    def closeEvent(self, event):
        self.reactor.stop()

if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    twistorr_interface = twistorr_client(reactor)
    twistorr_interface.show()
    reactor.run()
