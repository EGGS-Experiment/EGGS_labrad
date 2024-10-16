from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.trap_clients.RF_gui import RF_gui


class RF_client(GUIClient):

    name = 'RF Client'
    servers = {'rf': 'RF Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = RF_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # find main signal generator
        devices = yield self.rf.list_devices()
        for dev_id in devices:
            dev_name = dev_id[1]

            # select main signal generator
            if 'GPIB1::19::INSTR' in dev_name:
                yield self.rf.select_device(dev_name)

    @inlineCallbacks
    def initData(self):
        # get and assign parameters
        freq = yield self.rf.frequency()
        ampl = yield self.rf.amplitude()
        self.gui.wav_ampl.setValue(ampl)
        self.gui.wav_freq.setValue(freq / 1000000.)

        # get toggle status
        power_status =  yield self.rf.toggle()
        self.gui.wav_toggle.setChecked(power_status)

    def initGUI(self):
        # waveform parameters
        self.gui.wav_freq.valueChanged.connect(lambda freq: (self.rf.frequency(freq * 1000000)))
        self.gui.wav_ampl.valueChanged.connect(lambda ampl, units='DBM': self.rf.amplitude(ampl, units))
        # waveform buttons
        self.gui.wav_toggle.clicked.connect(lambda status: self.rf.toggle(status))
        self.gui.wav_lockswitch.clicked.connect(lambda status: self.lock(status))
        # set lockswitch to locked
        self.gui.wav_lockswitch.setChecked(False)
        self.gui.wav_lockswitch.click()


    # SLOTS
    def lock(self, status):
        """
        Locks signal generator interface.
        """
        # waveform parameters
        self.gui.wav_ampl.setEnabled(status)
        self.gui.wav_freq.setEnabled(status)
        self.gui.wav_toggle.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(RF_client)
