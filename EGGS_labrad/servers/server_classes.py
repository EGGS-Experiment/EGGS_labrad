from twisted.internet.task import LoopingCall
from labrad.server import LabradServer, setting


__all__ = ["PollingServer", "ARTIQServer"]


"""
Polling Server
"""
class PollingServer(LabradServer):
    """
    Holds all the functionality needed to run polling loops on the server.
    Also contains functionality for Signals.
    """

    # tells server whether to start polling upon startup
    POLL_ON_STARTUP = False
    POLL_INTERVAL_ON_STARTUP = 5

    # STARTUP
    def initServer(self):
        # call parent initserver to support further subclassing
        super().initServer()
        # signal stuff
        self.listeners = set()
        # create refresher for polling
        self.refresher = LoopingCall(self._poll)
        # set startup polling
        self.refresher.start(self.POLL_INTERVAL_ON_STARTUP, now=False)
        if not self.POLL_ON_STARTUP:
            self.refresher.stop()

    def stopServer(self):
        super().stopServer()
        if hasattr(self, 'refresher'):
            if self.refresher.running:
                self.refresher.stop()


    # CONTEXT
    def initContext(self, c):
        """
        Initialize a new context object.
        """
        self.listeners.add(c.ID)

    def expireContext(self, c):
        """
        Remove a context object and stop polling if there are no more listeners.
        """
        self.listeners.remove(c.ID)
        if len(self.listeners) == 0:
            self.refresher.stop()
            print('Stopped polling due to lack of listeners.')

    def getOtherListeners(self, c):
        """
        Get all listeners except for the context owner.
        """
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    def notifyOtherListeners(self, context, message, f):
        """
        Notifies all listeners except the one in the given context, executing function f
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        f(message, notified)


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
        #todo: maybe don't have it auto restart polling


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
    def get_devices(self):
        """
        Returns the device_db dictionary.
        """
        return self.devicedb_client.get_device_db()


    # EXPERIMENTS
    def runExperiment(self, filepath, kwargs):
        """
        Run an experiment file.
        Arguments:
            filepath    (str)   : the location of the experiment file
            args        (str)   : the arguments to run the experiment with
        Returns:
                        (*str)  : the runID parameters of the experiment
        """
        ps_pipeline = 'PS'
        ps_priority = 1
        ps_expid = {'log_level': 30,
                    'file': filepath,
                    'class_name': None,
                    'arguments': kwargs}
        self.ps_rid = self.scheduler_client.submit(pipeline_name=ps_pipeline, expid=ps_expid, priority=ps_priority)
        return self.ps_rid


    # DMA
    def DMArun(self, handle_name):
        """
        Run an experiment from core DMA.
        Arguments:
            handle_name (str)   : the handle of the DMA experiment.
        """
        yield self.artiq.runDMA(handle_name)

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


"""
Arduino Server
TODO: actually write this lol
"""

from EGGS_labrad.servers import SerialDeviceServer


class ArduinoServer(SerialDeviceServer):
    """
    A server that breaks out an Arduino.
    """

    # todo
    arduino_pins = {}

