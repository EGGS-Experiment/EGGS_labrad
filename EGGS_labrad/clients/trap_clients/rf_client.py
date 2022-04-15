from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.trap_clients.rf_gui import rf_gui


class rf_client(GUIClient):

    name = 'RF Client'
    servers = {'rf': 'RF Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = rf_gui()
        return self.gui

    @inlineCallbacks
    def initData(self):
        # lock while starting up
        self.gui.setEnabled(False)
        # select device
        yield self.rf.select_device()
        # get parameters
        freq = yield self.rf.frequency()
        self.gui.wav_freq.setValue(freq / 1000000)
        ampl = yield self.rf.amplitude()
        self.gui.wav_ampl.setValue(ampl)
        mod_freq = yield self.rf.modulation_frequency()
        self.gui.mod_freq.setValue(mod_freq / 1000)
        fm_dev = yield self.rf.fm_deviation()
        self.gui.mod_freq_dev.setValue(fm_dev / 1000)
        am_depth = yield self.rf.am_depth()
        self.gui.mod_ampl_depth.setValue(am_depth)
        pm_dev = yield self.rf.pm_deviation()
        self.gui.mod_phase_dev.setValue(pm_dev)
        # unlock after startup
        self.gui.setEnabled(True)

    def initGUI(self):
        # waveform parameters
        self.gui.wav_freq.valueChanged.connect(lambda freq: (self.rf.frequency(freq * 1000000)))
        self.gui.wav_ampl.valueChanged.connect(lambda ampl, units='DBM': self.rf.amplitude(ampl, units))
        # waveform buttons
        self.gui.wav_toggle.clicked.connect(lambda status: self.rf.toggle(status))
        self.gui.wav_lockswitch.clicked.connect(lambda status: self.lock(status))
        self.gui.wav_reset.clicked.connect(lambda: self.reset())
        # modulation parameters
        self.gui.mod_freq.valueChanged.connect(lambda freq: self.rf.modulation_frequency(freq * 1000))
        self.gui.mod_ampl_depth.valueChanged.connect(lambda ampl_depth: self.rf.am_depth(ampl_depth))
        self.gui.mod_freq_dev.valueChanged.connect(lambda freq_dev: self.rf.fm_dev(freq_dev))
        self.gui.mod_phase_dev.valueChanged.connect(lambda pm_dev: self.rf.pm_dev(pm_dev))
        # on/off buttons
        self.gui.mod_freq_toggle.clicked.connect(lambda status: self.rf.fm_toggle(status))
        self.gui.mod_ampl_toggle.clicked.connect(lambda status: self.rf.am_toggle(status))
        self.gui.mod_phase_toggle.clicked.connect(lambda status: self.rf.pm_toggle(status))


    # SLOTS
    @inlineCallbacks
    def reset(self):
        """
        Resets RF client buttons and sends reset signal to server.
        """
        # call reset
        yield self.rf.reset()
        # set parameters to device defaults
        yield self.initData(self.cxn)

    def lock(self, status):
        """
        Locks signal generator interface.
        """
        # invert since textchangingbutton is weird
        status = not status
        # waveform parameters
        self.gui.wav_ampl.setEnabled(status)
        self.gui.wav_freq.setEnabled(status)
        self.gui.wav_toggle.setEnabled(status)
        self.gui.wav_reset.setEnabled(status)
        # modulation parameters
        self.gui.mod_freq.setEnabled(status)
        self.gui.mod_freq_dev.setEnabled(status)
        self.gui.mod_ampl_depth.setEnabled(status)
        self.gui.mod_phase_dev.setEnabled(status)
        # modulation buttons
        self.gui.mod_ampl_toggle.setEnabled(status)
        self.gui.mod_freq_toggle.setEnabled(status)
        self.gui.mod_phase_toggle.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(rf_client)
