from numpy import arange, linspace
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
        yield self.wavemeter.addListener(listener=self.updateExp, source=None, ID=UPDATEEXP_ID)
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
        self.gui.startSwitch.setChecked(initstartvalue)
        self.gui.lockSwitch.setChecked(initlockvalue)
        # set display for each channel
        for channel_name, channel_params in self.chaninfo.items():
            # expand parameters and get GUI widget
            wmChannel, frequency, _, _, dacPort, _ = channel_params
            widget = self.gui.channels[wmChannel]
            # get channel values
            lock_frequency = yield self.wavemeter.get_pid_course(dacPort)
            lock_status = yield self.wavemeter.get_channel_lock(dacPort, wmChannel)
            exposure_ms = yield self.wavemeter.get_exposure(wmChannel)
            measure_state = yield self.wavemeter.get_switcher_signal_state(wmChannel)
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
            wmChannel, frequency, _, _, dacPort, _ = channel_params
            widget = self.gui.channels[wmChannel]
            # assign slots
            widget.showTrace.toggled.connect(lambda status, chan=wmChannel: self.toggleTrace(status, chan))
            widget.setPID.clicked.connect(lambda status, _dacPort=dacPort: self.setupPID(dacPort))
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
    def setupPID(self, dacPort):
        index_tmp = {1: 0, -1: 1}
        # get initial values
        pInit = yield self.wavemeter.get_pid_p(dacPort)
        iInit = yield self.wavemeter.get_pid_i(dacPort)
        dInit = yield self.wavemeter.get_pid_d(dacPort)
        dtInit = yield self.wavemeter.get_pid_dt(dacPort)
        constInit = yield self.wavemeter.get_const_dt(dacPort)
        sensInit = yield self.wavemeter.get_pid_sensitivity(dacPort)
        polInit = yield self.wavemeter.get_pid_polarity(dacPort)
        # set initial values
        self.gui.pidGUI.spinP.setValue(pInit)
        self.gui.pidGUI.spinI.setValue(iInit)
        self.gui.pidGUI.spinD.setValue(dInit)
        self.gui.pidGUI.spinDt.setValue(dtInit)
        self.gui.pidGUI.useDTBox.setCheckState(bool(constInit))
        self.gui.pidGUI.spinFactor.setValue(sensInit[0])
        self.gui.pidGUI.spinExp.setValue(sensInit[1])
        self.gui.pidGUI.polarityBox.setCurrentIndex(index_tmp[polInit])
        # connect signals to slots
        # self.gui.pidGUI.spinP.valueChanged.connect(lambda p, _dacPort=dacPort: self.wavemeter.set_pid_p(_dacPort, p))
        # self.gui.pidGUI.spinI.valueChanged.connect(lambda i, _dacPort=dacPort: self.wavemeter.set_pid_p(_dacPort, i))
        # self.gui.pidGUI.spinD.valueChanged.connect(lambda d, _dacPort=dacPort: self.wavemeter.set_pid_p(_dacPort, d))
        # self.gui.pidGUI.spinDt.valueChanged.connect(lambda dt, _dacPort=dacPort: self.wavemeter.set_pid_dt(_dacPort, dt))
        # self.gui.pidGUI.useDTBox.stateChanged.connect(lambda state, _dacPort=dacPort: self.wavemeter.set_const_dt(dacPort, state))
        # self.gui.pidGUI.spinFactor.valueChanged.connect(lambda factor, _dacPort=dacPort, exp=self.gui.pidGUI.spinExp.value():
        #                                              self.wavemeter.set_pid_sensitivity(dacPort, factor, int(exp)))
        # self.gui.pidGUI.spinExp.valueChanged.connect(lambda exp, _dacPort=dacPort, factor=self.gui.pidGUI.spinFactor.value():
        #                                           self.wavemeter.set_pid_sensitivity(dacPort, factor, int(exp)))
        #self.gui.pidGUI.polarityBox.currentIndexChanged.connect(lambda index, _dacPort=dacPort: self.changePolarity(index, _dacPort))

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
                self.gui.channels[chan].currentfrequency.setText('{:.6f}'.format(freq))

    def updatePIDvoltage(self, c, signal):
        dacPort, value = signal
        if dacPort in self.gui.dacPorts:
            #todo: check currently enabled
            try:
                pass
                # self.gui.channels[self.gui.dacPorts[dacPort]].PIDvoltage.setText('DAC Voltage (mV)  {:.1f}'.format(value))
                # self.gui.channels[self.gui.dacPorts[dacPort]].PIDindicator.update_slider(value / 1000.0)
            except Exception as e:
                print(e)

    def toggleTrace(self, status, chan):
        pi = self.gui.pattern[chan]
        if status:
            self.gui.trace_display.addItem(pi)
        else:
            self.gui.trace_display.removeItem(pi)

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

    def updateExp(self, c, signal):
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
        chan, trace = signal
        num_points = 512
        if chan in self.gui.pattern.keys():
            self.gui.pattern[chan].setData(x=linspace(0, 2000, num_points), y=trace)

    @inlineCallbacks
    def changePolarity(self, index, dacPort):
        if index == 0:
            yield self.wavemeter.set_pid_polarity(dacPort, 1)
        else:
            yield self.wavemeter.set_pid_polarity(dacPort, -1)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(multiplexer_client)
