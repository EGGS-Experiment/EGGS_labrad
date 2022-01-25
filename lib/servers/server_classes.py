from twisted.internet.task import LoopingCall
from labrad.server import LabradServer, setting


__all__ = ["PollingServer", "ARTIQServer"]


class PollingServer(LabradServer):
    """
    Holds all the functionality needed to
    run polling loops on the server.
    Also contains functionality for Signals.
    """

    POLL_ON_STARTUP = False

    # STARTUP
    def initServer(self):
        # call parent initserver to support further subclassing
        super().initServer()
        # signal stuff
        self.listeners = set()
        # create refresher for polling
        self.refresher = LoopingCall(self._poll)
        # set startup polling
        self.refresher.start(5, now=False)
        if not self.POLL_ON_STARTUP:
            self.refresher.stop()

    def stopServer(self):
        super().stopServer()
        if hasattr(self, 'refresher'):
            if self.refresher.running:
                self.refresher.stop()


    # CONTEXT
    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        """Remove a context object."""
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        """Get all listeners except for the context owner."""
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified


    # POLLING
    @setting(911, 'Polling', status='b', interval='v', returns='(bv)')
    def Polling(self, c, status=None, interval=None):
        """
        Configure polling of device for values.
        """
        # empty call returns getter
        if (status is None) and (interval is None):
            return (self.refresher.running, self.refresher.interval)

        # ensure interval is valid
        if interval is None:
            interval = 5.0
        elif (interval < 1) or (interval > 60):
            raise Exception('Invalid polling interval.')

        # start polling if we are stopped
        if status and (not self.refresher.running):
            self.startRefresher(interval)
        # change polling interval if already running
        elif status and self.refresher.running:
            self.refresher.interval = interval
        # stop polling if we are running
        elif (not status) and self.refresher.running:
            self.refresher.stop()
        return (self.refresher.running, self.refresher.interval)

    def startRefresher(self, interval=None):
        """
        Starts the polling loop and calls errbacks.
        """
        d = self.refresher.start(interval, now=False)
        d.addErrback(self._poll_fail)

    def _poll(self):
        """
        Polls the device for pressure readout.
        To be subclassed.
        """
        pass

    def _poll_fail(self, failure):
        print('Polling failed. Restarting polling.')
        yield self.ser.flush_input()
        yield self.ser.flush_output()
        self.startRefresher(5)




"""
ARTIQ Server
"""

from sipyco.pc_rpc import Client


class ARTIQServer(LabradServer):
    """
    A server that uses devices from the ARTIQ box.
    """

    # artiq_devices holds the desired variable name as keys and the artiq hardware name as values
    artiq_devices = {}


    # STARTUP
    def initServer(self):
        # call parent initserver to support further subclassing
        super().initServer()
        # check for artiq server
        try:
            self.artiq = self.client.artiq_server
            # get required devices
            for devices in self.artiq_devices.items():
                setattr(self, devices[0], devices[1])
            self.devicedb_client = Client('::1', 3251, 'master_device_db')
            self.datasetdb_client = Client('::1', 3251, 'master_dataset_db')
            self.scheduler_client = Client('::1', 3251, 'master_schedule')
        except Exception as e:
            print(e)
            raise


    # STATUS
    def devices(self, filepath):
        """
        Returns the device_db dictionary.
        """
        return self.devicedb_client.get_device_db()


    # EXPERIMENTS
    def runExperiment(self, file, *args, **kwargs):
        """
        Run an experiment file.
        Arguments:
            file    (str)   : the location of the experiment file
            args    (str)   : the arguments to run the experiment with
        Returns:
                    (*str)  : the runID parameters of the experiment
        """
        #todo: schedule dma programming experiment
        pass


    # DMA
    def DMArun(self, handle_name):
        """
        Run an experiment from core DMA.
        Arguments:
            handle_name (str)   : the handle of the DMA experiment.
        """
        yield self.artiq.

    # DATASETS
    def getDataset(self, dataset_name):
        """
        Get a dataset.
        Arguments:
            dataset_name    (str)   : the name of the dataset
        Returns:
                            (?)     : the dataset
        """
        return self.datasetdb_client.get(dataset_name)



    @setting(111, "Run Experiment", path='s', maxruns='i', returns='')
    def runExperiment(self, c, path, maxruns = 1):
        """
        Run the experiment a given number of times.
        Argument:
            path    (string): the filepath to the ARTIQ experiment.
            maxruns (int)   : the number of times to run the experiment
        """


    @setting(112, "Stop Experiment", returns='')
    def stopSequence(self, c):
        """
        Stops any currently running sequence.
        """
        # check that an experiment is currently running
        if self.ps_rid not in self.scheduler.get_status().keys():
            raise Exception('Error: no experiment currently running')
        yield self.inCommunication.acquire()
        yield deferToThread(self.scheduler.delete, self.ps_rid)
        self.ps_rid = None
        #todo: make resetting of ps_rid contingent on defertothread completion
        self.inCommunication.release()