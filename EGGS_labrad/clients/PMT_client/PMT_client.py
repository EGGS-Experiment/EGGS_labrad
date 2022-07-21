from time import time
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.PMT_client.PMT_gui import PMT_gui


class PMT_client(GUIClient):

    name = 'PMT Client'
    servers = {'aq': 'ARTIQ Server', 'dv': 'Data Vault'}

    def getgui(self):
        if self.gui is None:
            self.gui = PMT_gui()
        return self.gui

    def initClient(self):
        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False
        self.starttime = 0
        # create polling loop
        self.refresher = LoopingCall(self.update_counts)

    def initData(self):
        # set default values
        self.gui.sample_time.setValue(100)
        self.gui.sample_num.setValue(100)
        self.gui.poll_interval.setValue(5)

    def initGUI(self):
        # read buttons
        self.gui.read_once_switch.clicked.connect(lambda: self.update_counts())
        self.gui.read_cont_switch.toggled.connect(lambda status: self.toggle_polling(status))
        # lock
        self.gui.lockswitch.toggled.connect(lambda status: self._lock(status))
        # todo: implement quick check
        # todo: make ttl counter # a variable


    # SLOTS
    @inlineCallbacks
    def update_counts(self):
        """
        Main function that actually gets counts from artiq.
        """
        # get values from GUI
        sample_time_us = int(self.gui.sample_time.value())
        num_samples = int(self.gui.sample_num.value())
        # get counts
        counts = yield self.aq.ttl_counter('ttl_counter{:d}'.format(0), sample_time_us, num_samples)
        # update display
        self.gui.count_display.setText("{:.3f}".format(counts))
        # store data if recording
        if self.recording:
            yield self.dv.add(time() - self.starttime, counts, context=self.c_record)

    def toggle_polling(self, status):
        # start if not running
        if status and (not self.refresher.running):
            poll_interval_s = self.gui.poll_interval.value()
            self.gui.poll_interval.setEnabled(False)
            self.gui.read_once_switch.setEnabled(False)
            self.gui.count_display.setStyleSheet('color: green')
            self.refresher.start(poll_interval_s, now=True)
        # stop if running
        elif (not status) and (self.refresher.running):
            self.refresher.stop()
            self.gui.read_once_switch.setEnabled(True)
            self.gui.poll_interval.setEnabled(True)
            self.gui.count_display.setStyleSheet('color: red')

    @inlineCallbacks
    def record(self, status):
        """
        Creates a new dataset to record counts
        tells polling loop to add data to data vault.
        """
        self.recording = status
        # set up datavault
        if self.recording:
            self.starttime = time()
            trunk = createTrunk(self.name)
            yield self.dv.cd(trunk, True, context=self.c_record)
            yield self.dv.new('PMT Counter', [('Elapsed time', 't')], [('PMT', 'Counts', 'Num.')], context=self.c_record)

    def _lock(self, status):
        self.gui.read_once_switch.setEnabled(status)
        self.gui.read_cont_switch.setEnabled(status)
        self.gui.sample_time.setEnabled(status)
        self.gui.sample_num.setEnabled(status)
        self.gui.poll_interval.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(PMT_client)
