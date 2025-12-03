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
    SETPOINTID =    4651988
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
        yield self.tec.signal__setpoint_update(self.SETPOINTID)
        yield self.tec.addListener(listener=self.updateSetpoint, source=None, ID=self.SETPOINTID)

        poll_params = yield self.tec.polling()
        # only start if polling not start
        if not poll_params[0]:
            yield self.tec.polling(True, 5.0)

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
        _, lock_P =    yield self.tec.locking_p()
        _, lock_I =    yield self.tec.locking_i()
        _, lock_D =    yield self.tec.locking_d()

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

        # locking (only send value to device after RETURN key is pressed)
        self.gui.lock_set.textChanged.connect(lambda _: self.gui.lock_set.blockSignals(True))
        self.gui.lock_set.lineEdit().returnPressed.connect(lambda _box=self.gui.lock_set,
                                                           _device_func=self.tec.locking_setpoint:
                                                           self.value_changed(None, _box, _device_func))

        self.gui.lock_P.textChanged.connect(lambda _: self.gui.lock_P.blockSignals(True))
        self.gui.lock_P.lineEdit().returnPressed.connect(lambda _box=self.gui.lock_P,
                                                           _device_func=self.tec.locking_p:
                                                           self.value_changed(None, _box, _device_func))

        self.gui.lock_I.textChanged.connect(lambda _: self.gui.lock_I.blockSignals(True))
        self.gui.lock_I.lineEdit().returnPressed.connect(lambda _box=self.gui.lock_I,
                                                                _device_func=self.tec.locking_i:
                                                         self.value_changed(None, _box, _device_func))

        self.gui.lock_D.textChanged.connect(lambda _: self.gui.lock_D.blockSignals(True))
        self.gui.lock_D.lineEdit().returnPressed.connect(lambda _box=self.gui.lock_D,
                                                                _device_func=self.tec.locking_d:
                                                         self.value_changed(None, _box, _device_func))

        # todo: check
        self.gui.lock_button.setChecked(False)
        self.gui.lock_button.click()


    # SLOTS
    def value_changed(self, c, box, device_func):
        """
        Set/Get value of device based on gui input
        Args:
            c: labrad context
            box: gui element
            device_func: function used to write/read device parameter
        """
        val = float(box.text())
        device_func(val)
        box.blockSignals(False)

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
        """
        Lock other gui elements
        Args:
            status: indicate whether to prevent other gui elements from being toggled
        """
        self.gui.toggle_button.setEnabled(status)
        self.gui.lock_set.setEnabled(status)
        self.gui.lock_P.setEnabled(status)
        self.gui.lock_I.setEnabled(status)
        self.gui.lock_D.setEnabled(status)


    def updateTemperature(self, c, temp):
        """
        Update listed temperature if changed
        Args:
            c: labrad context
            temp: updated temperature of device
        """
        if not self.gui.displayTemp.signalsBlocked():
            self.gui.displayTemp.setText("{:.3f}".format(temp))
            if self.recording:
                yield self.dv.add(time() - self.starttime, temp, context=self.c_record)


    def updateCurrent(self, c, curr):
        """
        Update listed current if changed
        Args:
            c: labrad context
            curr: current outputted by device
        """
        if not self.gui.displayCurr.signalsBlocked():
            self.gui.displayCurr.setText("{:.3f}".format(curr))

    def updateToggle(self, c, status):
        """
        Update listed on/off status of device
        Args:
            c: labrad context
            status: indicates whether device has been turned on or off
        """
        # need to convert channel number to index
        toggleswitch = self.gui.toggle_button
        if not toggleswitch.signalsBlocked():
            toggleswitch.blockSignals(True)
            toggleswitch.setChecked(status)
            toggleswitch.setAppearance(status)
            toggleswitch.blockSignals(False)

    def updateSetpoint(self,c, setpoint):
        """
        Update listed setpoint of device
        Args:
            c: labrad context
            setpoint: current device has been set to output
        """
        if not self.gui.lock_set.signalsBlocked():
            self.gui.lock_set.blockSignals(True)
            self.gui.lock_set.setValue(setpoint)
            self.gui.lock_set.blockSignals(False)

    def updateLock(self, c, msg):
        """
        Update listed lock parameters of device
        Args:
            c: labrad context
            msg: message containing lock parameter and its new value
        """
        param, value = msg
        # get appropriate widget
        if param == 'p':    widget = self.gui.lock_P
        elif param == 'i':  widget = self.gui.lock_I
        elif param == 'd':  widget = self.gui.lock_D
        # set value
        if not widget.signalsBlocked():
            widget.blockSignals(True)
            widget.setValue(value)
            widget.blockSignals(False)

if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(InjectionLockTemperatureClient)
