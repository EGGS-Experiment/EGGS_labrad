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



class ARTIQServer(LabradServer):
    """
    A server that uses devices from the ARTIQ box.
    """

    artiq_devices = {}

    # STARTUP
    def initServer(self):
        # call parent initserver to support further subclassing
        super().initServer()
        # check for artiq server
        try:
            self.artiq = cxn.artiq_server
            # get required devices
            for devices in self.artiq_devices.items():
                setattr(self, devices[0], devices[1])
        except Exception as e:
            print(e)
            raise


    # STATUS
    # todo: get artiq box details (ip address, name, device_db)


    # DMA
    @setting(222222, 'DMA', status='b', returns='b')
    def DMA(self, c, status=None):
        """
        Program the core DMA
        Arguments:
            status  (bool)  : whether to stop or start correction mode.
        Returns:
            status  (bool)  : whether to stop or start correction mode.
        """
        pass
    #todo: write setting to program DMA


    # EXPERIMENTS
    def runExperiment(self, file, args):
        """
        Run an experiment file.
        Arguments:
            file    (str)   : the location of the experiment file
            args    (str)   : the arguments to run the experiment with
        Returns:
                    ((str))  : the run parameters of the experiment.
        """
        pass
        #todo

    def schedule(self):
        """

        """
        pass
    #todo: check scheduling


    # DATA
    # todo: get dataset values
    # todo: create datasets