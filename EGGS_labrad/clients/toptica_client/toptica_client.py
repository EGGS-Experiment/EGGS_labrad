from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.toptica_client.toptica_gui import toptica_gui

TOPTICA_CHANNELS = [(1, 'DLpro (S/N 029432)', '397'),
                    (2, 'DLpro (S/N 022111)', '852.36'),
                    (3, 'DLpro (S/N 029431)', '422'),
                    (4, 'DLpro (S/N 021957)', '850')]

CURRENTUPDATED_ID = 192611
TEMPERATUREUPDATED_ID = 192612
PIEZOUPDATED_ID = 192613


class toptica_client(GUIClient):

    name = 'Toptica Client'
    servers = {'toptica': 'toptica_server'}

    def getgui(self):
        if self.gui is None:
            self.gui = toptica_gui(TOPTICA_CHANNELS)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # get config
        self.channelinfo = yield self.toptica.device_list()
        # connect to device signals
        yield self.toptica.signal__current_updated(CURRENTUPDATED_ID)
        yield self.toptica.addListener(listener=self.updateCurrent, source=None, ID=CURRENTUPDATED_ID)
        yield self.toptica.signal__temperature_updated(TEMPERATUREUPDATED_ID)
        yield self.toptica.addListener(listener=self.updateTemperature, source=None, ID=TEMPERATUREUPDATED_ID)
        yield self.toptica.signal__piezo_updated(PIEZOUPDATED_ID)
        yield self.toptica.addListener(listener=self.updatePiezo, source=None, ID=PIEZOUPDATED_ID)
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # start device polling if not already started
        poll_params = yield self.toptica.polling()
        if not poll_params[0]:
            yield self.toptica.polling(True, 5.0)

    @inlineCallbacks
    def initData(self):
        self.gui.makeLayout(self.channelinfo)
        self.gui.show()
        # set display for each channel
        for chan_num, widget in self.gui.channels.items():
            # status
            _, name, wav, _, _, _, _ = yield self.toptica.device_info(chan_num)
            emission_status = yield self.toptica.emission(chan_num)
            widget.statusBox.channelDisplay.setText(str(chan_num))
            name_tmp = name[1].split('S/N ')[1]
            name_tmp = name_tmp[:-1]
            widget.statusBox.serDisplay.setText(name_tmp)
            widget.statusBox.wavDisplay.setText(wav[1])
            widget.statusBox.emissionButton.setChecked(emission_status)
            # feedback
            # todo
            # current
            current_set = yield self.toptica.current_set(chan_num)
            current_max = yield self.toptica.current_max(chan_num)
            widget.currBox.setBox.setValue(current_set)
            widget.currBox.maxBox.setValue(current_max)
            widget.currBox.lockswitch.setChecked(False)
            # temperature
            temperature_set = yield self.toptica.temperature_set(chan_num)
            temperature_max = yield self.toptica.temperature_max(chan_num)
            widget.tempBox.setBox.setValue(temperature_set)
            widget.tempBox.maxBox.setValue(temperature_max)
            widget.tempBox.lockswitch.setChecked(False)
            # piezo
            piezo_set = yield self.toptica.piezo_set(chan_num)
            piezo_max = yield self.toptica.piezo_max(chan_num)
            widget.piezoBox.setBox.setValue(piezo_set)
            widget.piezoBox.maxBox.setValue(piezo_max)
            widget.piezoBox.lockswitch.setChecked(False)
            # scan
            scan_freq = yield self.toptica.scan_frequency(chan_num)
            scan_amp = yield self.toptica.scan_amplitude(chan_num)
            scan_off = yield self.toptica.scan_offset(chan_num)
            widget.scanBox.freqBox.setValue(scan_freq)
            widget.scanBox.ampBox.setValue(scan_amp)
            widget.scanBox.offBox.setValue(scan_off)
            widget.scanBox.lockswitch.setChecked(False)

    def initGUI(self):
        # laser channel settings
        for chan_num, widget in self.gui.channels.items():
            #todo: set emission button, assign feedback slots, assign current slots
            widget.currBox.setBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.current_set(_chan_num, value))
            widget.currBox.maxBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.current_max(_chan_num, value))
            # assign temperature slots
            widget.tempBox.setBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.temperature_set(_chan_num, value))
            widget.tempBox.maxBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.temperature_max(_chan_num, value))
            # assign piezo slots
            if widget.piezo:
                # assign temperature slots
                widget.piezoBox.setBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.piezo_set(_chan_num, value))
                widget.piezoBox.maxBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.piezo_max(_chan_num, value))
            # assign scan slots
            #widget.scanBox.modeBox.currentItemChanged.connect(lambda index, _chan_num=chan_num: self.toptica.scan_mode(_chan_num, index))
            #widget.scanBox.shapeBox.currentItemChanged.connect(lambda index, _chan_num=chan_num: self.toptica.scan_shape(_chan_num, index))
            widget.scanBox.freqBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.scan_frequency(_chan_num, value))
            widget.scanBox.ampBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.scan_amplitude(_chan_num, value))
            widget.scanBox.offBox.valueChanged.connect(lambda value, _chan_num=chan_num: self.toptica.scan_offset(_chan_num, value))


    # SLOTS
    def updateCurrent(self, c, signal):
        chan_num, curr = signal
        if chan_num in self.gui.channels.keys():
            self.gui.channels[chan_num].currBox.actualValue.setText('{:0.4f}'.format(curr))

    def updateTemperature(self, c, signal):
        chan_num, temp = signal
        if chan_num in self.gui.channels.keys():
            self.gui.channels[chan_num].tempBox.actualValue.setText('{:0.4f}'.format(temp))

    def updatePiezo(self, c, signal):
        chan_num, voltage = signal
        if chan_num in self.gui.channels.keys():
            self.gui.channels[chan_num].piezoBox.actualValue.setText('{:0.4f}'.format(voltage))


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(toptica_client)
