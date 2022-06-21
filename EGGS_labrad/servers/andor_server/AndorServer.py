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
from twisted.internet.task import LoopingCall
from twisted.internet.threads import deferToThread
from twisted.internet.defer import returnValue, DeferredLock, Deferred, inlineCallbacks

from numpy import reshape, ravel
from labrad.server import LabradServer, setting, Signal

from EGGS_labrad.servers.andor_server.AndorAPI import AndorAPI

IMAGE_UPDATED_SIGNAL = 142312
# todo: clean up imports
# todo: GUI signals
# todo: make logger instead; remove all prints


class AndorServer(LabradServer):
    """
    Contains methods that interact with the Andor CCD Cameras.
    """

    name = "Andor Server"
    image_updated = Signal(IMAGE_UPDATED_SIGNAL, 'signal: image updated', '*i')

    def initServer(self):
        self.listeners = set()
        self.lock = DeferredLock()
        self.camera = AndorAPI()

    @inlineCallbacks
    def stopServer(self):
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
        # setter
        if temp is not None:
            print('acquiring: {}'.format(self.temperature.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.temperature.__name__))
                yield deferToThread(self.camera.set_temperature, temp)
            finally:
                print('releasing: {}'.format(self.temperature.__name__))
                self.lock.release()
        # getter
        temperature = None
        print('acquiring: {}'.format(self.temperature.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.temperature.__name__))
            temperature = yield deferToThread(self.camera.get_temperature)
        finally:
            print('releasing: {}'.format(self.temperature.__name__))
            self.lock.release()
        if temperature is not None:
            returnValue(temperature)

    @setting(121, "Cooler", state=['b', 'i'], returns='b')
    def cooler(self, c, state=None):
        """
        Get/set the current cooler state.
        Arguments:
            state   (bool)  : the cooler state.
        Returns:
                    (bool)  : the cooler state.
        """
        # setter
        if state is not None:
            if (type(state) is int) and (state not in (0, 1)):
                raise Exception("Error: invalid input.")
            print('acquiring: {}'.format(self.cooler.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.cooler.__name__))
                yield deferToThread(self.camera.set_cooler_on)
            finally:
                print('releasing: {}'.format(self.cooler.__name__))
                self.lock.release()
        # getter
        print('acquiring: {}'.format(self.cooler.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.cooler.__name__))
            yield deferToThread(self.camera.set_cooler_off)
        finally:
            print('releasing: {}'.format(self.cooler.__name__))
            self.lock.release()


    """
    EMCCD Gain Settings
    """
    @setting(211, "EMCCD Gain", gain='i', returns='i')
    def EMCCDGain(self, c, gain=None):
        """
        Get/set the current EMCCD gain.
        # todo: list accepted values
        Arguments:
            gain    (int)   : the EMCCD gain.
        Returns:
                    (int)   : the EMCCD gain.
        """
        # setter
        if gain is not None:
            print('acquiring: {}'.format(self.EMCCDGain.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.EMCCDGain.__name__))
                yield deferToThread(self.camera.set_emccd_gain, gain)
            finally:
                print('releasing: {}'.format(self.EMCCDGain.__name__))
                self.lock.release()
        # getter
        gain = None
        print('acquiring: {}'.format(self.EMCCDGain.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.EMCCDGain.__name__))
            gain = yield deferToThread(self.camera.get_emccd_gain)
        finally:
            print('releasing: {}'.format(self.EMCCDGain.__name__))
            self.lock.release()
        if gain is not None:
            returnValue(gain)

    @setting(221, "EMCCD Gain Range", returns='(ii)')
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
    @setting(311, "Read Mode", mode='s', returns='s')
    def readMode(self, c, mode=None):
        """
        Get/set the current read mode.
        # todo: list accepted values
        Arguments:
            mode    (str)   : the current read mode.
        Returns:
                    (str)   : the current read mode.
        """
        # setter
        if mode is not None:
            print('acquiring: {}'.format(self.readMode.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.readMode.__name__))
                yield deferToThread(self.camera.set_read_mode, mode)
            finally:
                print('releasing: {}'.format(self.readMode.__name__))
                self.lock.release()
        # getter
        return self.camera.get_read_mode()

    @setting(321, "Shutter Mode", mode='s', returns='s')
    def shutterMode(self, c, mode):
        """
        Get/set the current shutter mode.
        # todo: list accepted values
        Arguments:
            mode    (str)   : the shutter mode.
        Returns:
                    (str)   : the shutter mode.
        """
        # setter
        if mode is not None:
            mode = None
            print('acquiring: {}'.format(self.shutterMode.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.shutterMode.__name__))
                yield deferToThread(self.camera.set_shutter_mode, mode)
            finally:
                print('releasing: {}'.format(self.shutterMode.__name__))
                self.lock.release()
            if mode is not None:
                returnValue(mode)
        # getter
        return self.camera.get_shutter_mode()

    @setting(331, "Acquisition Mode", mode='s', returns='s')
    def acquisitionMode(self, c, mode=None):
        """
        Get/set the current acquisition mode.
        # todo: list accepted values
        Arguments:
            mode    (str)   : the acquisition mode.
        Returns:
                    (str)   : the acquisition mode.
        """
        # setter
        if mode is not None:
            print('acquiring: {}'.format(self.acquisitionMode.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.acquisitionMode.__name__))
                yield deferToThread(self.camera.set_acquisition_mode, mode)
            finally:
                print('releasing: {}'.format(self.acquisitionMode.__name__))
                self.lock.release()
        # getter
        return self.camera.get_acquisition_mode()

    @setting(341, "Trigger Mode", mode='s', returns='s')
    def triggerMode(self, c, mode=None):
        """
        Get/set the current trigger mode.
        # todo: list accepted values
        Arguments:
            mode    (str)   : the trigger mode.
        Returns:
                    (str)   : the trigger mode.
        """
        # setter
        if mode is not None:
            print('acquiring: {}'.format(self.triggerMode.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.triggerMode.__name__))
                yield deferToThread(self.camera.set_acquisition_mode, mode)
            finally:
                print('releasing: {}'.format(self.triggerMode.__name__))
                self.lock.release()
        # getter
        return self.camera.get_trigger_mode()

    @setting(351, "Exposure Time", time='v', returns='v')
    def exposureTime(self, c, time=None):
        """
        Get/set the current exposure time.
        # todo: list accepted values
        Arguments:
            time    (float)   : the trigger mode.
        Returns:
                    (float) : the current exposure time in seconds.
        """
        # setter
        if time is not None:
            print('acquiring: {}'.format(self.exposureTime.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.exposureTime.__name__))
                yield deferToThread(self.camera.set_exposure_time, time)
            finally:
                print('releasing: {}'.format(self.exposureTime.__name__))
                self.lock.release()
        # getter
        return self.camera.get_exposure_time()


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
    @setting(511, "Get Number Kinetics", returns='i')
    def getNumberKinetics(self, c):
        """
        Gets number of scans in a kinetic cycle.
        """
        return self.camera.get_number_kinetics()

    @setting(512, "Set Number Kinetics", numKin='i', returns='')
    def setNumberKinetics(self, c, numKin):
        """
        Sets number of scans in a kinetic cycle.
        """
        print('acquiring: {}'.format(self.setNumberKinetics.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setNumberKinetics.__name__))
            yield deferToThread(self.camera.set_number_kinetics, numKin)
        finally:
            print('releasing: {}'.format(self.setNumberKinetics.__name__))
            self.lock.release()

    # UPDATED THE TIMEOUT. FIX IT LATER
    @setting(513, "Wait For Kinetic", timeout='v[s]', returns='b')
    def waitForKinetic(self, c, timeout=1):
        """
        Waits until the given number of kinetic images are completed.
        """
        requestCalls = int(timeout['s'] / 0.050)  # number of request calls
        for i in range(requestCalls):
            print('acquiring: {}'.format(self.waitForKinetic.__name__))
            yield self.lock.acquire()
            try:
                print('acquired : {}'.format(self.waitForKinetic.__name__))
                status = yield deferToThread(self.camera.get_status)
                # useful for debugging of how many iterations have been completed in case of missed trigger pulses
                a, b = yield deferToThread(self.camera.get_series_progress)
                print(a, b)
                print(status)
            finally:
                print('releasing: {}'.format(self.waitForKinetic.__name__))
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
        # todo: gui signal
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
        #         print('acquiring: {}'.format(self.getMostRecentImage.__name__))
        yield self.lock.acquire()
        try:
            #             print('acquired : {}'.format(self.getMostRecentImage.__name__))
            image = yield deferToThread(self.camera.get_most_recent_image)
        finally:
            #             print('releasing: {}'.format(self.getMostRecentImage.__name__))
            self.lock.release()
        returnValue(image)


    """
    Signal
    """
    @setting(201, returns='')
    def start_signal_loop(self, c):
        """
        Start the loop sending images to remote clients.
        """
        self.live_update_loop = LoopingCall(self.update_signal_loop)  # loop to send images to remote clients
        self.last_image = None  # the last retrived image
        self.live_update_loop.start(
            0.1)  # a reasonable interval considering the Network speed, setting it shorter should not negatively influence the performance

    @setting(202, returns='')
    def stop_signal_loop(self, c):
        """
        Stop the loop sending images to remote clients.
        """
        self.live_update_loop.stop()

    @inlineCallbacks
    def update_signal_loop(self):
        data = yield self.getMostRecentImage(None)
        # if there is a new image since the last update, send a signal to the clients
        if data != self.last_image:
            self.last_image = data
            yield self.image_updated(data)


    # HELPER
    def _run(self, function_name):
        """
        Sets the target temperature.
        """
        print('acquiring: {}'.format(self.set_temperature.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.set_temperature.__name__))
            yield deferToThread(self.camera.set_temperature, setTemp['degC'])
        finally:
            print('releasing: {}'.format(self.set_temperature.__name__))
            self.lock.release()


if __name__ == "__main__":
    from labrad import util
    util.runServer(AndorServer())
