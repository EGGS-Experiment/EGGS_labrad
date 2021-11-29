import os

from twisted.internet.defer import inlineCallbacks, Deferred
from EGGS_labrad.lib.clients.trap_clients.rf_gui import rf_gui

from PyQt5.QtWidgets import QWidget

class rf_client(rf_gui):

    name = 'RF Client'

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn=cxn
        self.gui = self
        self.reactor = reactor
        self.connect()
        self.gui.setupUi()

    # Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to labrad
        """
        # use connection object since we need
        # to wait until servers are all connected
        if not self.cxn:
            from EGGS_labrad.lib.clients.connection import connection
            self.cxn = connection()
            yield self.cxn.connect()

        #add following servers to connection for future use
        try:
            yield self.cxn.get_server('Registry')
            yield self.cxn.get_server('Data Vault')
            yield self.cxn.get_server('RF Server')
        except Exception as e:
            print(e)
            raise

        try:
            yield self.selectDevice()
            yield self.initializeGUI()
            yield self.getDeviceParams()
        except Exception as e:
            print(e)
            raise

        #initialize client when rf server is connected
        yield self.cxn.add_on_connect('RF Server', self.selectDevice)
        yield self.cxn.add_on_connect('RF Server', self.initializeGUI)
        yield self.cxn.add_on_connect('RF Server', self.getDeviceParams)
        #prevent changes when rf server disconnects
        #yield self.cxn.add_on_disconnect('RF Server', self.lock())

    @inlineCallbacks
    def initializeGUI(self):
        # print('init s')
        rf = yield self.cxn.get_server('RF Server')
        # waveform
            #parameters
        self.gui.wav_freq.valueChanged.connect(lambda freq: (rf.frequency(freq * 1000)))
        self.gui.wav_ampl.valueChanged.connect(lambda ampl, units='DBM': rf.amplitude(ampl, units))
            #buttons
        self.gui.wav_toggle.clicked.connect(lambda status: rf.toggle(status))
        self.gui.wav_lockswitch.clicked.connect(lambda status: self.lock(status))
        self.gui.wav_reset.clicked.connect(lambda: self.reset())
        # modulation
            #parameters
        self.gui.mod_freq.valueChanged.connect(lambda freq: rf.modulation_frequency(freq * 1000))
        self.gui.mod_ampl_depth.valueChanged.connect(lambda ampl_depth: rf.am_depth(ampl_depth))
        self.gui.mod_freq_dev.valueChanged.connect(lambda freq_dev: rf.fm_dev(freq_dev))
        self.gui.mod_phase_dev.valueChanged.connect(lambda pm_dev: rf.pm_dev(pm_dev))
            #on/off buttons
        self.gui.mod_freq_toggle.clicked.connect(lambda status: rf.fm_toggle(status))
        self.gui.mod_ampl_toggle.clicked.connect(lambda status: rf.am_toggle(status))
        self.gui.mod_phase_toggle.clicked.connect(lambda status: rf.pm_toggle(status))
        # print('init e')

    @inlineCallbacks
    def selectDevice(self):
        # print('sel s')
        rf = yield self.cxn.get_server('RF Server')
        yield rf.select_device()
        # print('sel e')

    @inlineCallbacks
    def getDeviceParams(self):
        # print('gdp s')
        rf = yield self.cxn.get_server('RF Server')
        try:
            freq = yield rf.frequency()
            self.gui.wav_freq.setValue(freq / 1000)
            ampl = yield rf.amplitude()
            self.gui.wav_ampl.setValue(ampl)
            mod_freq = yield rf.modulation_frequency()
            self.gui.mod_freq.setValue(mod_freq / 1000)
            fm_dev = yield rf.fm_deviation()
            self.gui.mod_freq_dev.setValue(fm_dev / 1000)
            am_depth = yield rf.am_depth()
            self.gui.mod_ampl_depth.setValue(am_depth)
            pm_dev = yield rf.pm_deviation()
            self.gui.mod_phase_dev.setValue(pm_dev)
        except Exception as e:
            print(e)
        # print('gdp e')


    @inlineCallbacks
    def reset(self):
        """
        Resets RF client buttons and sends reset signal to server.
        """
        rf = yield self.cxn.get_server('RF Server')
        #call reset
        yield rf.reset()
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
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__=="__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(rf_client)