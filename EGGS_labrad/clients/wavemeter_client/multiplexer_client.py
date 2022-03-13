from numpy import arange
from socket import gethostname
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.clients import GUIClient
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

    def getgui(self):
        if self.gui is None:
            self.gui = multiplexer_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        try:
            from EGGS_labrad.config.multiplexerclient_config import multiplexer_config
        except Exception as e:
            pass

        self.chaninfo = multiplexer_config.info
        wavemeterIP = multiplexer_config.ip
        # todo: make accept different IP
        self.cxn = yield connectAsync(wavemeterIP,
                                      name=self.name,
                                      password=self.password)

        yield self.wavemeter.signal__frequency_changed(FREQ_CHANGED_ID)
        yield self.wavemeter.signal__selected_channels_changed(CHANNEL_CHANGED_ID)
        yield self.wavemeter.signal__update_exp(UPDATEEXP_ID)
        yield self.wavemeter.signal__lock_changed(LOCK_CHANGED_ID)
        yield self.wavemeter.signal__output_changed(OUTPUT_CHANGED_ID)
        yield self.wavemeter.signal__pidvoltage_changed(PID_CHANGED_ID)
        yield self.wavemeter.signal__channel_lock_changed(CHAN_LOCK_CHANGED_ID)
        yield self.wavemeter.signal__amplitude_changed(AMPLITUDE_CHANGED_ID)
        yield self.wavemeter.signal__pattern_changed(PATTERN_CHANGED_ID)

        yield self.wavemeter.addListener(listener=self.updateFrequency, source=None, ID=FREQ_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.toggleMeas, source=None, ID=CHANNEL_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updateexp, source=None, ID=UPDATEEXP_ID)
        yield self.wavemeter.addListener(listener=self.toggleLock, source=None, ID=LOCK_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updateWLMOutput, source=None, ID=OUTPUT_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updatePIDvoltage, source=None, ID=PID_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.toggleChannelLock, source=None, ID=CHAN_LOCK_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updateAmplitude, source=None, ID=AMPLITUDE_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updatePattern, source=None, ID=PATTERN_CHANGED_ID)

    @inlineCallbacks
    def initData(self):
        initstartvalue = yield self.wavemeter.get_wlm_output()
        initlockvalue = yield self.wavemeter.get_lock_state()
        self.gui.lockSwitch.setChecked(initlockvalue)
        self.gui.startSwitch.setChecked(initstartvalue)


        # todo: iterate for each channel
        initcourse = yield self.getPIDCourse(dacPort, hint)
        widget.spinFreq.setValue(initcourse)

        initLock = yield self.wavemeter.get_channel_lock(dacPort, wmChannel)
        widget.lockChannel.setChecked(bool(initLock))

        initvalue = yield self.wavemeter.get_exposure(wmChannel)
        widget.spinExp.setValue(initvalue)

        initmeas = yield self.wavemeter.get_switcher_signal_state(wmChannel)
        initmeas = initmeas
        widget.measSwitch.setChecked(bool(initmeas))

    def initGUI(self):
        self.lockSwitch.toggled.connect(self.setLock)
        self.startSwitch.toggled.connect(self.setOutput)

        # get channel
        for chan in self.chaninfo:
            if dacPort != 0:
                widget.spinFreq.valueChanged.connect(
                    lambda freq=widget.spinFreq.value(), dacPort=dacPort: self.freqChanged(freq, dacPort))

                widget.lockChannel.toggled.connect(
                    lambda state=widget.lockChannel.isDown(), dacPort=dacPort: self.lockSingleChannel(state, dacPort))
            else:
                widget.spinFreq.setValue(float(hint))
                widget.lockChannel.toggled.connect(
                    lambda state=widget.lockChannel.isDown(), wmChannel=wmChannel: self.setButtonOff(wmChannel))

            widget.spinExp.valueChanged.connect(
                lambda exp=widget.spinExp.value(), wmChannel=wmChannel: self.expChanged(exp, wmChannel))

            widget.measSwitch.toggled.connect(
                lambda state=widget.measSwitch.isDown(), wmChannel=wmChannel: self.changeState(state, wmChannel))


    @inlineCallbacks
    def InitializePIDGUI(self, dacPort, chan):
        pInit = yield self.wavemeter.get_pid_p(dacPort)
        iInit = yield self.wavemeter.get_pid_i(dacPort)
        dInit = yield self.wavemeter.get_pid_d(dacPort)
        dtInit = yield self.wavemeter.get_pid_dt(dacPort)
        constInit = yield self.wavemeter.get_const_dt(dacPort)
        sensInit = yield self.wavemeter.get_pid_sensitivity(dacPort)
        polInit = yield self.wavemeter.get_pid_polarity(dacPort)

        self.pid.spinP.setValue(pInit)
        self.pid.spinI.setValue(iInit)
        self.pid.spinD.setValue(dInit)
        self.pid.spinDt.setValue(dtInit)
        self.pid.useDTBox.setCheckState(bool(constInit))
        self.pid.spinFactor.setValue(sensInit[0])
        self.pid.spinExp.setValue(sensInit[1])
        self.pid.polarityBox.setCurrentIndex(self.index[polInit])

        self.pid.spinP.valueChanged.connect(lambda p=self.pid.spinP.value(), dacPort=dacPort: self.changeP(p, dacPort))
        self.pid.spinI.valueChanged.connect(lambda i=self.pid.spinI.value(), dacPort=dacPort: self.changeI(i, dacPort))
        self.pid.spinD.valueChanged.connect(lambda d=self.pid.spinD.value(), dacPort=dacPort: self.changeD(d, dacPort))
        self.pid.spinDt.valueChanged.connect(
            lambda dt=self.pid.spinDt.value(), dacPort=dacPort: self.changeDt(dt, dacPort))
        self.pid.useDTBox.stateChanged.connect(
            lambda state=self.pid.useDTBox.isChecked(), dacPort=dacPort: self.constDt(state, dacPort))
        self.pid.spinFactor.valueChanged.connect(
            lambda factor=self.pid.spinFactor.value(), dacPort=dacPort: self.changeFactor(factor, dacPort))
        self.pid.spinExp.valueChanged.connect(
            lambda exponent=self.pid.spinExp.value(), dacPort=dacPort: self.changeExponent(exponent, dacPort))
        self.pid.polarityBox.currentIndexChanged.connect(
            lambda index=self.pid.polarityBox.currentIndex(), dacPort=dacPort: self.changePolarity(index, dacPort))

        self.pid.show()

    @inlineCallbacks
    def expChanged(self, exp, chan):
        # these are switched, dont know why
        exp = int(exp)
        yield self.wavemeter.set_exposure_time(chan, exp)

    def updateFrequency(self, c, signal):
        chan = signal[0]
        if chan in self.channels:
            freq = signal[1]

            if not self.channels[chan].measSwitch.isChecked():
                self.channels[chan].currentfrequency.setText('Not Measured')
            elif freq == -3.0:
                self.channels[chan].currentfrequency.setText('Under Exposed')
            elif freq == -4.0:
                self.channels[chan].currentfrequency.setText('Over Exposed')
            elif freq == -17.0:
                self.channels[chan].currentfrequency.setText('Data Error')
            else:
                self.channels[chan].currentfrequency.setText(str(freq)[0:10])

    def updatePIDvoltage(self, c, signal):
        dacPort, value = signal[0]
        if dacPort in dacPorts:
            try:
                self.channels[dacPorts[dacPort]].PIDvoltage.setText('DAC Voltage (mV)  ' + "{:.1f}".format(value))
                self.channels[dacPorts[dacPort]].PIDindicator.update_slider(value / 1000.0)
            except:
                pass

    def toggleMeas(self, c, signal):
        chan, value = signal
        if chan in self.channels:
            self.channels[chan].measSwitch.blockSignals(True)
            self.channels[chan].measSwitch.setChecked(value)
            self.channels[chan].measSwitch.blockSignals(False)

    def toggleLock(self, c, signal):
        self.lockSwitch.blockSignals(True)
        self.lockSwitch.setChecked(signal)
        self.lockSwitch.blockSignals(False)

    def toggleChannelLock(self, c, signal):
        _, wmChannel, state = signal
        if wmChannel in self.channels:
            self.channels[wmChannel].lockChannel.blockSignals(True)
            self.channels[wmChannel].lockChannel.setChecked(bool(state))
            self.channels[wmChannel].lockChannel.blockSignals(False)

    def updateexp(self, c, signal):
        chan, value = signal
        if chan in self.channels:
            self.channels[chan].spinExp.blockSignals(True)
            self.channels[chan].spinExp.setValue(value)
            self.channels[chan].spinExp.blockSignals(False)

    def updateWLMOutput(self, c, signal):
        self.startSwitch.blockSignals(True)
        self.startSwitch.setChecked(signal)
        self.startSwitch.blockSignals(False)

    def updateAmplitude(self, c, signal):
        wmChannel,value = signal
        if wmChannel in self.channels:
            self.channels[wmChannel].powermeter.blockSignals(True)
            self.channels[wmChannel].powermeter.setValue(value)
            self.channels[wmChannel].powermeter.blockSignals(False)

    def updatePattern(self, c, signal):
        chan, IF1 = signal
        points = 512
        if chan in self.gui.pattern:
            self.gui.pattern[chan].setData(x=arange(points), y=IF1)

    def setButtonOff(self, wmChannel):
        self.channels[wmChannel].lockChannel.setChecked(False)

    @inlineCallbacks
    def changeState(self, state, chan):
        yield self.wavemeter.set_switcher_signal_state(chan, state)

    @inlineCallbacks
    def lockSingleChannel(self, state, dacPort):
        wmChannel = dacPorts[dacPort]
        yield self.wavemeter.set_channel_lock(dacPort, wmChannel, state)

    @inlineCallbacks
    def freqChanged(self, freq, dacPort):
        yield self.wavemeter.set_pid_course(dacPort, freq)

    @inlineCallbacks
    def setLock(self, state):
        yield self.wavemeter.set_lock_state(state)

    @inlineCallbacks
    def setOutput(self, state):
        yield self.wavemeter.set_wlm_output(state)

    @inlineCallbacks
    def getPIDCoursegetPIDCourse(self, dacPort, hint):
        course = yield self.wavemeter.get_pid_course(dacPort)
        try:
            course = float(course)
        except:
            try:
                course = float(hint)
            except:
                course = 600
        returnValue(course)

    @inlineCallbacks
    def changeP(self, p, dacPort):
        yield self.wavemeter.set_pid_p(dacPort, p)

    @inlineCallbacks
    def changeI(self, i, dacPort):
        yield self.wavemeter.set_pid_i(dacPort, i)

    @inlineCallbacks
    def changeD(self, d, dacPort):
        yield self.wavemeter.set_pid_d(dacPort, d)

    @inlineCallbacks
    def changeDt(self, dt, dacPort):
        yield self.wavemeter.set_pid_dt(dacPort, dt)

    @inlineCallbacks
    def constDt(self, state, dacPort):
        if state == 0:
            yield self.wavemeter.set_const_dt(dacPort, False)
        else:
            yield self.wavemeter.set_const_dt(dacPort, True)

    @inlineCallbacks
    def changeFactor(self, factor, dacPort):
        yield self.wavemeter.set_pid_sensitivity(dacPort, factor, int(self.pid.spinExp.value()))

    @inlineCallbacks
    def changeExponent(self, exponent, dacPort):
        yield self.wavemeter.set_pid_sensitivity(dacPort, self.pid.spinFactor.value(), int(exponent))

    @inlineCallbacks
    def changePolarity(self, index, dacPort):
        if index == 0:
            yield self.wavemeter.set_pid_polarity(dacPort, 1)
        else:
            yield self.wavemeter.set_pid_polarity(dacPort, -1)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(multiplexer_client)
