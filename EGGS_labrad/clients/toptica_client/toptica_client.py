from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.config.toptica_config import toptica_config
from EGGS_labrad.clients.toptica_client.toptica_gui import toptica_gui

FREQ_CHANGED_ID = 445566
CHANNEL_CHANGED_ID = 143533
UPDATEEXP_ID = 111221
LOCK_CHANGED_ID = 549210
OUTPUT_CHANGED_ID = 190909
PID_CHANGED_ID = 102588
CHAN_LOCK_CHANGED_ID = 148323
AMPLITUDE_CHANGED_ID = 238883
PATTERN_CHANGED_ID = 462917


class toptica_client(GUIClient):

    name = 'Toptica Client'
    servers = {'toptica': 'toptica_server'}

    def getgui(self):
        if self.gui is None:
            self.gui = toptica_gui(toptica_config)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # get config
        self.chaninfo = toptica_config
        # connect to device signals
        yield self.toptica.signal__frequency_changed(FREQ_CHANGED_ID)
        yield self.toptica.addListener(listener=self.updateFrequency, source=None, ID=FREQ_CHANGED_ID)
        yield self.toptica.signal__selected_channels_changed(CHANNEL_CHANGED_ID)
        yield self.toptica.addListener(listener=self.toggleMeas, source=None, ID=CHANNEL_CHANGED_ID)
        yield self.toptica.signal__update_exp(UPDATEEXP_ID)
        yield self.toptica.addListener(listener=self.updateExp, source=None, ID=UPDATEEXP_ID)
        yield self.toptica.signal__lock_changed(LOCK_CHANGED_ID)
        yield self.toptica.addListener(listener=self.updateWMOutput, source=None, ID=OUTPUT_CHANGED_ID)
        yield self.toptica.signal__output_changed(OUTPUT_CHANGED_ID)

    @inlineCallbacks
    def initData(self):
        # set display for each channel
        for channel_name, channel_params in self.chaninfo.items():
            widget = self.gui.channels[wmChannel]
            # get channel values
            lock_frequency = yield self.toptica.get_pid_course(dacPort)
            lock_status = yield self.toptica.get_channel_lock(dacPort, wmChannel)
            exposure_ms = yield self.toptica.get_exposure(wmChannel)
            measure_state = yield self.toptica.get_switcher_signal_state(wmChannel)
            widget.lockChannel.setChecked(bool(lock_status))
            widget.spinExp.setValue(exposure_ms)
            widget.measSwitch.setChecked(bool(measure_state))
            widget.spinFreq.setValue(float(lock_frequency))

    def initGUI(self):
        # laser channel settings
        for chan_num, channel_params in self.chaninfo.items():
            # expand parameters and get GUI widget
            wmChannel, frequency, _, _, dacPort, _ = channel_params
            widget = self.gui.channels[wmChannel]
            # assign feedback slots
            # todo
            # assign current slots
            widget.currBox.setBox.valueChanged.connect(lambda value, _chan_num: self.toptica.current_set(_chan_num, value))
            widget.currBox.minBox.valueChanged.connect(lambda value, _chan_num: self.toptica.current_min(_chan_num, value))
            widget.currBox.maxBox.valueChanged.connect(lambda value, _chan_num: self.toptica.current_max(_chan_num, value))
            # assign temperature slots
            widget.tempBox.setBox.valueChanged.connect(lambda value, _chan_num: self.toptica.temperature_set(_chan_num, value))
            widget.tempBox.minBox.valueChanged.connect(lambda value, _chan_num: self.toptica.temperature_min(_chan_num, value))
            widget.tempBox.maxBox.valueChanged.connect(lambda value, _chan_num: self.toptica.temperature_max(_chan_num, value))
            # assign piezo slots
            if widget.piezo:
                # assign temperature slots
                widget.piezoBox.setBox.valueChanged.connect(lambda value, _chan_num: self.toptica.piezo_set(_chan_num, value))
                widget.piezoBox.minBox.valueChanged.connect(lambda value, _chan_num: self.toptica.piezo_min(_chan_num, value))
                widget.piezoBox.maxBox.valueChanged.connect(lambda value, _chan_num: self.toptica.piezo_max(_chan_num, value))
            # assign scan slots
            widget.scanBox.modeBox.currentItemChanged.
            widget.scanBox.freqBox.valueChanged.connect(lambda value, _chan_num: self.toptica.scan_frequency(_chan_num, value))
            widget.scanBox.ampBox.valueChanged.connect(lambda value, _chan_num: self.toptica.scan_amplitude(_chan_num, value))
            widget.scanBox.offBox.valueChanged.connect(lambda value, _chan_num: self.toptica.scan_offset(_chan_num, value))


    # SLOTS
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

    def updateAmplitude(self, c, signal):
        chan, value = signal
        if chan in self.gui.channels.keys():
            value = int(value)
            self.gui.channels[chan].powermeter.setValue(value)
            self.gui.channels[chan].powermeter_display.setText('{:4d}'.format(value))


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(toptica_client)
