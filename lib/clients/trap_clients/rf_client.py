import os

from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.lib.clients.trap_clients.rf_gui import rf_gui

from PyQt5.QtWidgets import QWidget

class rf_client(object):
    name = 'RF Client'

    def __init__(self, reactor, parent=None):
        self.gui = rf_gui()
        self.reactor = reactor
        self.connect()
        self.initializeGUI()

    #Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad
        """
        import os
        LABRADHOST = os.environ['LABRADHOST']
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        self.reg = self.cxn.registry
        self.dv = self.cxn.data_vault
        self.rf = self.cxn.rf_server
        #todo: ensure device is selected

        yield self.rf.select_device()

    #@inlineCallbacks
    def initializeGUI(self):
        self.gui.setupUi()
        # waveform
            #parameters
        self.gui.wav_freq.valueChanged.connect(lambda freq: (self.rf.frequency(freq * 1000)))
        self.gui.wav_ampl.valueChanged.connect(lambda ampl, units='DBM': self.rf.amplitude(ampl, units))
            #buttons
        self.gui.wav_toggle.clicked.connect(lambda status: self.rf.toggle(status))
        self.gui.wav_lockswitch.clicked.connect(lambda status: self.lock(status))
        self.gui.wav_reset.clicked.connect(lambda: self.reset())
        # modulation
            #parameters
        self.gui.mod_freq.valueChanged.connect(lambda freq: self.rf.mod_freq(freq * 1000))
        self.gui.mod_ampl_depth.valueChanged.connect(lambda ampl_depth: self.rf.am_depth(ampl_depth))
        self.gui.mod_freq_dev.valueChanged.connect(lambda freq_dev: self.rf.fm_dev(freq_dev))
        self.gui.mod_phase_dev.valueChanged.connect(lambda pm_dev: self.rf.pm_dev(pm_dev))
            #on/off buttons
        self.gui.mod_freq_toggle.clicked.connect(lambda status: self.rf.fm_toggle(status))
        self.gui.mod_ampl_toggle.clicked.connect(lambda status: self.rf.am_toggle(status))
        self.gui.mod_phase_toggle.clicked.connect(lambda status: self.rf.pm_toggle(status))

        #yield self.getDeviceParams()

    @inlineCallbacks
    def getDeviceParams(self):
        """
        Gets default/startup values from device.
        """
        freq = yield self.rf.frequency()
        self.gui.wav_freq.setValue(freq / 1000)
        ampl = self.rf.amplitude()
        self.gui.wav_ampl.setValue(ampl)
        mod_freq = self.rf.mod_freq()
        self.gui.mod_freq.setValue(mod_freq / 1000)
        fm_dev = self.rf.fm_dev()
        self.gui.mod_freq_dev.setValue(fm_dev / 1000)
        am_depth = self.rf.am_depth()
        self.gui.mod_ampl_depth.setValue(am_depth)
        pm_dev = self.rf.pm_dev()
        self.gui.mod_phase_dev.setValue(pm_dev)
        onoff_status = self.rf.toggle()
        self.gui.wav_toggle.setChecked(onoff_status)
        am_status = self.rf.am_toggle()
        self.gui.wav_toggle.setChecked(am_status)
        fm_status = self.rf.fm_toggle()
        self.gui.wav_toggle.setChecked(fm_status)
        pm_status = self.rf.pm_toggle()
        self.gui.wav_toggle.setChecked(pm_status)

    @inlineCallbacks
    def reset(self):
        """
        Resets RF client buttons and sends reset signal to server.
        """
        #call reset
        yield self.rf.reset()
        #set parameters to device defaults
        yield self.getDeviceParams()

    def lock(self, status):
        """
        Locks signal generator interface.
        """
        # invert since textchangingbutton is weird
        status = not status
        # waveform
        self.gui.wav_ampl.setEnabled(status)
        self.gui.wav_freq.setEnabled(status)
        self.gui.wav_toggle.setEnabled(status)
        self.gui.wav_reset.setEnabled(status)
        # modulation
            # parameters
        self.gui.mod_freq.setEnabled(status)
        self.gui.mod_freq_dev.setEnabled(status)
        self.gui.mod_ampl_depth.setEnabled(status)
        self.gui.mod_phase_dev.setEnabled(status)
            # buttons
        self.gui.mod_ampl_toggle.setEnabled(status)
        self.gui.mod_freq_toggle.setEnabled(status)
        self.gui.mod_phase_toggle.setEnabled(status)

    def closeEvent(self, event):
        self.reactor.stop()

if __name__=="__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(rf_client)

