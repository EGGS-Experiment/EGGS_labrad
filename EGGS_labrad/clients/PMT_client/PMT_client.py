from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.PMT_client.PMT_gui import PMT_gui


class PMT_client(GUIClient):

    name = 'PMT Client'
    servers = {'artiq': 'ARTIQ Server', 'dv': 'Data Vault'}

    def getgui(self):
        if self.gui is None:
            self.gui = PMT_gui()
        return self.gui

    def initClient(self):
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        # create polling loop
        self.refresher = LoopingCall(self.update_counts)

    @inlineCallbacks
    def initData(self):
        self.gui.sample_time.setValue(500)
        self.gui.sample_num.setValue(100)
        self.gui.poll_interval.setValue(4)

    def initGUI(self):
        # read buttons
        self.gui.read_once_switch.toggled.connect(lambda status: self.read_counts())
        self.gui.read_cont_switch.toggled.connect(lambda status, _poll_time=self.gui.poll_interval.value(): self.refresher.start(_poll_time, now=True))
        # start up locked
        self.gui.lockswitch.setChecked(False)


    # SLOTS
    @inlineCallbacks
    def update_counts(self):
        sample_time_us = self.gui.sample_time.value()
        num_samples = self.gui.sample_num.value()
        counts = yield self.aq.ttl_counter('ttl_counter{:d}'.format(0), sample_time_us, num_samples)
        self.gui.count_display.setText("{:.2f}".format(counts))

    def toggle_polling(self, status):
        # start if not running
        if status and (not self.refresher.running):
            poll_interval_s = self.gui.poll_interval.value()
            self.refresher.start(poll_interval_s, now=True)
            # disable read once button
            self.gui.read_once_switch.setEnabled(False)
        # stop if running
        elif (not status) and (self.refresher.running):
            self.refresher.stop()
            self.gui.read_once_switch.setEnabled(True)

    def lock(self, status):
        self.gui.read_once_switch.setEnabled(status)
        self.gui.read_cont_switch.setEnabled(status)
        self.gui.sample_time.setEnabled(status)
        self.gui.sample_num.setEnabled(status)
        self.gui.poll_interval.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(PMT_client)
