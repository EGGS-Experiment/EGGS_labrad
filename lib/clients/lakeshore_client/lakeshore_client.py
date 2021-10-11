import os, socket

from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QGroupBox, QDialog, QVBoxLayout, QGridLayout
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet.task import LoopingCall
from .lakeshore_gui import lakeshore_gui

class lakeshore_client(QWidget):

    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, parent=None):
        super(lakeshore_client, self).__init__()
        self.reactor = reactor
        self.connect()
        self.initializeGUI()
        self.set_signal_listeners()

        #create and start loop to poll server for temperature
        self.temp_loop = LoopingCall(self.poll)
        self.start_polling()

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to lakeshore server
        and relevant labrad servers
        """
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync('localhost', name = 'Lakeshore 336 Client', password = self.password)
        self.reg = yield self.cxn.registry
        self.ls = yield self.cxn.lakeshore_336_server

        # get polling time
        yield self.reg.cd(['Clients', 'Lakeshore 336 Client'])
        self.poll_time = yield self.registry.get('poll_time')

    @inlineCallbacks
    def initializeGUI(self):
        #set layout
        layout = QGridLayout()
        qBox = QGroupBox('Single Channel Software Lock')
        subLayout = QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        #initialize main GUI
        self.gui = lakeshore_gui

        #connect signals to slots
        #todo: connect

    #Slot functions
    #todo: write them
    @inlineCallbacks
    def lowRailChanged(self, value, chan):
        yield self.lock_server.set_low_rail(value, chan)

    #Polling functions
    def start_polling(self):
        self.temp_loop.start(self.poll_time)

    def stop_polling(self):
        self.temp_loop.stop()

    def poll(self):
        temp = yield self.ls.read_temperature('0')
        self.gui.temp1.setText(str(temp[0]))
        self.gui.temp2.setText(str(temp[1]))
        self.gui.temp3.setText(str(temp[2]))
        self.gui.temp4.setText(str(temp[3]))
        if self.heat1_mode.currentText() is not 'Off':
            curr1 = yield self.ls.get_heater_output(1)
            self.gui.heat1.setText(str(curr1))
        if self.heat2_mode.currentText() is not 'Off':
            curr2 = yield self.ls.get_heater_output(2)
            self.gui.heat2.setText(str(temp[0]))
        #todo: heater?


if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    software_lock = software_laser_lock_client(reactor)
    software_lock.show()
    reactor.run()
