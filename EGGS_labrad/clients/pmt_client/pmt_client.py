from twisted.internet.defer import inlineCallbacks
from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.pmt_client.pmt_gui import PMT_gui


class PMT_client(GUIClient):
    """

    """

    servers = ['PMT Server', 'ARTIQ Server']
    gui = PMT_gui('PMT Client')

    @inlineCallbacks
    def initClient(self, cxn):
        """
        Get necessary servers.
        """
        try:
            self.pmt = yield self.cxn.pmt_server
            self.artiq = yield self.cxn.artiq_server
        except Exception as e:
            print(e)
            raise

    @inlineCallbacks
    def initData(self, cxn):
        """
        Get startup data from servers and show on GUI.
        """
        try:
            # get available TTLInOuts
            ttl_list = yield self.pmt.ttl_available()
            ttl_list = [ttl_name[3:] for ttl_name in ttl_list]
            for ttl_name in ttl_list:
                self.gui.ttl_pmt.addItem(ttl_name)
                self.gui.ttl_trig.addItem(ttl_name)
            # devices
            pmt_chan = yield self.pmt.ttl_pmt()
            trig_active, trig_chan = yield self.pmt.ttl_trigger()
            self.gui.ttl_pmt.setCurrentIndex(pmt_chan)
            self.gui.trigger_active.setChecked(trig_active)
            self.gui.ttl_trig.setCurrentIndex(trig_chan)
            # timing
            t_bin = yield self.pmt.gating_time()
            t_delay = yield self.pmt.gating_delay()
            t_length = yield self.pmt.length()
            self.gui.time_record.setValue(t_bin)
            self.gui.time_delay.setValue(t_delay)
            self.gui.time_length.setValue(t_length)
            # running
            edge_method = yield self.pmt.gating_edge()
            ind = self.gui.edge_method.findText(edge_method)
            self.gui.edge_method.setCurrentIndex(ind)


    def initializeGUI(self, cxn):
        """
        Connect signals to slots.
        """
        # device
        self.gui.ttl_pmt.currentTextChanged.connect(lambda text: self.pmt.ttl_pmt(int(text)))
        self.gui.ttl_trig.currentTextChanged.connect(lambda text, status=self.pmt_: self.pmt.ttl_trigger(int(text)))
        self.gui.trigger_active.toggled.connect(lambda status: self.pmt.ttl_trigger(status))
        # timing
        self.gui.time_record.valueChanged.connect(lambda value: self.pmt.gating_time(value))
        self.gui.time_delay.valueChanged.connect(lambda value: self.pmt.gating_delay(value))
        self.gui.length.valueChanged.connect(lambda value: self.pmt.length(value))
        # edge
        self.gui.time_delay.currentTextChanged.connect(lambda type: self.pmt.gating_edge(type))
        # buttons
        self.gui.program_button.clicked.connect(lambda: self.pmt.program())
        self.gui.start_button.clicked.connect(lambda: self.pmt.start())
        self.gui.lockswitch.toggled.connect(lambda status: self.lock(status))


    # SLOTS
    def lock(self, status):
        self.gui.setEnabled(status)
        self.gui.lockswitch.setEnabled(True)





if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(PMT_gui)
