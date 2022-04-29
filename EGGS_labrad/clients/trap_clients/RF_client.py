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
        # find desired device
        devices = yield self.rf.list_devices()
        for dev_id in devices:
            dev_name = dev_id[1]
            if 'GPIB0::1::INSTR' in dev_name:
                yield self.rf.select_device(dev_name)

    @inlineCallbacks
    def initData(self):
        # get and assign parameters
        freq = yield self.rf.frequency()
        ampl = yield self.rf.amplitude()
        mod_freq = yield self.rf.modulation_frequency()
        fm_dev = yield self.rf.modulation_fm_deviation()
        am_depth = yield self.rf.modulation_am_depth()
        pm_dev = yield self.rf.modulation_pm_deviation()
        self.gui.wav_ampl.setValue(ampl)
        self.gui.wav_freq.setValue(freq / 1000000)
        self.gui.mod_freq.setValue(mod_freq / 1000)
        self.gui.mod_freq_dev.setValue(fm_dev / 1000)
        self.gui.mod_ampl_depth.setValue(am_depth)
        self.gui.mod_phase_dev.setValue(pm_dev)
        # get toggle status
        power_status = yield self.rf.toggle()
        am_toggle = yield self.rf.toggle_am()
        pm_toggle = yield self.rf.toggle_pm()
        fm_toggle = yield self.rf.toggle_fm()
        self.gui.wav_toggle.setChecked(power_status)
        self.gui.mod_ampl_toggle.setChecked(am_toggle)
        self.gui.mod_ampl_toggle.setChecked(pm_toggle)
        self.gui.mod_ampl_toggle.setChecked(fm_toggle)

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
        self.gui.mod_ampl_depth.valueChanged.connect(lambda ampl_depth: self.rf.modulation_am_depth(ampl_depth))
        self.gui.mod_freq_dev.valueChanged.connect(lambda freq_dev: self.rf.modulation_fm_deviation(freq_dev))
        self.gui.mod_phase_dev.valueChanged.connect(lambda pm_dev: self.rf.modulation_pm_deviation(pm_dev))
        # on/off buttons
        self.gui.mod_freq_toggle.clicked.connect(lambda status: self.rf.toggle_fm(status))
        self.gui.mod_ampl_toggle.clicked.connect(lambda status: self.rf.toggle_am(status))
        self.gui.mod_phase_toggle.clicked.connect(lambda status: self.rf.toggle_pm(status))
        # set lockswitch to locked
        self.gui.wav_lockswitch.setChecked(False)
        self.gui.wav_lockswitch.click()


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
    runClient(RF_client)
