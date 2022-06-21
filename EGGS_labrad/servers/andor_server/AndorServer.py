"""
### BEGIN NODE INFO
[info]
name =  Andor Server
version = 1.1.0
description = Server for the Andor iXon3.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from twisted.internet.defer import returnValue, DeferredLock, Deferred, inlineCallbacks

from numpy import reshape, ravel
from labrad.server import setting, Signal

from EGGS_labrad.servers import PollingServer
from EGGS_labrad.servers.andor_server.AndorAPI import AndorAPI

IMAGE_UPDATED_SIGNAL = 142312
# todo: stop using reactor.callLater
# todo: GUI signals
# todo: finish moving all to run
# todo: add binning


class AndorServer(PollingServer):
    """
    Contains methods that interact with the Andor CCD Cameras.
    """

    name = "Andor Server"
    image_updated = Signal(IMAGE_UPDATED_SIGNAL, 'signal: image updated', '*i')

    def initServer(self):
        super().initServer()
        self.listeners = set()
        self.lock = DeferredLock()
        self.camera = AndorAPI()
        self.last_image = None

    @inlineCallbacks
    def stopServer(self):
        super().stopServer()
        try:
            # todo: gui signal
            print('acquiring: {}'.format(self.stopServer.__name__))
            yield self.lock.acquire()
            print('acquired : {}'.format(self.stopServer.__name__))
            self.camera.shut_down()
            print('releasing: {}'.format(self.stopServer.__name__))
            self.lock.release()
        except Exception as e:
            print(e)
            pass

    def initContext(self, c):
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified


    """
    General
    """
    @setting(11, "Info Serial Number", returns='i')
    def serialNumber(self, c):
        """
        Gets the camera's serial number.
        Returns:
            (int)   : the camera's serial number.
        """
        return self.camera.get_camera_serial_number()

    @setting(31, "Info Detector Dimensions", returns='ww')
    def detectorDimensions(self, c):
        """
        Gets the dimensions of the camera's detector.
        Returns:
            (ww)   : the dimensions of the camera's detector.
        """
        print('acquiring: {}'.format(self.detectorDimensions.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.detectorDimensions.__name__))
            dimensions = yield deferToThread(self.camera.get_detector_dimensions)
        finally:
            print('releasing: {}'.format(self.detectorDimensions.__name__))
            self.lock.release()
        returnValue(dimensions)

    def wait(self, seconds, result=None):
        """
        Returns a deferred that will be fired later.
        """
        d = Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d


    """
    Temperature Related Settings
    """
    @setting(111, "Temperature", temp='v', returns='v')
    def temperature(self, c, temp=None):
        """
        Get/set the current/target device temperature.
        # todo: list accepted values
        Arguments:
            temp    (float) : the target temperature (in Celsius).
        Returns:
                    (float) : the current temperature (in Celsius).
        """
        temp = yield self._run('temperature', 'get_temperature', 'set_temperature', temp)
        returnValue(temp)

    @setting(121, "Cooler", state=['b', 'i'], returns='b')
    def cooler(self, c, state=None):
        """
        Get/set the current cooler state.
        Arguments:
            state   (bool)  : the cooler state.
        Returns:
                    (bool)  : the cooler state.
        """
        state = yield self._run('cooler', 'get_cooler_state', 'set_cooler_state', state)
        returnValue(state)


    """
    EMCCD Gain Settings
    """
    @setting(211, "EMCCD Gain", gain='i', returns='i')
    def EMCCDGain(self, c, gain=None):
        """
        Get/set the current EMCCD gain.
        Arguments:
            gain    (int)   : the EMCCD gain.
        Returns:
                    (int)   : the EMCCD gain.
        """
        gain = yield self._run('EMCCD Gain', 'get_emccd_gain', 'set_emccd_gain', gain)
        returnValue(gain)

    @setting(221, "EMCCD Range", returns='(ii)')
    def EMCCDRange(self, c):
        """
        Get the EMCCD gain range.
        Returns:
            (int, int)  : the minimum and maximum EMCCD gain values.
        """
        return self.camera.get_camera_em_gain_range()


    """
    Acquisition Settings
    """
    @setting(311, "Mode Read", mode='s', returns='s')
    def modeRead(self, c, mode=None):
        """
        Get/set the current read mode.
            Can be one of ('Full Vertical Binning', 'Multi-Track', 'Random-Track', 'Single-Track', Image').
        Arguments:
            mode    (str)   : the current read mode.
        Returns:
                    (str)   : the current read mode.
        """
        mode = yield self._run('Mode Read', 'get_read_mode', 'set_read_mode', mode)
        returnValue(mode)

    @setting(321, "Mode Shutter", mode='s', returns='s')
    def modeShutter(self, c, mode=None):
        """
        Get/set the current shutter mode.
            Can be one of ('Open', 'Auto', 'Close').
        Arguments:
            mode    (str)   : the shutter mode.
        Returns:
                    (str)   : the shutter mode.
        """
        mode = yield self._run('Mode Shutter', 'get_shutter_mode', 'set_shutter_mode', mode)
        returnValue(mode)

    @setting(331, "Mode Acquisition", mode='s', returns='s')
    def modeAcquisition(self, c, mode=None):
        """
        Get/set the current acquisition mode.
            Can be one of ('Single Scan', 'Accumulate', 'Kinetics', 'Fast Kinetics', 'Run till abort').
        Arguments:
            mode    (str)   : the acquisition mode.
        Returns:
                    (str)   : the acquisition mode.
        """
        mode = yield self._run('Mode Acquisition', 'get_acquisition_mode', 'set_acquisition_mode', mode)
        returnValue(mode)

    @setting(341, "Mode Trigger", mode='s', returns='s')
    def modeTrigger(self, c, mode=None):
        """
        Get/set the current trigger mode.
            Can be one of ('Internal', 'External', 'External Start', 'External Exposure', 'External FVB EM', 'Software Trigger', 'External Charge Shifting').
        Arguments:
            mode    (str)   : the trigger mode.
        Returns:
                    (str)   : the trigger mode.
        """
        mode = yield self._run('Mode Trigger', 'get_trigger_mode', 'set_trigger_mode', mode)
        returnValue(mode)

    @setting(351, "Exposure Time", time='v', returns='v')
    def exposureTime(self, c, time=None):
        """
        Get/set the current exposure time.
        Arguments:
            time    (float)   : the trigger mode.
        Returns:
                    (float) : the current exposure time in seconds.
        """
        mode = yield self._run('Exposure Time', 'get_exposure_time', 'set_exposure_time', time)
        returnValue(mode)


    """
    Image Region
    """
    @setting(411, "Get Image Region", returns='*i')
    def getImageRegion(self, c):
        """
        Gets current image region.
        Returns:
            # todo
        """
        return self.camera.get_image()

    @setting(412, "Set Image Region", horizontalBinning='i', verticalBinning='i', horizontalStart='i', horizontalEnd='i',
             verticalStart='i', verticalEnd='i', returns='')
    def setImageRegion(self, c, horizontalBinning, verticalBinning, horizontalStart, horizontalEnd, verticalStart,
                       verticalEnd):
        """
        Sets current image region.
        Arguments:
            # todo
        """
        print('acquiring: {}'.format(self.setImageRegion.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setImageRegion.__name__))
            yield deferToThread(self.camera.set_image, horizontalBinning, verticalBinning, horizontalStart,
                                horizontalEnd, verticalStart, verticalEnd)
        finally:
            print('releasing: {}'.format(self.setImageRegion.__name__))
            self.lock.release()


    """
    Kinetic Series
    """
    @setting(511, "Kinetic Number", num='i', returns='i')
    def kineticNumber(self, c, num=None):
        """
        Get/set number of scans in a kinetic cycle.
        Arguments:
            num (int)   : the number of scans.
        Returns:
                (int)   : the number of scans.
        """
        num = yield self._run('Kinetic Number', 'get_number_kinetics', 'set_number_kinetics', num)
        returnValue(num)

    @setting(512, "Kinetic Wait", timeout='v', returns='b')
    def kineticWait(self, c, timeout=1):
        """
        Waits until the given number of kinetic images are completed.
        Arguments:
            the (float) : the # todo
        Returns:
                (bool)  : fd # todo
        """
        # UPDATED THE TIMEOUT. FIX IT LATER
        # todo: fix
        requestCalls = int(timeout['s'] / 0.050)  # number of request calls
        for i in range(requestCalls):
            print('acquiring: {}'.format(self.kineticWait.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.kineticWait.__name__))
                status = yield deferToThread(self.camera.get_status)
                # useful for debugging of how many iterations have been completed in case of missed trigger pulses
                a, b = yield deferToThread(self.camera.get_series_progress)
                print(a, b)
                print(status)
            finally:
                print('releasing: {}'.format(self.kineticWait.__name__))
                self.lock.release()
            if status == 'DRV_IDLE':
                returnValue(True)
            yield self.wait(0.050)
        returnValue(False)


    """
    Acquisition
    """
    @setting(611, "Acquisition Start", returns='')
    def acquisitionStart(self, c):
        """
        Start acquisition.
        """
        print('acquiring: {}'.format(self.acquisitionStart.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.acquisitionStart.__name__))
            # speeds up the call to start_acquisition
            yield deferToThread(self.camera.prepare_acqusition)
            yield deferToThread(self.camera.start_acquisition)
            # necessary so that start_acquisition call completes even for long kinetic series
            yield self.wait(0.1)
        finally:
            print('releasing: {}'.format(self.acquisitionStart.__name__))
            self.lock.release()

    @setting(612, "Acquisition Stop", returns='')
    def acquisitionStop(self, c):
        print('acquiring: {}'.format(self.acquisitionStop.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.acquisitionStop.__name__))
            yield deferToThread(self.camera.abort_acquisition)
        finally:
            print('releasing: {}'.format(self.acquisitionStop.__name__))
            self.lock.release()

    @setting(621, "Acquisition Wait", returns='')
    def acquisitionWait(self, c):
        """
        Wait for acquisition.
        """
        print('acquiring: {}'.format(self.acquisitionWait.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.acquisitionWait.__name__))
            yield deferToThread(self.camera.wait_for_acquisition)
        finally:
            print('releasing: {}'.format(self.acquisitionWait.__name__))
            self.lock.release()

    @setting(631, "Acquire Data", num_images='i', returns='*i')
    def acquireData(self, c, num_images=1):
        """
        Get the acquired images.
        Arguments:
            # todo
        Returns:
            # todo
        """
        print('acquiring: {}'.format(self.acquireData.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.acquireData.__name__))
            image = yield deferToThread(self.camera.get_acquired_data, num_images)
        finally:
            print('releasing: {}'.format(self.acquireData.__name__))
            self.lock.release()
        returnValue(image)

    @setting(632, "Acquire Data Summed", num_images='i', returns='*i')
    def acquireDataSummed(self, c, num_images=1):
        """
        Get the counts with the vertical axis summed over.
        Arguments:
            # todo
        Returns:
            # todo
        """
        print('acquiring: {}'.format(self.acquireDataSummed.__name__))
        yield self.lock.acquire()
        try:
            print('acquired: {}'.format(self.acquireDataSummed.__name__))
            images = yield deferToThread(self.camera.get_acquired_data, num_images)
            hbin, vbin, hstart, hend, vstart, vend = self.camera.get_image()
            x_pixels = int((hend - hstart + 1.) / (hbin))
            y_pixels = int(vend - vstart + 1.) / (vbin)
            images = reshape(images, (num_images, y_pixels, x_pixels)).sum(axis=1)
            images = ravel(images, order='C')
        finally:
            print('releasing: {}'.format(self.acquireDataSummed.__name__))
            self.lock.release()
        returnValue(images.tolist())

    @setting(641, "Acquire Image Recent", returns='*i')
    def getMostRecentImage(self, c):
        """
        Get all data.
        """
        # print('acquiring: {}'.format(self.getMostRecentImage.__name__))
        yield self.lock.acquire()
        try:
            # print('acquired : {}'.format(self.getMostRecentImage.__name__))
            image = yield deferToThread(self.camera.get_most_recent_image)
        finally:
            # print('releasing: {}'.format(self.getMostRecentImage.__name__))
            self.lock.release()
        returnValue(image)


    """
    POLLING
    """
    @inlineCallbacks
    def _poll(self):
        """
        Polls the camera for image readout.
        """
        data = yield self.getMostRecentImage(None)
        # if there is a new image since the last update, send a signal to the clients
        if data != self.last_image:
            self.last_image = data
            yield self.image_updated(data)


    # HELPER
    @inlineCallbacks
    def _run(self, function_name, getter, setter=None, setter_val=None):
        """
        Runs a getter/setter combo.
        """
        # setter
        if setter_val is not None:
            # print('acquiring: {}'.format(function_name))
            yield self.lock.acquire()
            try:
                # print('acquired : {}'.format(function_name))
                setter_func = getattr(self.camera, setter)
                yield deferToThread(setter_func, setter_val)
            finally:
                # print('releasing: {}'.format(function_name))
                self.lock.release()
        # getter
        resp = None
        # print('acquiring: {}'.format(function_name))
        yield self.lock.acquire()
        try:
            # print('acquired : {}'.format(function_name))
            getter_func = getattr(self.camera, getter)
            resp = yield deferToThread(getter_func)
        finally:
            # print('releasing: {}'.format(function_name))
            self.lock.release()
        if resp is not None:
            returnValue(resp)


if __name__ == "__main__":
    from labrad import util
    util.runServer(AndorServer())
