from numpy import arange
from socket import gethostname
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.config.multiplexerclient_config import multiplexer_config
from EGGS_labrad.clients.wavemeter_client.multiplexer_gui import multiplexer_gui


FREQ_CHANGED_ID = 445566
CHANNEL_CHANGED_ID = 143533
UPDATEEXP_ID = 111221
LOCK_CHANGED_ID = 549210
OUTPUT_CHANGED_ID = 190909
PID_CHANGED_ID = 102588
CHAN_LOCK_CHANGED_ID = 148323
AMPLITUDE_CHANGED_ID = 238883
PATTERN_CHANGED_ID = 462917


#todo: move all displays to one
#todo: create single PID box
class multiplexer_client(GUIClient):

    name = gethostname() + ' Wavemeter Client'
    servers = {'wavemeter': 'multiplexerserver'}
    LABRADHOST = multiplexer_config.ip

    def getgui(self):
        if self.gui is None:
            self.gui = multiplexer_gui(multiplexer_config.channels)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # get config
        self.chaninfo = multiplexer_config.channels

        # connect to device signals
        yield self.wavemeter.signal__frequency_changed(FREQ_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updateFrequency, source=None, ID=FREQ_CHANGED_ID)
        yield self.wavemeter.signal__selected_channels_changed(CHANNEL_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.toggleMeas, source=None, ID=CHANNEL_CHANGED_ID)
        yield self.wavemeter.signal__update_exp(UPDATEEXP_ID)
        yield self.wavemeter.addListener(listener=self.updateexp, source=None, ID=UPDATEEXP_ID)
        yield self.wavemeter.signal__lock_changed(LOCK_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updateWLMOutput, source=None, ID=OUTPUT_CHANGED_ID)
        yield self.wavemeter.signal__output_changed(OUTPUT_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.toggleLock, source=None, ID=LOCK_CHANGED_ID)
        yield self.wavemeter.signal__pidvoltage_changed(PID_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updatePIDvoltage, source=None, ID=PID_CHANGED_ID)
        yield self.wavemeter.signal__channel_lock_changed(CHAN_LOCK_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.toggleChannelLock, source=None, ID=CHAN_LOCK_CHANGED_ID)
        yield self.wavemeter.signal__amplitude_changed(AMPLITUDE_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updateAmplitude, source=None, ID=AMPLITUDE_CHANGED_ID)
        yield self.wavemeter.signal__pattern_changed(PATTERN_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updatePattern, source=None, ID=PATTERN_CHANGED_ID)

    @inlineCallbacks
    def initData(self):
        # wavemeter status
        initstartvalue = yield self.wavemeter.get_wlm_output()
        initlockvalue = yield self.wavemeter.get_lock_state()
        self.gui.lockSwitch.setChecked(initlockvalue)
        self.gui.startSwitch.setChecked(initstartvalue)
        # set display for each channel
        for channel_name, channel_params in self.chaninfo.items():
            # expand parameters and get GUI widget
            wmChannel, frequency, _, _, _, dacPort, _, _ = channel_params
            widget = self.gui.channels[wmChannel]
            # get channel values
            lock_frequency = yield self.wavemeter.get_pid_course(dacPort)
            lock_status = yield self.wavemeter.get_channel_lock(dacPort, wmChannel)
            exposure_ms = yield self.wavemeter.get_exposure(wmChannel)
            measure_state = yield self.wavemeter.get_switcher_signal_state(wmChannel)
            # set channel values in GUI
            try:
                lock_frequency_tmp = float(lock_frequency)
                widget.spinFreq.setValue(lock_frequency_tmp)
            except Exception as e:
                pass
            widget.lockChannel.setChecked(bool(lock_status))
            widget.spinExp.setValue(exposure_ms)
            widget.measSwitch.setChecked(bool(measure_state))

    def initGUI(self):
        # global wavemeter settings
        #self.gui.lockSwitch.toggled.connect(lambda state: self.wavemeter.set_lock_state(state))
        #self.gui.startSwitch.toggled.connect(lambda state: self.wavemeter.set_wlm_output(state))
        # channel wavemeter settings
        for channel_name, channel_params in self.chaninfo.items():
            # expand parameters and get GUI widget
            wmChannel, frequency, _, _, _, dacPort, _, _ = channel_params
            widget = self.gui.channels[wmChannel]
            # assign slots
            #widget.spinExp.valueChanged.connect(lambda exp: self.wavemeter.set_exposure_time(wmChannel, int(exp)))
            #widget.measSwitch.toggled.connect(lambda state: self.wavemeter.set_switcher_signal_state(wmChannel, state))
            # if dacPort != 0:
            #     widget.spinFreq.valueChanged.connect(lambda freq, _dacPort=dacPort: self.wavemeter.set_pid_course(_dacPort, freq))
            #     widget.lockChannel.toggled.connect(
            #         lambda state, dac_port=dacPort, wm_channel=wmChannel: self.wavemeter.set_channel_lock(dacPort, wm_channel, state))
            # else:
            #     widget.spinFreq.setValue(float(frequency))
            #     widget.lockChannel.toggled.connect(lambda state: widget.lockChannel.setChecked(False))

    @inlineCallbacks
    def initializePIDGUI(self, dacPort):
        # get initial values
        pInit = yield self.wavemeter.get_pid_p(dacPort)
        iInit = yield self.wavemeter.get_pid_i(dacPort)
        dInit = yield self.wavemeter.get_pid_d(dacPort)
        dtInit = yield self.wavemeter.get_pid_dt(dacPort)
        constInit = yield self.wavemeter.get_const_dt(dacPort)
        sensInit = yield self.wavemeter.get_pid_sensitivity(dacPort)
        polInit = yield self.wavemeter.get_pid_polarity(dacPort)
        # set initial values
        self.gui.pid.spinP.setValue(pInit)
        self.gui.pid.spinI.setValue(iInit)
        self.gui.pid.spinD.setValue(dInit)
        self.gui.pid.spinDt.setValue(dtInit)
        self.gui.pid.useDTBox.setCheckState(bool(constInit))
        self.gui.pid.spinFactor.setValue(sensInit[0])
        self.gui.pid.spinExp.setValue(sensInit[1])
        self.gui.pid.polarityBox.setCurrentIndex(self.index[polInit])
        # connect signals to slots
        # self.gui.pid.spinP.valueChanged.connect(lambda p, _dacPort=dacPort: self.wavemeter.set_pid_p(_dacPort, p))
        # self.gui.pid.spinI.valueChanged.connect(lambda i, _dacPort=dacPort: self.wavemeter.set_pid_p(_dacPort, i))
        # self.gui.pid.spinD.valueChanged.connect(lambda d, _dacPort=dacPort: self.wavemeter.set_pid_p(_dacPort, d))
        # self.gui.pid.spinDt.valueChanged.connect(lambda dt, _dacPort=dacPort: self.wavemeter.set_pid_dt(_dacPort, dt))
        # self.gui.pid.useDTBox.stateChanged.connect(lambda state, _dacPort=dacPort: self.wavemeter.set_const_dt(dacPort, state))
        # self.gui.pid.spinFactor.valueChanged.connect(lambda factor, _dacPort=dacPort, exp=self.gui.pid.spinExp.value():
        #                                              self.wavemeter.set_pid_sensitivity(dacPort, factor, int(exp)))
        # self.gui.pid.spinExp.valueChanged.connect(lambda exp, _dacPort=dacPort, factor=self.gui.pid.spinFactor.value():
        #                                           self.wavemeter.set_pid_sensitivity(dacPort, factor, int(exp)))
        #self.gui.pid.polarityBox.currentIndexChanged.connect(lambda index, _dacPort=dacPort: self.changePolarity(index, _dacPort))
        self.gui.pid.show()

    def updateFrequency(self, c, signal):
        chan, freq = signal
        if chan in self.gui.channels.keys():
            if not self.gui.channels[chan].measSwitch.isChecked():
                self.gui.channels[chan].currentfrequency.setText('Not Measured')
            elif freq == -3.0:
                self.gui.channels[chan].currentfrequency.setText('Under Exposed')
            elif freq == -4.0:
                self.gui.channels[chan].currentfrequency.setText('Over Exposed')
            elif freq == -17.0:
                self.gui.channels[chan].currentfrequency.setText('Data Error')
            else:
                self.gui.channels[chan].currentfrequency.setText(str(freq)[0:10])

    def updatePIDvoltage(self, c, signal):
        dacPort, value = signal
        if dacPort in self.gui.dacPorts:
            try:
                self.gui.channels[self.gui.dacPorts[dacPort]].PIDvoltage.setText('DAC Voltage (mV)  {:.1f}'.format(value))
                self.gui.channels[self.gui.dacPorts[dacPort]].PIDindicator.update_slider(value / 1000.0)
            except Exception as e:
                pass

    def toggleMeas(self, c, signal):
        chan, state = signal
        if chan in self.gui.channels.keys():
            widget = self.gui.channels[chan]
            widget.measSwitch.blockSignals(True)
            widget.measSwitch.setChecked(state)
            widget.measSwitch.blockSignals(False)

    def toggleLock(self, c, signal):
        self.gui.lockSwitch.blockSignals(True)
        self.gui.lockSwitch.setChecked(signal)
        self.gui.lockSwitch.blockSignals(False)

    def toggleChannelLock(self, c, signal):
        _, chan, state = signal
        if chan in self.gui.channels.keys():
            self.gui.channels[chan].lockChannel.blockSignals(True)
            self.gui.channels[chan].lockChannel.setChecked(bool(state))
            self.gui.channels[chan].lockChannel.blockSignals(False)

    def updateexp(self, c, signal):
        chan, value = signal
        if chan in self.gui.channels.keys():
            self.gui.channels[chan].spinExp.blockSignals(True)
            self.gui.channels[chan].spinExp.setValue(value)
            self.gui.channels[chan].spinExp.blockSignals(False)

    def updateWLMOutput(self, c, signal):
        self.gui.startSwitch.blockSignals(True)
        self.gui.startSwitch.setChecked(signal)
        self.gui.startSwitch.blockSignals(False)

    def updateAmplitude(self, c, signal):
        chan, value = signal
        if chan in self.gui.channels.keys():
            self.gui.channels[chan].powermeter.blockSignals(True)
            self.gui.channels[chan].powermeter.setValue(value)
            self.gui.channels[chan].powermeter.blockSignals(False)

    def updatePattern(self, c, signal):
        chan, IF1 = signal
        points = 512
        if chan in self.gui.pattern.keys():
            self.gui.pattern[chan].setData(x=arange(points), y=IF1)

    @inlineCallbacks
    def changePolarity(self, index, dacPort):
        if index == 0:
            yield self.wavemeter.set_pid_polarity(dacPort, 1)
        else:
            yield self.wavemeter.set_pid_polarity(dacPort, -1)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(multiplexer_client)
