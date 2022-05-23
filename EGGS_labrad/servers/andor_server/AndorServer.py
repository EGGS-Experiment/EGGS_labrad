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

import numpy as np
from labrad.units import WithUnit
from labrad.server import LabradServer, setting, Signal

from AndorAPI import AndorAPI

IMAGE_UPDATED_SIGNAL = 142312
# todo: strip units
# todo: clean up imports
# todo: make setter/getter in one
# todo: make logger instead


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

    def initContext(self, c):
        """
        Initialize a new context object.
        """
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    '''
    Temperature Related Settings
    '''
    @setting(111, "Temperature", temp='v', returns='v')
    def temperature(self, c, temp=None):
        """
        Get/set the current/target device temperature.
        Arguments:
            temp    (float) : the target temperature (in Celsius).
        Returns:
                    (float) : the target temperature (in Celsius).
        """
        temperature = None
        print('acquiring: {}'.format(self.get_temperature.__name__))
        yield self.lock.acquire()
        if temp is not None:
        try:
            print('acquired : {}'.format(self.get_temperature.__name__))
            temperature = yield deferToThread(self.camera.get_temperature)
        finally:
            print('releasing: {}'.format(self.get_temperature.__name__))
            self.lock.release()
        if temperature is not None:
            returnValue(temperature)
        """
        Sets the target temperature.
        print('acquiring: {}'.format(self.set_temperature.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.set_temperature.__name__))
            yield deferToThread(self.camera.set_temperature, setTemp['degC'])
        finally:
            print('releasing: {}'.format(self.set_temperature.__name__))
            self.lock.release()
        """

    @setting(121, "Cooler", state=['b', 'i'], returns='b')
    def cooler(self, c):
        """
        Returns current cooler state.
        """
        cooler_state = None
        print('acquiring: {}'.format(self.get_cooler_state.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.get_cooler_state.__name__))
            cooler_state = yield deferToThread(self.camera.get_cooler_state)
        finally:
            print('releasing: {}'.format(self.get_cooler_state.__name__))
            self.lock.release()
        if cooler_state is not None:
            returnValue(cooler_state)
        """
        Turns cooler on.
        """
        print('acquiring: {}'.format(self.set_cooler_on.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.set_cooler_on.__name__))
            yield deferToThread(self.camera.set_cooler_on)
        finally:
            print('releasing: {}'.format(self.set_cooler_on.__name__))
            self.lock.release()
        """
        Turns cooler on.
        """
        print('acquiring: {}'.format(self.set_cooler_off.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.set_cooler_off.__name__))
            yield deferToThread(self.camera.set_cooler_off)
        finally:
            print('releasing: {}'.format(self.set_cooler_off.__name__))
            self.lock.release()

    '''
    EMCCD Gain Settings
    '''

    @setting(6, "Get EMCCD Gain", returns='i')
    def getEMCCDGain(self, c):
        """
        Gets the current EMCCD gain.
        """
        gain = None
        print('acquiring: {}'.format(self.getEMCCDGain.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.getEMCCDGain.__name__))
            gain = yield deferToThread(self.camera.get_emccd_gain)
        finally:
            print('releasing: {}'.format(self.getEMCCDGain.__name__))
            self.lock.release()
        if gain is not None:
            returnValue(gain)

    @setting(7, "Set EMCCD Gain", gain='i', returns='')
    def setEMCCDGain(self, c, gain):
        """
        Sets the current EMCCD gain.
        """
        print('acquiring: {}'.format(self.setEMCCDGain.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setEMCCDGain.__name__))
            yield deferToThread(self.camera.set_emccd_gain, gain)
        finally:
            print('releasing: {}'.format(self.setEMCCDGain.__name__))
            self.lock.release()
        # todo: gui signal

    '''
    Read mode
    '''

    @setting(8, "Get Read Mode", returns='s')
    def getReadMode(self, c):
        """
        Gets the current read mode.
        """
        return self.camera.get_read_mode()

    @setting(9, "Set Read Mode", readMode='s', returns='')
    def setReadMode(self, c, readMode):
        """
        Sets the current read mode.
        """
        mode = None
        print('acquiring: {}'.format(self.setReadMode.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setReadMode.__name__))
            yield deferToThread(self.camera.set_read_mode, readMode)
        finally:
            print('releasing: {}'.format(self.setReadMode.__name__))
            self.lock.release()
        if mode is not None:
            returnValue(mode)

    '''
    Shutter Mode
    '''

    @setting(100, "get_shutter_mode", returns='s')
    def get_shutter_mode(self, c):
        """
        Gets the current shutter mode.
        """
        return self.camera.get_shutter_mode()

    @setting(101, "set_shutter_mode", shutterMode='s', returns='')
    def set_shutter_mode(self, c, shutterMode):
        """
        Sets the current shutter mode.
        """
        mode = None
        print('acquiring: {}'.format(self.set_shutter_mode.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.set_shutter_mode.__name__))
            yield deferToThread(self.camera.set_shutter_mode, shutterMode)
        finally:
            print('releasing: {}'.format(self.set_shutter_mode.__name__))
            self.lock.release()
        if mode is not None:
            returnValue(mode)

    '''
    Acquisition Mode
    '''

    @setting(10, "Get Acquisition Mode", returns='s')
    def getAcquisitionMode(self, c):
        """
        Gets the current acquisition mode.
        """
        return self.camera.get_acquisition_mode()

    @setting(11, "Set Acquisition Mode", mode='s', returns='')
    def setAcquisitionMode(self, c, mode):
        """
        Sets the current acquisition Mode.
        """
        print('acquiring: {}'.format(self.setAcquisitionMode.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setAcquisitionMode.__name__))
            yield deferToThread(self.camera.set_acquisition_mode, mode)
        finally:
            print('releasing: {}'.format(self.setAcquisitionMode.__name__))
            self.lock.release()
        # todo: gui signal

    '''
    Trigger Mode
    '''

    @setting(12, "Get Trigger Mode", returns='s')
    def getTriggerMode(self, c):
        """
        Gets the current trigger mode.
        """
        return self.camera.get_trigger_mode()

    @setting(13, "Set Trigger Mode", mode='s', returns='')
    def setTriggerMode(self, c, mode):
        """
        Sets the current trigger Mode.
        """
        print('acquiring: {}'.format(self.setTriggerMode.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setTriggerMode.__name__))
            yield deferToThread(self.camera.set_trigger_mode, mode)
        finally:
            print('releasing: {}'.format(self.setTriggerMode.__name__))
            self.lock.release()
        # todo: gui signal

    '''
    Exposure Time
    '''

    @setting(14, "Get Exposure Time", returns='v[s]')
    def getExposureTime(self, c):
        """
        Gets current exposure time.
        """
        time = self.camera.get_exposure_time()
        return WithUnit(time, 's')

    @setting(15, "Set Exposure Time", expTime='v[s]', returns='v[s]')
    def setExposureTime(self, c, expTime):
        """
        Sets current exposure time.
        """
        print('acquiring: {}'.format(self.setExposureTime.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setExposureTime.__name__))
            yield deferToThread(self.camera.set_exposure_time, expTime['s'])
        finally:
            print('releasing: {}'.format(self.setExposureTime.__name__))
            self.lock.release()
        # need to request the actual set value because it may differ from the request when the request is not possible
        time = self.camera.get_exposure_time()
        # todo: gui signal
        returnValue(WithUnit(time, 's'))

    '''
    Image Region
    '''

    @setting(16, "Get Image Region", returns='*i')
    def getImageRegion(self, c):
        """
        Gets current image region.
        """
        return self.camera.get_image()

    @setting(17, "Set Image Region", horizontalBinning='i', verticalBinning='i', horizontalStart='i', horizontalEnd='i',
             verticalStart='i', verticalEnd='i', returns='')
    def setImageRegion(self, c, horizontalBinning, verticalBinning, horizontalStart, horizontalEnd, verticalStart,
                       verticalEnd):
        """
        Sets current image region.
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

    '''
    Acquisition
    '''

    @setting(18, "Start Acquisition", returns='')
    def startAcquisition(self, c):
        print('acquiring: {}'.format(self.startAcquisition.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.startAcquisition.__name__))
            # speeds up the call to start_acquisition
            yield deferToThread(self.camera.prepare_acqusition)
            yield deferToThread(self.camera.start_acquisition)
            # necessary so that start_acquisition call completes even for long kinetic series
            # yield self.wait(0.050)
            yield self.wait(0.1)
        finally:
            print('releasing: {}'.format(self.startAcquisition.__name__))
            self.lock.release()

    @setting(19, "Wait For Acquisition", returns='')
    def waitForAcquisition(self, c):
        print('acquiring: {}'.format(self.waitForAcquisition.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.waitForAcquisition.__name__))
            yield deferToThread(self.camera.wait_for_acquisition)
        finally:
            print('releasing: {}'.format(self.waitForAcquisition.__name__))
            self.lock.release()

    @setting(20, "Abort Acquisition", returns='')
    def abortAcquisition(self, c):
        # todo: gui signal
        print('acquiring: {}'.format(self.abortAcquisition.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.abortAcquisition.__name__))
            yield deferToThread(self.camera.abort_acquisition)
        finally:
            print('releasing: {}'.format(self.abortAcquisition.__name__))
            self.lock.release()

    @setting(21, "Get Acquired Data", num_images='i', returns='*i')
    def getAcquiredData(self, c, num_images=1):
        """
        Get the acquired images.
        """
        print('acquiring: {}'.format(self.getAcquiredData.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.getAcquiredData.__name__))
            image = yield deferToThread(self.camera.get_acquired_data, num_images)
        finally:
            print('releasing: {}'.format(self.getAcquiredData.__name__))
            self.lock.release()
        returnValue(image)

    @setting(33, "Get Summed Data", num_images='i', returns='*i')
    def getSummedData(self, c, num_images=1):
        """
        Get the counts with the vertical axis summed over.
        """
        print('acquiring: {}'.format(self.getAcquiredData.__name__))
        yield self.lock.acquire()
        try:
            print('acquired: {}'.format(self.getAcquiredData.__name__))
            images = yield deferToThread(self.camera.get_acquired_data, num_images)
            hbin, vbin, hstart, hend, vstart, vend = self.camera.get_image()
            x_pixels = int((hend - hstart + 1.) / (hbin))
            y_pixels = int(vend - vstart + 1.) / (vbin)
            images = np.reshape(images, (num_images, y_pixels, x_pixels))
            images = images.sum(axis=1)
            images = np.ravel(images, order='C')
            images = images.tolist()
        finally:
            print('releasing: {}'.format(self.getAcquiredData.__name__))
            self.lock.release()
        returnValue(images)

    '''
    General
    '''

    @setting(22, "Get Camera Serial Number", returns='i')
    def getCameraSerialNumber(self, c):
        """
        Gets camera serial number.
        """
        return self.camera.get_camera_serial_number()

    @setting(23, "Get Most Recent Image", returns='*i')
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

    @setting(26, "Get Number Kinetics", returns='i')
    def getNumberKinetics(self, c):
        """
        Gets number of scans in a kinetic cycle.
        """
        return self.camera.get_number_kinetics()

    @setting(27, "Set Number Kinetics", numKin='i', returns='')
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
    @setting(28, "Wait For Kinetic", timeout='v[s]', returns='b')
    def waitForKinetic(self, c, timeout=WithUnit(1, 's')):
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

    @setting(31, "Get Detector Dimensions", returns='ww')
    def get_detector_dimensions(self, c):
        print('acquiring: {}'.format(self.get_detector_dimensions.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.get_detector_dimensions.__name__))
            dimensions = yield deferToThread(self.camera.get_detector_dimensions)
        finally:
            print('releasing: {}'.format(self.get_detector_dimensions.__name__))
            self.lock.release()
        returnValue(dimensions)

    @setting(32, "getemrange", returns='(ii)')
    def getemrange(self, c):
        # emrange = yield self.camera.get_camera_em_gain_range()
        # returnValue(emrange)
        return self.camera.get_camera_em_gain_range()

    def wait(self, seconds, result=None):
        """
        Returns a deferred that will be fired later.
        """
        d = Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d

    def stop(self):
        self._stopServer()

    @inlineCallbacks
    def stopServer(self):
        """
        Shut down camera before closing.
        """
        try:
            # todo: gui signal
            print('acquiring: {}'.format(self.stopServer.__name__))
            yield self.lock.acquire()
            print('acquired : {}'.format(self.stopServer.__name__))
            self.camera.shut_down()
            print('releasing: {}'.format(self.stopServer.__name__))
            self.lock.release()
        except Exception:
            # not yet created
            pass

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
    def _lock_tmp(self):
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
