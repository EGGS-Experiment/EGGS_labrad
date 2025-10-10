from time import time
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.injection_lock_diode_client.injection_lock_temperature_gui import InjectionLockTemperatureGUI


class InjectionLockTemperatureClient(GUIClient):

    name = 'Injection Lock Temperature Client'

    TOGGLEID =      4651984
    TEMPERATUREID = 4651986
    CURRENTID =     4651985
    LOCKID =        4651987
    servers = {'tec': 'Injection Lock Temperature Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = InjectionLockTemperatureGUI()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        yield self.tec.signal__toggle_update(self.TOGGLEID)
        yield self.tec.addListener(listener=self.updateToggle, source=None, ID=self.TOGGLEID)
        yield self.tec.signal__current_update(self.CURRENTID)
        yield self.tec.addListener(listener=self.updateCurrent, source=None, ID=self.CURRENTID)
        yield self.tec.signal__temperature_update(self.TEMPERATUREID)
        yield self.tec.addListener(listener=self.updateTemperature, source=None, ID=self.TEMPERATUREID)
        yield self.tec.signal__lock_update(self.LOCKID)
        yield self.tec.addListener(listener=self.updateLock, source=None, ID=self.LOCKID)

        # set up recording variables
        self.c_record = self.cxn.context()
        self.recording = False

    @inlineCallbacks
    def initData(self):
        # get data
        status =    yield self.tec.toggle()
        curr =      yield self.tec.current()
        temp =      yield self.tec.temperature()
        lock_set =  yield self.tec.locking_setpoint()
        lock_P =    yield self.tec.locking_p()
        lock_I =    yield self.tec.locking_i()
        lock_D =    yield self.tec.locking_d()

        # set GUI
        self.gui.toggle_button.setChecked(status)
        self.gui.displayCurr.setText(str(curr))
        self.gui.displayTemp.setText(str(temp))
        self.gui.lock_set.setValue(lock_set)
        self.gui.lock_P.setValue(lock_P)
        self.gui.lock_I.setValue(lock_I)
        self.gui.lock_D.setValue(lock_D)

    def initGUI(self):
        # general
        self.gui.toggle_button.clicked.connect(lambda status: self.tec.toggle(status))
        self.gui.record_button.clicked.connect(lambda status: self._record(status))
        self.gui.lock_button.clicked.connect(lambda status: self._lock(status))

        # locking
        self.gui.lock_set.valueChanged.connect(lambda val_set: self.tec.locking_setpoint(val_set))
        self.gui.lock_P.valueChanged.connect(lambda val_p: self.tec.locking_p(val_p))
        self.gui.lock_I.valueChanged.connect(lambda val_i: self.tec.locking_i(val_i))
        self.gui.lock_D.valueChanged.connect(lambda val_d: self.tec.locking_d(val_d))

        # todo: check
        self.gui.lock_button.setChecked(False)
        self.gui.lock_button.click()


    # SLOTS
    @inlineCallbacks
    def _record(self, status):
        """
        Creates a new dataset to record temperature and
        tells polling loop to add data to data vault.
        """
        self.recording = status

        if self.recording:
            self.starttime = time()

            # set up datavault
            trunk = createTrunk(self.name)
            yield self.dv.cd(trunk, True, context=self.c_record)
            yield self.dv.new(
                'AMO2 TEC Controller',
                [('Elapsed time', 't')],
                [
                    ('Thermistor Temperature', 'Temperature', 'C')
                ],
                context=self.c_record
            )

    def _lock(self, status):
        self.gui.toggle_button.setEnabled(status)
        self.gui.lock_set.setEnabled(status)
        self.gui.lock_P.setEnabled(status)
        self.gui.lock_I.setEnabled(status)
        self.gui.lock_D.setEnabled(status)

    @inlineCallbacks
    def updateTemperature(self, c, temp):
        self.gui.displayTemp.setText("{:.3f}".format(temp))
        if self.recording:
            yield self.dv.add(time() - self.starttime, temp, context=self.c_record)

    def updateCurrent(self, c, curr):
        self.gui.displayCurr.setText("{:.3f}".format(curr))

    def updateToggle(self, c, status):
        # need to convert channel number to index
        toggleswitch = self.gui.toggle_button
        toggleswitch.blockSignals(True)
        toggleswitch.setChecked(status)
        toggleswitch.setAppearance(status)
        toggleswitch.blockSignals(False)

    def updateLock(self, c, msg):
        param, value = msg
        # get appropriate widget
        if param == 'p':    widget = self.gui.lock_P
        elif param == 'i':  widget = self.gui.lock_I
        elif param == 'd':  widget = self.gui.lock_D
        # set value
        widget.setValue(param)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(InjectionLockTemperatureClient)
