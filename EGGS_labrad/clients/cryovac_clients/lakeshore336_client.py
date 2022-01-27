import time
from datetime import datetime
from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients.cryovac_clients.lakeshore336_gui import lakeshore336_gui


class lakeshore336_client(lakeshore336_gui):

    name = 'Lakeshore336 Client'
    TEMPERATUREID = 194538

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.gui.setupUi()
        self.reactor = reactor
        self.servers = ['Lakeshore336 Server', 'Data Vault']
        # initialization sequence
        d = self.connect()
        d.addCallback(self.initData)
        d.addCallback(self.initializeGUI)


    # SETUP
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad.
        """
        # create labrad connection
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        # check that required servers are online
        try:
            self.dv = yield self.cxn.data_vault
            self.ls = yield self.cxn.lakeshore336_server
            self.reg = yield self.cxn.registry
        except Exception as e:
            print('Required servers not connected, disabling widget.')
            self.setEnabled(False)

        # connect to signals
            # device parameters
        yield self.ls.signal__temperature_update(self.TEMPERATUREID)
        yield self.ls.addListener(listener=self.updateTemperature, source=None, ID=self.TEMPERATUREID)
            # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 111398, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=111398)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 111397, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=111397)

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # start device polling
        poll_params = yield self.ls.polling()
        # only start polling if not started
        if not poll_params[0]:
            yield self.ls.polling(True, 5.0)

        return self.cxn

    @inlineCallbacks
    def initData(self, cxn):
        """
        Get startup data from servers and show on GUI.
        """
        # setup
        res1, max_curr1 = yield self.ls.heater_setup(1)
        self.gui.heat1_res.setCurrentIndex(res1-1)
        self.gui.heat1_curr.setValue(max_curr1)
        res2, max_curr2 = yield self.ls.heater_setup(2)
        self.gui.heat2_res.setCurrentIndex(res2 - 1)
        self.gui.heat2_curr.setValue(max_curr2)
        # mode
        mode1, in1 = yield self.ls.heater_mode(1)
        self.gui.heat1_mode.setCurrentIndex(mode1)
        self.gui.heat1_in.setCurrentIndex(in1)
        mode2, in2 = yield self.ls.heater_mode(2)
        self.gui.heat2_mode.setCurrentIndex(mode2)
        self.gui.heat2_in.setCurrentIndex(in2)
        # range
        range1 = yield self.ls.heater_range(1)
        self.gui.heat1_range.setCurrentIndex(range1)
        range2 = yield self.ls.heater_range(2)
        self.gui.heat2_range.setCurrentIndex(range2)
        # power
        pow1 = yield self.ls.heater_power(1)
        self.gui.heat1_p1.setValue(pow1)
        pow2 = yield self.ls.heater_power(2)
        self.gui.heat2_p1.setValue(pow2)
        return cxn

    def initializeGUI(self, cxn):
        """
        Connect signals to slots and other initializations.
        """
        # temperature
        self.gui.tempAll_record.clicked.connect(lambda status: self.record_temp(status))
        # heaters
            # lockswitch
        self.gui.heatAll_lockswitch.toggled.connect(lambda status: self.lock_heaters(status))
        self.gui.heatAll_lockswitch.setChecked(False)
            # setup
        self.gui.heat1_res.currentIndexChanged.connect(lambda res, max_curr=self.gui.heat1_curr.value(): self.ls.heater_setup(1, res + 1, max_curr))
        self.gui.heat1_curr.valueChanged.connect(lambda max_curr, res=self.gui.heat1_res.currentIndex(): self.ls.heater_setup(1, res + 1, max_curr))
        self.gui.heat2_res.currentIndexChanged.connect(lambda res, max_curr=self.gui.heat2_curr.value(): self.ls.heater_setup(2, res + 1, max_curr))
        self.gui.heat2_curr.valueChanged.connect(lambda max_curr, res=self.gui.heat2_res.currentIndex(): self.ls.heater_setup(2, res + 1, max_curr))
            # mode
        self.gui.heat1_mode.currentIndexChanged.connect(lambda mode, in_diode=self.gui.heat1_in.currentIndex(): self.ls.heater_mode(1, mode + 1, in_diode))
        self.gui.heat1_in.currentIndexChanged.connect(lambda in_diode, mode=self.gui.heat1_mode.currentIndex(): self.ls.heater_mode(1, mode + 1, in_diode))
        self.gui.heat2_mode.currentIndexChanged.connect(lambda mode, in_diode=self.gui.heat2_in.currentIndex(): self.ls.heater_mode(2, mode + 1, in_diode))
        self.gui.heat2_in.currentIndexChanged.connect(lambda in_diode, mode=self.gui.heat2_mode.currentIndex(): self.ls.heater_mode(2, mode + 1, in_diode))
            # range
        self.gui.heat1_range.currentIndexChanged.connect(lambda level: self.ls.heater_range(1, level))
        self.gui.heat2_range.currentIndexChanged.connect(lambda level: self.ls.heater_range(2, level))
            # current
        self.gui.heat1_p1.valueChanged.connect(lambda value: self.ls.heater_power(1, value))
        self.gui.heat2_p1.valueChanged.connect(lambda value: self.ls.heater_power(2, value))
        return cxn


    # SIGNALS
    @inlineCallbacks
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' reconnected, enabling widget.')
            # get latest values
            yield self.initData(self.cxn)
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' disconnected, disabling widget.')
            self.setEnabled(False)


    # SLOTS
    @inlineCallbacks
    def updateTemperature(self, c, temp):
        self.gui.temp1.setText('{:.4f}'.format(temp[0]))
        self.gui.temp2.setText('{:.4f}'.format(temp[1]))
        self.gui.temp3.setText('{:.4f}'.format(temp[2]))
        self.gui.temp4.setText('{:.4f}'.format(temp[3]))
        if self.recording == True:
            yield self.dv.add(time.time() - self.starttime, temp[0], temp[1], temp[2], temp[3], context=self.c_record)

    @inlineCallbacks
    def record_temp(self, status):
        """
        Creates a new dataset to record temperature and
        tells polling loop to add data to data vault.
        """
        # set up datavault
        self.recording = status
        if self.recording == True:
            self.starttime = time.time()
            date = datetime.now()
            year = str(date.year)
            month = '{:02d}'.format(date.month)
            trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
            trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(self.name, date.hour, date.minute)
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
            yield self.dv.new('Lakeshore 336 Temperature Controller', [('Elapsed time', 't')],
                                       [('Diode 1', 'Temperature', 'K'), ('Diode 2', 'Temperature', 'K'),
                                        ('Diode 3', 'Temperature', 'K'), ('Diode 4', 'Temperature', 'K')], context=self.c_record)

    def lock_heaters(self, status):
        """
        Locks heater updating.
        """
        status = not status
        # heater 1
        self.gui.heat1_mode.setEnabled(status)
        self.gui.heat1_in.setEnabled(status)
        self.gui.heat1_res.setEnabled(status)
        self.gui.heat1_curr.setEnabled(status)
        self.gui.heat1_range.setEnabled(status)
        self.gui.heat1_p1.setEnabled(status)
        self.gui.heat1_set.setEnabled(status)
        self.gui.heat1_mode.setEnabled(status)

        # heater 2
        self.gui.heat2_in.setEnabled(status)
        self.gui.heat2_res.setEnabled(status)
        self.gui.heat2_curr.setEnabled(status)
        self.gui.heat2_range.setEnabled(status)
        self.gui.heat2_p1.setEnabled(status)
        self.gui.heat2_set.setEnabled(status)

    @inlineCallbacks
    def heater_setup(self, chan, res, max_curr):
        """
        Set up the heater.
        """
        yield self.ls.heater_setup(chan, res, max_curr)

    @inlineCallbacks
    def heater_mode(self, chan, mode, input):
        """
        Set the heater mode.
        """
        yield self.ls.heater_mode(chan, mode, input)

    @inlineCallbacks
    def heater_range(self, chan, range):
        """
        Set the heater range.
        """
        yield self.ls.heater_range(chan, range)

    @inlineCallbacks
    def heater_power(self, chan, curr):
        """
        Set the heater power.
        """
        yield self.ls.heater_power(chan, curr)


    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(lakeshore336_client)
