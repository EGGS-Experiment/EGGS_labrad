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
        self.dv = yield.self.cxn.data_vault
        self.ls = yield self.cxn.lakeshore_336_server

        # get polling time
        yield self.reg.cd(['Clients', 'Lakeshore 336 Client'])
        self.poll_time = yield float(self.registry.get('poll_time'))

        # set recording stuff
        self.c_temp = self.cxn.context()
        self.recording = False

    @inlineCallbacks
    def initializeGUI(self):
        #set layout
        layout = QGridLayout()
        qBox = QGroupBox('Lakeshore 336')
        subLayout = QGridLayout()
        qBox.setLayout(subLayout)
        layout.addWidget(qBox, 0, 0)

        #initialize main GUI
        self.gui = lakeshore_gui()

        #connect signals to slots
            #record temperature
        self.gui.tempAll_record.toggled.connect()

            #update heater setting
        self.gui.heat1_update.toggled.connect(self.update_heater(1))
        self.gui.heat2_update.toggled.connect(self.update_heater(2))

            #lock heater settings
        self.gui.lockswitch.toggled.connect(self.lock_heaters)

            #mode changed
        self.gui.heat1_mode.activated.connect(self.heater_mode_changed(1))
        self.gui.heat1_mode.activated.connect(self.heater_mode_changed(2))


    #Slot functions
    @inlineCallbacks
    def record_temp(self):
        """
        Creates a new dataset to record temperature and tells polling loop
        to add data to data vault
        """
        self.recording = self.gui.tempAll_record.isChecked()
        if self.gui.recording == True:
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context = self.c_temp)
            yield self.dv.new('Lakeshore 336 Temperature Controller', [('Elapsed time', 't')], \
                                       [('Diode 1', 'Temperature', 'K'), ('Diode 2', 'Temperature', 'K'), \
                                        ('Diode 3', 'Temperature', 'K'), ('Diode 4', 'Temperature', 'K')], context=self.c_temp)
        #todo: set colors of button?

    @inlineCallbacks
    def update_heater(self, chan):
        """
        fd
        """
        #todo: check mode
        #todo: config
        #todo: setup
        #todo: set param

    @inlineCallbacks
    def lock_heaters(self):
        """
        Locks heater updating
        """
        lock_status = self.gui.heatAll_lockswitch.isChecked()
        self.gui.heat1_update.setEnabled(lock_status)

    @inlineCallbacks
    def heater_mode_changed(self, chan, mode):
        """
        fd
        """
        if mode == 0:
            self.gui.heat1_in.setEnabled(False)
            self.gui.heat1_curr.setEnabled(False)
            self.gui.heat1_res.setEnabled(False)
            self.gui.heat1_set.setEnabled(False)
            self.gui.heat1_range.setEnabled(False)
            self.gui.heat1_p1.setEnabled(False)
            self.gui.heat1_p2.setEnabled(False)
            self.gui.heat1_p3.setEnabled(False)
        elif mode == 1:
            self.gui.heat1_in.setEnabled(True)
            self.gui.heat1_curr.setEnabled(True)
            self.gui.heat1_res.setEnabled(True)
            self.gui.heat1_set.setEnabled(True)
            self.gui.heat1_range.setEnabled(True)
            self.gui.heat1_p1.setEnabled(True)
            self.gui.heat1_p2.setEnabled(False)
            self.gui.heat1_p3.setEnabled(False)
            self.gui.heat1_p1_label.setText('P-I-D')
            self.gui.heat1_p2_label.setText('')
            self.gui.heat1_p3_label.setText('')
            self.heat1_p1.setDecimals(0)
            self.heat1_p1.setSingleStep(1)
            self.heat1_p1.setRange(0, 2)
        elif mode == 2:
            self.gui.heat1_in.setEnabled(True)
            self.gui.heat1_curr.setEnabled(True)
            self.gui.heat1_res.setEnabled(True)
            self.gui.heat1_set.setEnabled(True)
            self.gui.heat1_range.setEnabled(True)
            self.gui.heat1_p1.setEnabled(True)
            self.gui.heat1_p2.setEnabled(True)
            self.gui.heat1_p3.setEnabled(True)
            self.gui.heat1_p1_label.setText('P')
            self.gui.heat1_p2_label.setText('I')
            self.gui.heat1_p3_label.setText('D')
            self.heat1_p1.setDecimals(1)
            self.heat1_p1.setSingleStep(1e-1)
            self.heat1_p1.setRange(0, 1000)
        elif mode == 3:
            self.gui.heat1_in.setEnabled(True)
            self.gui.heat1_curr.setEnabled(True)
            self.gui.heat1_res.setEnabled(True)
            self.gui.heat1_set.setEnabled(True)
            self.gui.heat1_range.setEnabled(True)
            self.gui.heat1_p1.setEnabled(True)
            self.gui.heat1_p2.setEnabled(False)
            self.gui.heat1_p3.setEnabled(False)
            self.gui.heat1_p1_label.setText('Current (A)')
            self.gui.heat1_p2_label.setText('')
            self.gui.heat1_p3_label.setText('')
            self.heat1_p1.setDecimals(2)
            self.heat1_p1.setSingleStep(1e-2)
            self.heat1_p1.setRange(0, self.gui.heat1_curr.value())

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
        if self.recording == True:
            yield self.dv.add(elapsedtime, temp[0], temp[1], temp[2], temp[3], context=self.c_temp)
        if self.heat1_mode.currentText() is not 'Off':
            curr1 = yield self.ls.get_heater_output(1)
            self.gui.heat1.setText(str(curr1))
        if self.heat2_mode.currentText() is not 'Off':
            curr2 = yield self.ls.get_heater_output(2)
            self.gui.heat2.setText(str(curr2))

if __name__ == "__main__":
    a = QApplication([])
    import qt5reactor
    qt5reactor.install()
    from twisted.internet import reactor
    software_lock = lakeshore_client(reactor)
    software_lock.show()
    reactor.run()
