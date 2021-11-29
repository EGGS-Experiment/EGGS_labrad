import os
import time
import datetime as datetime

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.cryovac_clients.lakeshore336_gui import lakeshore336_gui

from PyQt5.QtGui import QFont


class lakeshore336_client(lakeshore336_gui):

    name = 'Lakeshore336 Client'

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.gui.setupUi()
        self.reactor = reactor
        self.connect()
        self.initializeGUI()

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to lakeshore server
        and relevant labrad servers
        """
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        #check that required servers are online
        try:
            self.dv = yield self.cxn.data_vault
            self.ls = yield self.cxn.lakeshore336_server
            self.reg = yield self.cxn.registry
        except Exception as e:
            print(e)
            raise

        # get polling time
        #yield self.reg.cd(['Clients', self.name])
        #self.poll_time = yield self.reg.get('poll_time')
        #self.poll_time = float(self.poll_time)
        self.poll_time = 1.0

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

        #create and start loop to poll server for temperature
        self.poll_loop = LoopingCall(self.poll)
        self.reactor.callLater(1.0, self.start_polling)

    #@inlineCallbacks
    def initializeGUI(self):
        #connect signals to slots
            #record temperature
        self.gui.tempAll_record.toggled.connect(lambda status: self.record_temp(status))
            #update heater setting
        #self.gui.heat1_update.toggled.connect(lambda: self.update_heater(chan = 1))
        #self.gui.heat2_update.toggled.connect(lambda: self.update_heater(chan = 2))
            #lock heater settings
        self.gui.heatAll_lockswitch.toggled.connect(lambda status: self.lock_heaters(status))
            #mode changed
        self.gui.heat1_mode.currentIndexChanged.connect(lambda mode: self.heater_mode_changed(mode, chan=1))
        self.gui.heat2_mode.currentIndexChanged.connect(lambda mode: self.heater_mode_changed(mode, chan=2))


    #Slot functions
    @inlineCallbacks
    def record_temp(self, status):
        """
        Creates a new dataset to record temperature and tells polling loop
        to add data to data vault
        """
        self.recording = status
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
            yield self.dv.new('Lakeshore 336 Temperature Controller', [('Elapsed time', 't')],
                                       [('Diode 1', 'Temperature', 'K'), ('Diode 2', 'Temperature', 'K'),
                                        ('Diode 3', 'Temperature', 'K'), ('Diode 4', 'Temperature', 'K')], context=self.c_record)

    @inlineCallbacks
    def update_heater(self, chan):
        """
        Sends the heater config and parameters to the lakeshore server
        """
        if chan == 1:
            mode = self.gui.heat1_mode.currentIndex()
            input_channel = self.gui.heat1_in.currentData()
            resistance = self.gui.heat1_res.currentData()
            max_curr = self.gui.heat1_curr.currentData()
            h_range = self.gui.heat1_range.currentData()
            set = self.gui.heat1_set.currentData()
            p1 = self.gui.heat1_p1.currentData()
            if mode == 2:
                p2 = self.gui.heat1_p2.currentData()
                p3 = self.gui.heat1_p3.currentData()
        elif chan == 2:
            mode = self.gui.heat2_mode.currentIndex()
            input_channel = self.gui.heat2_in.currentData()
            resistance = self.gui.heat2_res.currentData()
            max_curr = self.gui.heat2_curr.currentData()
            h_range = self.gui.heat2_range.currentData()
            set = self.gui.heat2_set.currentData()
            p1 = self.gui.heat2_p1.currentData()
            if mode == 2:
                p2 = self.gui.heat2_p2.currentData()
                p3 = self.gui.heat2_p3.currentData()

        yield self.ls.configure_heater(chan, mode, input_channel)
        yield self.ls.setup_heater(chan, resistance, max_curr)
        yield self.ls.set_heater_range(chan, h_range)
        yield self.ls.set_heater_setpoint(chan, set)

        if mode == 1:
            yield self.ls.autotune_heater(chan, input_channel, p1)
        elif mode == 2:
            yield self.ls.autotune_heater(chan, p1, p2, p3)
        elif mode == 3:
            yield self.ls.set_heater_power(chan, p1)

    def lock_heaters(self, status):
        """
        Locks heater updating.
        """
        pass
        #self.gui.heat1_update.setEnabled(lock_status)
        #self.gui.heat2_update.setEnabled(lock_status)

    def heater_mode_changed(self, mode, chan):
        """
        Disables and enables the relevant settings for each mode
        """
        if chan == 1:
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
                self.gui.heat1_p1.setDecimals(0)
                self.gui.heat1_p1.setSingleStep(1)
                self.gui.heat1_p1.setRange(0, 2)
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
                self.gui.heat1_p1.setDecimals(1)
                self.gui.heat1_p1.setSingleStep(1e-1)
                self.gui.heat1_p1.setRange(0, 1000)
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
                self.gui.heat1_p1.setDecimals(2)
                self.gui.heat1_p1.setSingleStep(1e-2)
                self.gui.heat1_p1.setRange(0, self.gui.heat1_curr.value())
        elif chan == 2:
            mode = self.gui.heat2_mode.currentIndex()
            if mode == 0:
                self.gui.heat2_in.setEnabled(False)
                self.gui.heat2_curr.setEnabled(False)
                self.gui.heat2_res.setEnabled(False)
                self.gui.heat2_set.setEnabled(False)
                self.gui.heat2_range.setEnabled(False)
                self.gui.heat2_p1.setEnabled(False)
                self.gui.heat2_p2.setEnabled(False)
                self.gui.heat2_p3.setEnabled(False)
            elif mode == 1:
                self.gui.heat2_in.setEnabled(True)
                self.gui.heat2_curr.setEnabled(True)
                self.gui.heat2_res.setEnabled(True)
                self.gui.heat2_set.setEnabled(True)
                self.gui.heat2_range.setEnabled(True)
                self.gui.heat2_p1.setEnabled(True)
                self.gui.heat2_p2.setEnabled(False)
                self.gui.heat2_p3.setEnabled(False)
                self.gui.heat2_p1_label.setText('P-I-D')
                self.gui.heat2_p2_label.setText('')
                self.gui.heat2_p3_label.setText('')
                self.gui.heat2_p1.setDecimals(0)
                self.gui.heat2_p1.setSingleStep(1)
                self.gui.heat2_p1.setRange(0, 2)
            elif mode == 2:
                self.gui.heat2_in.setEnabled(True)
                self.gui.heat2_curr.setEnabled(True)
                self.gui.heat2_res.setEnabled(True)
                self.gui.heat2_set.setEnabled(True)
                self.gui.heat2_range.setEnabled(True)
                self.gui.heat2_p1.setEnabled(True)
                self.gui.heat2_p2.setEnabled(True)
                self.gui.heat2_p3.setEnabled(True)
                self.gui.heat2_p1_label.setText('P')
                self.gui.heat2_p2_label.setText('I')
                self.gui.heat2_p3_label.setText('D')
                self.gui.heat2_p1.setDecimals(1)
                self.gui.heat2_p1.setSingleStep(1e-1)
                self.gui.heat2_p1.setRange(0, 1000)
            elif mode == 3:
                self.gui.heat2_in.setEnabled(True)
                self.gui.heat2_curr.setEnabled(True)
                self.gui.heat2_res.setEnabled(True)
                self.gui.heat2_set.setEnabled(True)
                self.gui.heat2_range.setEnabled(True)
                self.gui.heat2_p1.setEnabled(True)
                self.gui.heat2_p2.setEnabled(False)
                self.gui.heat2_p3.setEnabled(False)
                self.gui.heat2_p1_label.setText('Current (A)')
                self.gui.heat2_p2_label.setText('')
                self.gui.heat2_p3_label.setText('')
                self.gui.heat2_p1.setDecimals(2)
                self.gui.heat2_p1.setSingleStep(1e-2)
                self.gui.heat2_p1.setRange(0, self.gui.heat1_curr.value())

    #Polling functions
    def start_polling(self):
        self.poll_loop.start(self.poll_time)

    def stop_polling(self):
        self.poll_loop.stop()

    @inlineCallbacks
    def poll(self):
        #get temperature and set diode
        temp = yield self.ls.read_temperature('0')
        self.gui.temp1.setText(str(temp[0]))
        self.gui.temp2.setText(str(temp[1]))
        self.gui.temp3.setText(str(temp[2]))
        self.gui.temp4.setText(str(temp[3]))
        if self.recording == True:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, temp[0], temp[1], temp[2], temp[3], context=self.c_record)
        if self.gui.heat1_mode.currentText() != 'Off':
            curr1 = yield self.ls.get_heater_output(1)
            self.gui.heat1.setText(str(curr1))
        if self.gui.heat2_mode.currentText() != 'Off':
            curr2 = yield self.ls.get_heater_output(2)
            self.gui.heat2.setText(str(curr2))

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(lakeshore336_client)
