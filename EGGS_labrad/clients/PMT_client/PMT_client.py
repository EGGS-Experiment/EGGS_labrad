from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.PMT_client.PMT_gui import PMT_gui


class PMT_client(GUIClient):

    name = 'PMT Client'
    servers = {'pmt': 'PMT Server', 'artiq': 'ARTIQ Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = PMT_gui()
        return self.gui

    def initClient(self):
        pass

    @inlineCallbacks
    def initData(self):
        # get available TTLInOuts
        ttl_list = yield self.pmt.ttl_available()
        for ttl_name in ttl_list:
            self.gui.ttl_pmt.addItem(str(ttl_name))
            self.gui.ttl_trigger.addItem(str(ttl_name))
        # devices
        pmt_chan = yield self.pmt.ttl_pmt()
        trig_chan = yield self.pmt.ttl_trigger()
        trig_active = yield self.pmt.trigger_active()
        self.gui.ttl_pmt.setCurrentIndex(pmt_chan)
        self.gui.ttl_trigger.setCurrentIndex(trig_chan)
        self.gui.trigger_active.setChecked(trig_active)
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

    def initGUI(self):
        # todo: save data to datavault
        # device
        self.gui.ttl_pmt.currentTextChanged.connect(lambda text: self.pmt.ttl_pmt(int(text)))
        self.gui.ttl_trigger.currentTextChanged.connect(lambda text: self.pmt.ttl_trigger(int(text)))
        self.gui.trigger_active.toggled.connect(lambda status: self.pmt.trigger_active(status))
        # timing
        self.gui.time_record.valueChanged.connect(lambda value: self.pmt.gating_time(value))
        self.gui.time_delay.valueChanged.connect(lambda value: self.pmt.gating_delay(value))
        self.gui.time_length.valueChanged.connect(lambda value: self.pmt.length(value))
        # edge
        self.gui.edge_method.currentTextChanged.connect(lambda type: self.pmt.gating_edge(type))
        # buttons
        self.gui.program_button.clicked.connect(lambda: self.pmt.program())
        self.gui.program_button.clicked.connect(lambda: self.pmt.start())
        self.gui.lockswitch.toggled.connect(lambda status: self.lock(status))
        # start up locked
        self.gui.lockswitch.setChecked(False)


    # SLOTS
    def lock(self, status):
        self.gui.ttl_pmt.setEnabled(status)
        self.gui.ttl_trigger.setEnabled(status)
        self.gui.trigger_active.setEnabled(status)
        self.gui.time_record.setEnabled(status)
        self.gui.time_delay.setEnabled(status)
        self.gui.time_length.setEnabled(status)
        self.gui.edge_method.setEnabled(status)
        self.gui.program_button.setEnabled(status)
        self.gui.program_button.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(PMT_client)
