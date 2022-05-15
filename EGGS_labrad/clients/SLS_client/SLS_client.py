from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.SLS_client.SLS_gui import SLS_gui

_TIME_STR = '{0:02d}:{1:02d}:{2:02d}'


class SLS_client(GUIClient):

    name = 'SLS Client'
    AUTOLOCKID = 295372
    servers = {'sls': 'SLS Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = SLS_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        yield self.sls.signal__autolock_update(self.AUTOLOCKID)
        yield self.sls.addListener(listener=self.updateAutolock, source=None, ID=self.AUTOLOCKID)
        # set up polling
        poll_params = yield self.sls.polling()
        if not poll_params[0]:
            yield self.sls.polling(True, 5.0)
        return self.cxn

    @inlineCallbacks
    def initData(self):
        # get all values
        values_tmp = yield self.sls.get_values()
        init_values = dict(zip(values_tmp[0], values_tmp[1]))
        # autolock
        self.gui.autolock_param.setCurrentIndex(int(init_values['SweepType']))
        self.gui.autolock_toggle.setChecked(bool(init_values['AutoLockEnable']))
        self.gui.autolock_attempts.setText(str(init_values['LockCount']))
        autolock_time = float(init_values['LockTime'])
        autolock_time_formatted = self._dateFormat(autolock_time)
        self.gui.autolock_time.setText(autolock_time_formatted)
        # offset
        self.gui.off_freq.setValue(float(init_values['OffsetFrequency']))
        self.gui.off_lockpoint.setCurrentIndex(int(init_values['LockPoint']))
        # PDH
        self.gui.PDH_freq.setValue(float(init_values['PDHFrequency']))
        self.gui.PDH_phasemodulation.setValue(float(init_values['PDHPMIndex']))
        self.gui.PDH_phaseoffset.setValue(float(init_values['PDHPhaseOffset']))
        self.gui.PDH_filter.setCurrentIndex(int(init_values['PDHDemodFilter']))
        # Servo
        self.gui.servo_param.setCurrentIndex(0)
        self.gui.servo_set.setValue(float(init_values['CurrentServoSetpoint']))
        self.gui.servo_p.setValue(float(init_values['CurrentServoPropGain']))
        self.gui.servo_i.setValue(float(init_values['CurrentServoIntGain']))
        self.gui.servo_d.setValue(float(init_values['CurrentServoDiffGain']))
        self.gui.servo_filter.setCurrentIndex(int(init_values['CurrentServoOutputFilter']))

    def initGUI(self):
        # autolock
        self.gui.autolock_toggle.toggled.connect(lambda status: self.sls.autolock_toggle(status))
        self.gui.autolock_param.currentTextChanged.connect(lambda param: self.sls.autolock_parameter(param.upper()))
        # pdh
        self.gui.PDH_freq.valueChanged.connect(lambda value: self.changePDHValue('frequency', value))
        self.gui.PDH_phasemodulation.valueChanged.connect(lambda value: self.changePDHValue('index', value))
        self.gui.PDH_phaseoffset.valueChanged.connect(lambda value: self.changePDHValue('phase', value))
        self.gui.PDH_filter.currentIndexChanged.connect(lambda value: self.changePDHValue('filter', value))
        # servo
        self.gui.servo_param.currentTextChanged.connect(lambda target: self.changeServoTarget(target))
        self.gui.servo_set.valueChanged.connect(lambda value: self.sls.servo(self.servo_target, 'set', value))
        self.gui.servo_filter.currentIndexChanged.connect(lambda value: self.sls.servo(self.servo_target, 'filter', value))
        self.gui.servo_p.valueChanged.connect(lambda value: self.sls.servo(self.servo_target, 'p', value))
        self.gui.servo_i.valueChanged.connect(lambda value: self.sls.servo(self.servo_target, 'i', value))
        self.gui.servo_d.valueChanged.connect(lambda value: self.sls.servo(self.servo_target, 'd', value))
        # lock everything on startup
        self.gui._lock(False, self.gui.autolock_widget)
        self.gui._lock(False, self.gui.off_widget)
        self.gui._lock(False, self.gui.PDH_widget)
        self.gui._lock(False, self.gui.servo_widget)

    # SIGNALS
    def updateAutolock(self, c, lockstatus):
        """
        Updates GUI when values are received from server.
        """
        autolock_time = lockstatus[1]
        autolock_time_formatted = self._dateFormat(autolock_time)
        self.gui.autolock_attempts.setText(str(lockstatus[0]))
        self.gui.autolock_time.setText(autolock_time_formatted)


    # SLOTS
    @inlineCallbacks
    def changePDHValue(self, param_name, param_value):
        yield self.sls.PDH(param_name, param_value)

    @inlineCallbacks
    def changeServoTarget(self, target):
        self.servo_target = target.lower()
        servo_params = {'p': self.gui.servo_p, 'i': self.gui.servo_i,
                        'd': self.gui.servo_d, 'set': self.gui.servo_set}
        for param_name, gui_element in servo_params.items():
            val = yield self.sls.servo(self.servo_target, param_name)
            gui_element.setEnabled(False)
            gui_element.setValue(float(val))
            gui_element.setEnabled(True)
        index = yield self.sls.servo(self.servo_target, 'filter')
        self.gui.servo_filter.setEnabled(False)
        self.gui.servo_filter.setCurrentIndex(int(index))
        self.gui.servo_filter.setEnabled(True)


    # HELPER
    def _dateFormat(self, _seconds):
        days = _seconds / 86400
        hours = (days % 1) * 24
        minutes = int((hours % 1) * 60)
        time_str = _TIME_STR.format(int(days), int(hours), minutes)
        return time_str


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(SLS_client)
