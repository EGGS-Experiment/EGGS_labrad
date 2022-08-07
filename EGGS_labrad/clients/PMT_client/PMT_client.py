from time import time
import time
from numpy import mean, std
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.PMT_client.PMT_gui import PMT_gui
# todo: integrate recording


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
        self.refresher = LoopingCall(self.update_counts_continually)
        self._sample_time_us = 0
        self._num_samples = 0
        self._time_per_data = 0

    def initData(self):
        # set default values
        self.gui.sample_time.setValue(500)
        self.gui.sample_num.setValue(100)
        self.gui.poll_interval.setValue(5)

    def initGUI(self):
        # read buttons
        self.gui.read_once_switch.clicked.connect(lambda: self.update_counts_once())
        self.gui.read_cont_switch.toggled.connect(lambda status: self.toggle_polling(status))
        self.gui.flip.clicked.connect(lambda: self.flipper_pulse())
        # lock
        self.gui.lockswitch.clicked.connect(lambda status: self._lock(status))
        # todo: make ttl counter # a variable


    # SLOTS
    @inlineCallbacks
    def update_counts_once(self):
        """
        Main function that actually gets counts from artiq.
        Gets values once per button press.
        """
        # get values from GUI
        sample_time_us = int(self.gui.sample_time.value())
        num_samples = int(self.gui.sample_num.value())
        time_per_data = sample_time_us * num_samples * 1e-6

        # ensure valid timing
        if (time_per_data > self.gui.poll_interval.value()) or (time_per_data > 1):
            raise Exception("Error: invalid timing.")

        # get counts
        try:
            self._lock(False)
            count_list = yield self.aq.ttl_count_list('ttl_counter{:d}'.format(0), sample_time_us, num_samples)
        except Exception as e:
            print("Error while getting values:")
            print(e)
        finally:
            self._lock(True)

        # update display
        # todo: clean up display
        if self.gui.sample_std_off.isChecked():
            self.gui.count_display.setText("{:.3f}".format(mean(count_list)))
        else:
            self.gui.count_display.setText("{:.3f} \u00B1 {:.3f}".format(mean(count_list), std(count_list)))

    @inlineCallbacks
    def update_counts_continually(self):
        """
        Main function that actually gets counts from artiq.
        Gets values continually.
        """
        # get counts
        count_list = yield self.aq.ttl_count_list('ttl_counter{:d}'.format(0), self.sample_time_us, self.num_samples)

        # update display
        # todo: clean up display
        if self.gui.sample_std_off.isChecked():
            self.gui.count_display.setText("{:.3f}".format(mean(count_list)))
        else:
            self.gui.count_display.setText("{:.3f} \u00B1 {:.3f}".format(mean(count_list), std(count_list)))
        # store data if recording
        if self.recording:
            yield self.dv.add(time() - self.starttime, mean(count_list), context=self.c_record)

    def toggle_polling(self, status):
        # start if not running
        if status and (not self.refresher.running):
            # get timing values
            poll_interval_s = self.gui.poll_interval.value()
            self.sample_time_us = int(self.gui.sample_time.value())
            self.num_samples = int(self.gui.sample_num.value())
            time_per_data = self.sample_time_us * self.num_samples * 1e-6
            # ensure valid timing
            if (time_per_data > poll_interval_s) or (time_per_data > 1):
                raise Exception("Error: invalid timing.")
            # set up display and start polling
            self.gui.count_display.setStyleSheet('color: green')
            self.refresher.start(poll_interval_s, now=True)
        # stop if running
        elif (not status) and (self.refresher.running):
            self.refresher.stop()
            self.gui.count_display.setStyleSheet('color: red')

        # set gui element status
        self.gui.sample_time.setEnabled(not status)
        self.gui.sample_num.setEnabled(not status)
        self.gui.poll_interval.setEnabled(not status)
        self.gui.read_once_switch.setEnabled(not status)
        self.gui.flip.setEnabled(not status)

    @inlineCallbacks
    def flipper_pulse(self):
        # send TTL to flipper mount
        yield self.aq.ttl_set("ttl23", 1)
        time.sleep(.2)
        yield self.aq.ttl_set("ttl23", 0)

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
            # todo: get channel correctly
            yield self.dv.new('PMT', [('Elapsed time', 't')], [('PMT Reading', 'Counts', 'Number')], context=self.c_record)

    def _lock(self, status):
        self.gui.read_once_switch.setEnabled(status)
        self.gui.read_cont_switch.setEnabled(status)
        self.gui.sample_time.setEnabled(status)
        self.gui.sample_num.setEnabled(status)
        self.gui.poll_interval.setEnabled(status)
        self.gui.flip.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(PMT_client)
