from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.SLS_client.SLS_gui import SLS_gui

_TIME_STR = '{0:02d}:{1:02d}:{2:02d}'


class SLS_client(GUIClient):

    name = 'SLS Client'
    AUTOLOCKID = 295379
    OFFSETID = 295378
    PDHID = 295377
    SERVOID = 295376
    servers = {'sls': 'SLS Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = SLS_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        # autolock
        yield self.sls.signal__autolock_update(self.AUTOLOCKID)
        yield self.sls.addListener(listener=self.updateAutolock, source=None, ID=self.AUTOLOCKID)

        # offset
        yield self.sls.signal__offset_update(self.OFFSETID)
        yield self.sls.addListener(listener=self.updateOffset, source=None, ID=self.OFFSETID)

        # pdh
        yield self.sls.signal__pdh_update(self.PDHID)
        yield self.sls.addListener(listener=self.updatePDH, source=None, ID=self.PDHID)

        # current servo
        yield self.sls.signal__current_servo_update(self.SERVOID)
        yield self.sls.addListener(listener=self.updateServo, source=None, ID=self.SERVOID)

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
        self.gui.autolock_status.setText(str(init_values['AutoLockStatus']))
        autolock_time = float(init_values['LockTime'])
        autolock_time_formatted = self._dateFormat(autolock_time)
        self.gui.autolock_time.setText(autolock_time_formatted)

        # offset
        offset_freq_mhz = float(init_values['OffsetFrequency']) / 1e6
        self.gui.offset_freq.setValue(offset_freq_mhz)
        self.gui.offset_eom_rf_amp.setValue(float(init_values['EOMRFAmplitude']))
        self.gui.offset_lockpoint.setCurrentIndex(int(init_values['LockPoint']))

        # PDH
        print(int(init_values['PDHFrequency']))
        self.gui.PDH_freq.setValue(float(init_values['PDHFrequency']))
        self.gui.PDH_phasemodulation.setValue(float(init_values['PDHPMIndex']))
        self.gui.PDH_phaseoffset.setValue(float(init_values['PDHPhaseOffset']))
        self.gui.PDH_filter.setCurrentIndex(int(init_values['PDHDemodFilter']))

        # servo
        self.servo_target = 0
        self.gui.servo_param.setCurrentIndex(self.servo_target)
        self.gui.servo_set.setValue(float(init_values['CurrentServoSetpoint']))
        self.gui.servo_p.setValue(float(init_values['CurrentServoPropGain']))
        self.gui.servo_i.setValue(float(init_values['CurrentServoIntGain']))
        self.gui.servo_d.setValue(float(init_values['CurrentServoDiffGain']))
        self.gui.servo_filter.setCurrentIndex(int(init_values['CurrentServoOutputFilter']))

    def initGUI(self):
        # autolock
        self.gui.autolock_toggle.toggled.connect(lambda status: self.sls.autolock_toggle(status))
        self.gui.autolock_param.currentTextChanged.connect(lambda param: self.sls.autolock_parameter(param.upper()))

        # PDH
        self.gui.PDH_freq.valueChanged.connect(lambda value: self.changePDHValue('frequency', value))
        self.gui.PDH_phasemodulation.valueChanged.connect(lambda value: self.changePDHValue('index', value))
        self.gui.PDH_phaseoffset.valueChanged.connect(lambda value: self.changePDHValue('phase', value))
        self.gui.PDH_filter.currentIndexChanged.connect(lambda value: self.changePDHValue('filter', value))

        # todo: offset

        # servo
        self.gui.servo_param.currentTextChanged.connect(lambda target: self.changeServoTarget(target))
        self.gui.servo_set.valueChanged.connect(lambda value: self.sls.servo(self.servo_target, 'set', value))
        self.gui.servo_filter.currentIndexChanged.connect(lambda value: self.sls.servo(self.servo_target, 'filter', value))
        self.gui.servo_p.valueChanged.connect(lambda value: self.sls.servo(self.servo_target, 'p', value))
        self.gui.servo_i.valueChanged.connect(lambda value: self.sls.servo(self.servo_target, 'i', value))
        self.gui.servo_d.valueChanged.connect(lambda value: self.sls.servo(self.servo_target, 'd', value))

        # lock everything on startup
        self.gui._lock(False, self.gui.autolock_widget)
        self.gui._lock(False, self.gui.offset_widget)
        self.gui._lock(False, self.gui.PDH_widget)
        self.gui._lock(False, self.gui.servo_widget)


    # SIGNALS
    def updateAutolock(self, c, lock_params):
        """
        Updates GUI when autolock values are received from server.

        Args:
            c: labrad context
            lock_params (tuple):
                - time the 729 laser in the SLS has been locked
                - how many lock attempts via the autolocking feature were needed to lock 729 laser
                - if laser is successfully locked
        """

        # extract values
        autolock_time = lock_params[0]
        autolock_count = lock_params[1]
        autolock_status = lock_params[2]
        autolock_enabled = lock_params[3]

        # update GUI
        autolock_time_formatted = self._dateFormat(autolock_time)
        self.gui.autolock_attempts.setText(str(autolock_count))
        self.gui.autolock_status.setText(str(autolock_status))
        self.gui.autolock_toggle.setChecked(bool(autolock_enabled))



    # SIGNALS
    def updateOffset(self, c, offset_params):
        """
        Updates GUI when offset values are received from server.

        Args:
            c: labrad context
            offset_params (tuple):
                - the frequency used for offset locking in MHz
                - rf ampltiude used to generate the offset frequency (in percent)
                - order sideband used for generating the offset lock (J0, J_+1, J_+2, J_-1, J_-2)
        """
        # extract values
        offset_freq_mhz = offset_params[0]
        offset_eom_rf_amplitude = offset_params[1]
        offset_lockpoint = offset_params[2]

        # update GUI
        self.gui.offset_freq.setValue(offset_freq_mhz)
        self.gui.offset_eom_rf_amp.setValue(offset_eom_rf_amplitude)
        self.gui.offset_lockpoint.setValue(offset_lockpoint)


    def updatePDH(self,c, pdh_vals):
        """
        Updates GUI when pdh values are received from server.

        Args:
            c: labrad context
            pdh_vals (tuple):
                - frequency of pdh lock
                - phase modulation of pdh lock
                - reference phase of pdh lock
                - pdh filter index
        """
        # extract values
        pdh_freq = pdh_vals[0]
        pdh_phase_modulation = pdh_vals[1]
        pdh_reference_phase = pdh_vals[2]
        pdh_filter_index = pdh_vals[3]

        # update GUI
        self.gui.PDH_freq.setValue(pdh_freq)
        self.gui.PDH_phasemodulation.setValue(pdh_phase_modulation)
        self.gui.PDH_phaseoffset.setValue(pdh_reference_phase)
        self.gui.PDH_filter.setCurrentIndex(pdh_filter_index)

    def updateServo(self, c, servo_vals):
        """
        Updates GUI when servo values are received from server.
        Args:
            c: labrad context
            servo_vals (tuple):
                - parameter name
                - servo setpoint
                - servo prop gain
                - servo integral gain
                - servo differential gain
                - servo output filter
        Returns:
        """

        servo_parameter = servo_vals[0]
        servo_parameter_target_dict = {'Current': 0, 'PZT': 1, 'TX': 2}


        if self.servo_target == servo_parameter_target_dict[servo_parameter]:
            # extract values
            servo_setpoint = servo_vals[0]
            servo_p = servo_vals[1]
            servo_i = servo_vals[2]
            servo_d = servo_vals[3]
            servo_output_filter = servo_vals[4]

            # update GUI
            self.gui.servo_param.setValue(servo_setpoint)
            self.gui.servo_p.setValue(servo_p)
            self.gui.servo_i.setValue(servo_i)
            self.gui.servo_d.setValue(servo_d)
            self.gui.servo_filter.setCurrentIndex(servo_output_filter)

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
