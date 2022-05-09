from time import time
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.cryovac_clients.lakeshore336_gui import lakeshore336_gui


class lakeshore336_client(GUIClient):

    name = 'Lakeshore336 Client'
    TEMPERATUREID = 194538
    servers = {'ls': 'Lakeshore336 Server', 'dv': 'Data Vault'}

    def getgui(self):
        if self.gui is None:
            self.gui = lakeshore336_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to signals
        yield self.ls.signal__temperature_update(self.TEMPERATUREID)
        yield self.ls.addListener(listener=self.updateTemperature, source=None, ID=self.TEMPERATUREID)
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # start device polling
        poll_params = yield self.ls.polling()
        # only start polling if not started
        if not poll_params[0]:
            yield self.ls.polling(True, 5.0)

    @inlineCallbacks
    def initData(self):
        # setup
        res1, max_curr1 = yield self.ls.heater_setup(1)
        self.gui.heat1_res.setCurrentIndex(res1 - 1)
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

    def initGUI(self):
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


    # SLOTS
    @inlineCallbacks
    def updateTemperature(self, c, temp):
        self.gui.temp1.setText('{:.4f}'.format(temp[0]))
        self.gui.temp2.setText('{:.4f}'.format(temp[1]))
        self.gui.temp3.setText('{:.4f}'.format(temp[2]))
        self.gui.temp4.setText('{:.4f}'.format(temp[3]))
        if self.recording:
            yield self.dv.add(time() - self.starttime, temp[0], temp[1], temp[2], temp[3], context=self.c_record)

    @inlineCallbacks
    def record_temp(self, status):
        """
        Creates a new dataset to record temperature and
        tells polling loop to add data to data vault.
        """
        # set up datavault
        self.recording = status
        if self.recording:
            self.starttime = time()
            trunk = createTrunk(self.name)
            yield self.dv.cd(trunk, True, context=self.c_record)
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
        self.gui.heat2_mode.setEnabled(status)
        self.gui.heat2_in.setEnabled(status)
        self.gui.heat2_res.setEnabled(status)
        self.gui.heat2_curr.setEnabled(status)
        self.gui.heat2_range.setEnabled(status)
        self.gui.heat2_p1.setEnabled(status)
        self.gui.heat2_set.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(lakeshore336_client)
