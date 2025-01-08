from numpy import mean, std
from time import time, sleep
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from PyQt5.QtGui import QFont

from EGGS_labrad.clients import GUIClient, createTrunk
from EGGS_labrad.clients.PMT_client.PMT_gui import PMT_gui

EXPID = 564324
# todo: clean up display; make more programmatic
# todo: make ttl counter # a variable
# todo: subscribe to signals so we know when aperture is open or closed


class PMT_client(GUIClient):

    name = 'PMT Client'
    servers = {
        'aq': 'ARTIQ Server',
        'dv': 'Data Vault',
        'ell': 'Elliptec Server',
        'labjack': 'LabJack Server'
    }

    def getgui(self):
        if self.gui is None:
            self.gui = PMT_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # set recording stuff
        self.c_record =     self.cxn.context()
        self.recording =    False
        self.starttime =    0

        # create polling loop
        self.refresher =        LoopingCall(self.update_counts_continually)
        self._sample_time_us =  0
        self._num_samples =     0
        self._time_per_data =   0

        # connect to signals
        yield self.aq.signal__exp_running(EXPID)
        yield self.aq.addListener(listener=self.experimentRunning, source=None, ID=EXPID)

        # connect to labjack
        self.flipper_port_name = "DIO3"
        device_handle = yield self.labjack.device_info()

        if device_handle == -1:
            # get device list
            dev_list = yield self.labjack.device_list()
            # assume desired labjack is first in list
            yield self.labjack.device_select(dev_list[0])

    def initData(self):
        # set default values
        self.gui.sample_time.setValue(3000)
        self.gui.sample_num.setValue(50)
        self.gui.poll_interval.setValue(0.5)

    def initGUI(self):
        # general
        self.gui.record_button.clicked.connect(lambda status: self.record(status))
        self.gui.lockswitch.clicked.connect(lambda status: self._lock(status))
        # read buttons
        self.gui.read_once_switch.clicked.connect(lambda: self.update_counts_once())
        self.gui.read_cont_switch.toggled.connect(lambda status: self.toggle_polling(status))
        # imaging utilities
        self.gui.flip.clicked.connect(lambda: self.flipper_pulse())
        self.gui.aperture_button.toggled.connect(lambda status: self.aperture_toggle(status))


    """
    SLOTS
    """
    @inlineCallbacks
    def update_counts_once(self):
        """
        Main function that actually gets counts from artiq.
        Gets values once per button press.
        """
        # get values from GUI
        sample_time_us =    int(self.gui.sample_time.value())
        num_samples =       int(self.gui.sample_num.value())
        time_per_data =     (sample_time_us * 1e-6) * num_samples

        # ensure valid timing
        if (time_per_data > self.gui.poll_interval.value()) or (time_per_data > 10):
            raise Exception("Error: invalid timing.")

        # get counts
        try:
            self._lock(False)
            counts_avg, counts_std = yield self.aq.ttl_counts('ttl{:d}_counter'.format(0), sample_time_us, num_samples)
        except Exception as e:
            print("Error while getting values:")
            print(repr(e))
        finally:
            self._lock(True)

        # update display
        if self.gui.sample_std_off.isChecked():
            self.gui.count_display.setText("{:.2f}".format(counts_avg))
        else:
            self.gui.count_display.setText("{:.2f} \u00B1 {:.2f}".format(counts_avg, counts_std))

    @inlineCallbacks
    def update_counts_continually(self):
        """
        Main function that actually gets counts from artiq.
        Gets values continually.
        """
        # get counts
        counts_avg, counts_std = yield self.aq.ttl_counts('ttl{:d}_counter'.format(0), self.sample_time_us, self.num_samples)

        # update display
        if self.gui.sample_std_off.isChecked():
            self.gui.count_display.setFont(QFont('MS Shell Dlg 2', pointSize=23))
            self.gui.count_display.setText("{:.2f}".format(counts_avg))
        else:
            self.gui.count_display.setFont(QFont('MS Shell Dlg 2', pointSize=19))
            self.gui.count_display.setText("{:.2f} \u00B1 {:.2f}".format(counts_avg, counts_std))
        # store data if recording
        if self.recording:
            yield self.dv.add(time() - self.starttime, counts_avg, context=self.c_record)

    def toggle_polling(self, status):
        # start if not running
        if status and (not self.refresher.running):
            # get timing values
            poll_interval_s =       self.gui.poll_interval.value()
            self.sample_time_us =   int(self.gui.sample_time.value())
            self.num_samples =      int(self.gui.sample_num.value())
            time_per_data =         (self.sample_time_us * 1e-6) * self.num_samples

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
        yield self.labjack.write_name(self.flipper_port_name, 1)
        sleep(.1)
        yield self.labjack.write_name(self.flipper_port_name, 0)
        # yield self.aq.ttl_set("ttl15", 1)
        # sleep(.1)
        # yield self.aq.ttl_set("ttl15", 0)

    @inlineCallbacks
    def aperture_toggle(self, status):
        # open/close the aperture
        if status:
            yield self.ell.move_home()
        else:
            yield self.ell.move_absolute(2888)

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
            yield self.dv.new('PMT',
                              [('Elapsed time', 't')],
                              [('PMT Counts', 'Counts', 'Number')],
                              context=self.c_record)

    def experimentRunning(self, c, msg):
        # stop polling
        if self.refresher.running:
            self.gui.read_cont_switch.click()

        # set artiq monitor status
        self.gui.artiq_monitor.setStatus(msg)

        # workaround: enable aperture in case we need to quickly open it
        exp_running_status, rid = msg
        self.gui.setEnabled(True)
        self._lock(not exp_running_status)
        self.gui.lockswitch.setEnabled(not exp_running_status)
        self.gui.aperture_button.setEnabled(True)

    def _lock(self, status):
        # note: don't lock aperture since we may need to open it partway through
        self.gui.read_once_switch.setEnabled(status)
        self.gui.read_cont_switch.setEnabled(status)
        self.gui.sample_time.setEnabled(status)
        self.gui.sample_num.setEnabled(status)
        self.gui.poll_interval.setEnabled(status)
        self.gui.flip.setEnabled(status)
        self.gui.record_button.setEnabled(status)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(PMT_client)
