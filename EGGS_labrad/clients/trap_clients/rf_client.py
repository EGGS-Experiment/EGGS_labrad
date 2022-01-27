import os

from twisted.internet.defer import inlineCallbacks, Deferred
from EGGS_labrad.clients.trap_clients.rf_gui import rf_gui

from PyQt5.QtWidgets import QWidget

class rf_client(rf_gui):

    name = 'RF Client'

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.gui.setupUi()
        self.reactor = reactor
        self.servers = ['RF Server', 'Data Vault']
        # initialization sequence
        d = self.connect()
        d.addCallback(self.initData)
        d.addCallback(self.initializeGUI)

    # Setup functions
    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to utils.
        """
        # create connection to utils manager
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        # add following servers to connection for future use
        try:
            self.dv = yield self.cxn.data_vault
            self.rf = yield self.cxn.rf_server
        except Exception as e:
            print(e)

        # connect to signals
            # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)
        return self.cxn

    @inlineCallbacks
    def initData(self, cxn):
        """
        Get startup data from servers and show on GUI.
        """
        # lock while starting up
        self.setEnabled(False)

        freq = yield self.rf.frequency()
        self.gui.wav_freq.setValue(freq / 1000)
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
        self.setEnabled(True)
        return cxn

    def initializeGUI(self):
        """
        Connect signals to slots and other initializations.
        """
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
        self.gui.mod_freq.valueChanged.connect(lambda freq: self.rf.modulation_frequency(freq * 1000))
        self.gui.mod_ampl_depth.valueChanged.connect(lambda ampl_depth: self.rf.am_depth(ampl_depth))
        self.gui.mod_freq_dev.valueChanged.connect(lambda freq_dev: self.rf.fm_dev(freq_dev))
        self.gui.mod_phase_dev.valueChanged.connect(lambda pm_dev: self.rf.pm_dev(pm_dev))
            #on/off buttons
        self.gui.mod_freq_toggle.clicked.connect(lambda status: self.rf.fm_toggle(status))
        self.gui.mod_ampl_toggle.clicked.connect(lambda status: self.rf.am_toggle(status))
        self.gui.mod_phase_toggle.clicked.connect(lambda status: self.rf.pm_toggle(status))


    # SIGNALS
    @inlineCallbacks
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' reconnected, enabling widget.')
            # get latest values
            yield self.initData(self.cxn)
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' disconnected, disabling widget.')
            self.setEnabled(False)


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


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(rf_client)