from time import time
from numpy import linspace
from socket import gethostname
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient, createTrunk
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

# this variable controls how often we
# get the trace from the wavemeter
_TRACE_POLLING_RATE = 5


class multiplexer_client(GUIClient):

    name = gethostname() + ' Wavemeter Client'
    servers = {'wavemeter': 'multiplexerserver'}
    LABRADHOST = multiplexer_config.ip

    def getgui(self):
        if self.gui is None:
            self.gui = multiplexer_gui(multiplexer_config.channels)
        return self.gui


    # SETUP
    @inlineCallbacks
    def initClient(self):
        # get config
        self.chaninfo = multiplexer_config.channels
        # create dictionary for keeping track of which channels to record
        self.record_dict = {}
        # create connection to eggs_labrad to get data vault
        from labrad.wrappers import connectAsync
        from os import environ
        LABRADHOST_EGGS = environ['LABRADHOST']
        LABRADPASSWORD_EGGS = environ['LABRADPASSWORD']
        self.cxn_eggs = yield connectAsync(LABRADHOST_EGGS, name=self.name, password=LABRADPASSWORD_EGGS)
        self.dv = self.cxn_eggs['Data Vault']
        # connect to device signals
        yield self.wavemeter.signal__frequency_changed(FREQ_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updateFrequency, source=None, ID=FREQ_CHANGED_ID)
        yield self.wavemeter.signal__selected_channels_changed(CHANNEL_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.toggleMeas, source=None, ID=CHANNEL_CHANGED_ID)
        yield self.wavemeter.signal__update_exp(UPDATEEXP_ID)
        yield self.wavemeter.addListener(listener=self.updateExp, source=None, ID=UPDATEEXP_ID)
        yield self.wavemeter.signal__lock_changed(LOCK_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updateWMOutput, source=None, ID=OUTPUT_CHANGED_ID)
        yield self.wavemeter.signal__output_changed(OUTPUT_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.toggleLock, source=None, ID=LOCK_CHANGED_ID)
        yield self.wavemeter.signal__pidvoltage_changed(PID_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updatePIDvoltage, source=None, ID=PID_CHANGED_ID)
        yield self.wavemeter.signal__channel_lock_changed(CHAN_LOCK_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.toggleChannelLock, source=None, ID=CHAN_LOCK_CHANGED_ID)
        yield self.wavemeter.signal__amplitude_changed(AMPLITUDE_CHANGED_ID)
        yield self.wavemeter.addListener(listener=self.updateAmplitude, source=None, ID=AMPLITUDE_CHANGED_ID)
        # don't use signals for wavemeter trace since those update too frequently
        #yield self.wavemeter.signal__pattern_changed(PATTERN_CHANGED_ID)
        #yield self.wavemeter.addListener(listener=self.updatePattern, source=None, ID=PATTERN_CHANGED_ID)
        # instead, we use a loopingcall so we can control the update frequency
        self.refresher = LoopingCall(self.pollPattern)

    @inlineCallbacks
    def initData(self):
        # create parameters for recording
        for chan in self.gui.channels.keys():
            cntx_chan = self.cxn.context()
            name_tmp = 'tbh'
            for chan_name, chan_params in self.chaninfo.items():
                if chan == chan_params[0]:
                    name_tmp = chan_name
            self.record_dict[chan] = {'status': False, 'context': cntx_chan, 'starttime': None, 'name': name_tmp}
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
            widget.spinFreq.setValue(float(lock_frequency))

    def initGUI(self):
        # global wavemeter settings
        self.gui.lockSwitch.clicked.connect(lambda state: self.wavemeter.set_lock_state(state))
        self.gui.startSwitch.clicked.connect(lambda state: self.wavemeter.set_wlm_output(state))
        # channel wavemeter settings
        for channel_name, channel_params in self.chaninfo.items():
            # expand parameters and get GUI widget
            wmChannel, frequency, _, _, dacPort, _ = channel_params
            widget = self.gui.channels[wmChannel]
            # assign slots
            widget.showTrace.clicked.connect(lambda status, _wmChannel=wmChannel:
                                             self.toggleTrace(status, _wmChannel))
            widget.setPID.clicked.connect(lambda status, _wmChannel=wmChannel, _dacPort=dacPort:
                                          self.setupPID(_wmChannel, _dacPort))
            widget.spinExp.valueChanged.connect(lambda exp, _wmChannel=wmChannel:
                                                self.wavemeter.set_exposure_time(_wmChannel, int(exp)))
            widget.measSwitch.clicked.connect(lambda state, _wmChannel=wmChannel:
                                              self.wavemeter.set_switcher_signal_state(_wmChannel, state))
            if dacPort != 0:
                widget.spinFreq.valueChanged.connect(lambda freq, _dacPort=dacPort:
                                                     self.wavemeter.set_pid_course(_dacPort, freq))
                widget.lockChannel.clicked.connect(lambda state, _dacPort=dacPort, _wmChannel=wmChannel:
                                                   self.wavemeter.set_channel_lock(_dacPort, _wmChannel, state))
            # lock channels on startup to prevent accidental change of values
            widget.lockswitch.setChecked(False)
            # frequency recording
            widget.record_button.toggled.connect(lambda status, _wmChannel=wmChannel: self.record_freq(status, _wmChannel))
        # finally after everything has been set up, we can start polling wavemeter values
        self.refresher.start(_TRACE_POLLING_RATE, now=True)

    @inlineCallbacks
    def setupPID(self, channel, dacPort):
        pidGUI = self.gui.pidGUI
        channel_widget = self.gui.channels[channel]
        # channel details
        if channel_widget.lockChannel.isChecked():
            pidGUI.active_status.setText('Active')
            pidGUI.active_status.setStyleSheet('background-color: green')
        else:
            pidGUI.active_status.setText('Inactive')
            pidGUI.active_status.setStyleSheet('background-color: red')
        pidGUI.channelNum.setText(str(channel))
        pidGUI.dacPort_display.setText(str(dacPort))
        freq_val = channel_widget.spinFreq.value()
        pidGUI.lock_freq.setText('{:.4f}'.format(freq_val))
        # get initial values
        pInit = yield self.wavemeter.get_pid_p(dacPort)
        iInit = yield self.wavemeter.get_pid_i(dacPort)
        dInit = yield self.wavemeter.get_pid_d(dacPort)
        dtInit = yield self.wavemeter.get_pid_dt(dacPort)
        constInit = yield self.wavemeter.get_const_dt(dacPort)
        sensInit = yield self.wavemeter.get_pid_sensitivity(dacPort)
        polInit = yield self.wavemeter.get_pid_polarity(dacPort)
        # set initial values
        pidGUI.spinP.setValue(pInit)
        pidGUI.spinI.setValue(iInit)
        pidGUI.spinD.setValue(dInit)
        pidGUI.spinDt.setValue(dtInit)
        pidGUI.useDTBox.setChecked(constInit)
        pidGUI.spinFactor.setValue(sensInit[0])
        pidGUI.spinExp.setValue(sensInit[1])
        pidGUI.polarityBox.setCurrentIndex({1: 0, -1: 1}[polInit])
        # connect signals to slots
        self.gui.pidGUI.spinP.valueChanged.connect(lambda p, _dacPort=dacPort: self.wavemeter.set_pid_p(_dacPort, p))
        self.gui.pidGUI.spinI.valueChanged.connect(lambda i, _dacPort=dacPort: self.wavemeter.set_pid_p(_dacPort, i))
        self.gui.pidGUI.spinD.valueChanged.connect(lambda d, _dacPort=dacPort: self.wavemeter.set_pid_p(_dacPort, d))
        self.gui.pidGUI.spinDt.valueChanged.connect(lambda dt, _dacPort=dacPort: self.wavemeter.set_pid_dt(_dacPort, dt))
        self.gui.pidGUI.useDTBox.stateChanged.connect(lambda state, _dacPort=dacPort: self.wavemeter.set_const_dt(dacPort, state))
        self.gui.pidGUI.spinFactor.valueChanged.connect(lambda factor, _dacPort=dacPort, exp=self.gui.pidGUI.spinExp.value():
                                                     self.wavemeter.set_pid_sensitivity(dacPort, factor, int(exp)))
        self.gui.pidGUI.spinExp.valueChanged.connect(lambda exp, _dacPort=dacPort, factor=self.gui.pidGUI.spinFactor.value():
                                                  self.wavemeter.set_pid_sensitivity(dacPort, factor, int(exp)))
        self.gui.pidGUI.polarityBox.currentIndexChanged.connect(lambda index, _dacPort=dacPort: self.changePolarity(index, _dacPort))


    # SLOTS
    @inlineCallbacks
    def updateFrequency(self, c, signal):
        chan, freq = signal
        if chan in self.gui.channels.keys():
            freq_tmp = float('NaN')
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
                freq_tmp = freq
            record_params = self.record_dict[chan]
            if record_params['status']:
                starttime = record_params['starttime']
                cntx = record_params['context']
                elapsedtime = time() - starttime
                try:
                    yield self.dv.add(elapsedtime, freq_tmp, context=cntx)
                except Exception as e:
                    pass

    def updatePIDvoltage(self, c, signal):
        dacPort, value = signal
        try:
            active_dacPort = int(self.gui.pidGUI.dacPort_display.text())
            if (dacPort in self.gui.dacPorts) and (dacPort == active_dacPort):
                try:
                    self.gui.pidGUI.PIDvoltage.setText('{:4.2f}'.format(value))
                    self.gui.pidGUI.PIDindicator.updateSlider(value / 1000.0)
                except Exception as e:
                    print(e)
        except Exception as e:
            pass

    def updateExp(self, c, signal):
        chan, value = signal
        if chan in self.gui.channels.keys():
            self.gui.channels[chan].spinExp.blockSignals(True)
            self.gui.channels[chan].spinExp.setValue(value)
            self.gui.channels[chan].spinExp.blockSignals(False)

    def updateWMOutput(self, c, signal):
        self.gui.startSwitch.setChecked(signal)

    def updateAmplitude(self, c, signal):
        chan, value = signal
        if chan in self.gui.channels.keys():
            value = int(value)
            self.gui.channels[chan].powermeter.setValue(value)
            self.gui.channels[chan].powermeter_display.setText('{:4d}'.format(value))

    def updatePattern(self, c, signal):
        """
        This is not currently in use since patterns
        are received too frequently from the wavemeter server,
        creating considerable overhead (about 1Mbps per channel).
        """
        chan, trace = signal
        num_points = 512
        if chan in self.gui.pattern.keys():
            self.gui.pattern[chan].setData(x=linspace(0, 2000, num_points), y=trace)

    @inlineCallbacks
    def pollPattern(self):
        num_points = 512
        for chan in self.gui.pattern.keys():
            trace = yield self.wavemeter.get_wavemeter_pattern(chan)
            self.gui.pattern[chan].setData(x=linspace(0, 2000, num_points), y=trace[0])

    def toggleTrace(self, status, chan):
        trace = self.gui.pattern[chan]
        if status:
            self.gui.trace_display.addItem(trace)
        else:
            self.gui.trace_display.removeItem(trace)

    def toggleMeas(self, c, signal):
        chan, state = signal
        if chan in self.gui.channels.keys():
            self.gui.channels[chan].setChecked(state)

    def toggleLock(self, c, signal):
        self.gui.lockSwitch.setChecked(signal)

    def toggleChannelLock(self, c, signal):
        _, chan, state = signal
        if chan in self.gui.channels.keys():
            self.gui.channels[chan].lockChannel.setChecked(bool(state))

    @inlineCallbacks
    def changePolarity(self, index, dacPort):
        if index == 0:
            yield self.wavemeter.set_pid_polarity(dacPort, 1)
        else:
            yield self.wavemeter.set_pid_polarity(dacPort, -1)

    @inlineCallbacks
    def record_freq(self, status, channel):
        record_params = self.record_dict[channel]
        # create trunk
        record_params['status'] = status
        if status:
            record_params['starttime'] = time()
            cntx = record_params['context']
            trunk_tmp = createTrunk(self.name)
            dataset_name = record_params['name']
            # reassign parameters first to minimize yielding
            self.record_dict[channel] = record_params
            # create dataset
            yield self.dv.cd(trunk_tmp, True, context=cntx)
            yield self.dv.new(dataset_name, [('Elapsed time', 't')],
                              [('Laser', 'Frequency', 'THz')], context=cntx)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(multiplexer_client)
