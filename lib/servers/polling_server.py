from twisted.internet.task import LoopingCall
from labrad.server import LabradServer, setting

class PollingServer(LabradServer):
    """
    Holds all the functionality needed to
    run polling loops on the server.
    Also contains functionality for Signals.
    """

    # STARTUP
    def initServer(self):
        # call parent initserver to support further subclassing
        super().initServer()
        # signal stuff
        self.listeners = set()
        # polling stuff
        self.refresher = LoopingCall(self._poll)
        self.startRefresher(5)

    def stopServer(self):
        if hasattr(self, 'refresher'):
            if self.refresher.running:
                self.refresher.stop()
        super().stopServer()

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
    @setting(911, 'Set Polling', status='b', interval='v', returns='(bv)')
    def set_polling(self, c, status, interval):
        """
        Configure polling of device for values.
        """
        # ensure interval is valid
        if (interval < 1) or (interval > 60):
            raise Exception('Invalid polling interval.')
        # only start/stop polling if we are not already started/stopped
        if status and (not self.refresher.running):
            self.startRefresher(interval)
        elif status and self.refresher.running:
            self.refresher.interval = interval
        elif (not status) and (self.refresher.running):
            self.refresher.stop()
        return (self.refresher.running, self.refresher.interval)

    @setting(912, 'Get Polling', returns='(bv)')
    def get_polling(self, c):
        """
        Get polling parameters.
        """
        # in case refresher is off
        interval_tmp = 0
        if self.refresher.interval is None:
            interval_tmp = 0
        else:
            interval_tmp = self.refresher.interval
        return (self.refresher.running, interval_tmp)

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
        # print(failure)
        print('Polling failed. Restarting polling.')
        self.ser.flush_input_buffers()
        self.ser.flush_output_buffers
        self.startRefresher(5)
