"""
### BEGIN NODE INFO
[info]
name =  Andor Server
version = 1.2.0
description = Server for the Andor iXon3.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 30

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
from twisted.internet.threads import deferToThread
from twisted.internet.defer import returnValue, DeferredLock, inlineCallbacks

import numpy as np
from labrad.util import wakeupCall
from labrad.server import setting, Signal

from EGGS_labrad.servers import PollingServer
from EGGS_labrad.servers.andor_server.AndorAPI import AndorAPI

IMAGE_UPDATED_SIGNAL =          142312
MODE_UPDATED_SIGNAL =           142313
PARAMETER_UPDATED_SIGNAL =      142314
# todo: finish moving all to _run helper function
# todo: add binning
# todo: spice up documentation
# todo: make signal updates use send to other listeners
# todo: what is a prescan? baseline clamp? kinetic series length?


class AndorServer(PollingServer):
    """
    Contains methods that interact with the Andor CCD Cameras.
    """

    name = "Andor Server"
    image_updated =         Signal(IMAGE_UPDATED_SIGNAL,        'signal: image updated', '*i')
    mode_updated =          Signal(MODE_UPDATED_SIGNAL,         'signal: mode updated', '(ss)')
    parameter_updated =     Signal(PARAMETER_UPDATED_SIGNAL,    'signal: parameter updated', '(ss)')

    POLL_INTERVAL_MIN =     0.1


    """
    CORE SERVER FUNCTIONALITY
    """
    def initServer(self):
        super().initServer()
        # create camera-related objects
        self.lock =                 DeferredLock()
        self.camera =               AndorAPI()
        self.last_image =           None
        self.acquisition_running =  False

    def stopServer(self):
        super().stopServer()

        # shut down the camera when the server is stopped
        try:
            # release deferred lock and shut down immediately
            self.lock.release()
            self.camera.shut_down()

            # print('acquiring: {}'.format(self.stopServer.__name__))
            # yield self.lock.acquire()
            # print('acquired : {}'.format(self.stopServer.__name__))
            # self.camera.shut_down()
            # print('releasing: {}'.format(self.stopServer.__name__))
            # self.lock.release()
        except Exception as e:
            print(repr(e))
            pass


    """
    GENERAL
    """
    @setting(11, "Info Serial Number", returns='i')
    def infoSerialNumber(self, c):
        """
        Gets the camera's serial number.
        Returns:
            (int)   : the camera's serial number.
        """
        return self.camera.get_camera_serial_number()

    @setting(12, "Info Detector Dimensions", returns='(ii)')
    def infoDetectorDimensions(self, c):
        """
        Gets the dimensions of the camera's detector.
        Returns:
            (ww)   : the dimensions of the camera's detector.
        """
        return self.camera.get_detector_dimensions()


    @setting(13, "Info EMCCD Range", returns='(ii)')
    def infoEMCCDRange(self, c):
        """
        Get the EMCCD gain range.
        Returns:
            (int, int)  : the minimum and maximum EMCCD gain values.
        """
        return self.camera.get_camera_em_gain_range()

    @setting(14, "Info Vertical Shift", returns='*(s*s)')
    def infoVerticalShift(self, c):
        """
        Get information about the camera's vertical shift capabilities.
        Returns:
            (str, list(str))  : tuples containing the parameter name and a list of all values.
        """
        # get valid values from camera info structure
        vs_speed_vals = (
            'Vertical Shift Speed (us)',
            [str(round(val, 2)) for val in self.camera.info.vertical_shift_speed_values]
        )
        vs_ampl_vals = (
            'Vertical Shift Voltage (V)',
            [str(val) for val in self.camera.info.vertical_shift_amplitude_values]
        )
        return [vs_speed_vals, vs_ampl_vals]

    @setting(15, "Info Horizontal Shift", returns='*(s*s)')
    def infoHorizontalShift(self, c):
        """
        Get information about the camera's horizontal shift capabilities.
        Returns:
            (str, list(str))  : tuples containing the parameter name and a list of all values.
        """
        # get valid values from camera info structure
        hs_speed_vals = (
            'Horizontal Shift Speed (MHz)',
            [str(round(val, 2)) for val in self.camera.info.horizontal_shift_speed_values]
        )
        hs_preamp_gain_vals = (
            'Preamplifier Gain',
            [str(round(val, 2)) for val in self.camera.info.horizontal_shift_preamp_gain_values]
        )
        return [hs_speed_vals, hs_preamp_gain_vals]

    @setting(21, "Get Status", returns='s')
    def getStatus(self, c):
        """
        Gets the camera status.
        Returns:
            (str)   : the camera status.
        """
        return self.camera.get_status()


    """
    TEMPERATURE
    """
    @setting(111, "Temperature Setpoint", temp='v', returns='v')
    def temperature_setpoint(self, c, temp=None):
        """
        Get/set the camera's temperature setpoint.
        Arguments:
            temp    (float) : the target temperature (in Celsius).
        Returns:
                    (float) : the current temperature (in Celsius).
        """
        temp = yield self._run('temperature_setpoint', 'get_temperature_setpoint', 'set_temperature_setpoint', temp)
        self.notifyOtherListeners(c, ("temp_set", str(temp)), self.parameter_updated)
        returnValue(temp)

    @setting(112, "Temperature Actual", returns='v')
    def temperature_actual(self, c):
        """
        Get the current device temperature.
        Arguments:
            temp    (float) : the target temperature (in Celsius).
        Returns:
                    (float) : the current temperature (in Celsius).
        """
        temp = yield self._run('temperature', 'get_temperature_actual')
        self.notifyOtherListeners(c, ("temp_actual", str(temp)), self.parameter_updated)
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
    CAMERA MODE SETUP
    """
    @setting(601, "Mode Acquisition", mode='s', returns='s')
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
        self.notifyOtherListeners(c, ("acquisition", mode), self.mode_updated)
        returnValue(mode)

    @setting(311, "Mode Read", mode='s', returns='s')
    def modeRead(self, c, mode=None):
        """
        Get/set the current read mode.
        Can be one of   ('Full Vertical Binning', 'Multi-Track',
                        'Random-Track', 'Single-Track', 'Image').
        Arguments:
            mode    (str)   : the current read mode.
        Returns:
                    (str)   : the current read mode.
        """
        mode = yield self._run('Mode Read', 'get_read_mode', 'set_read_mode', mode)
        self.notifyOtherListeners(c, ("read", mode), self.mode_updated)
        returnValue(mode)

    @setting(341, "Mode Trigger", mode='s', returns='s')
    def modeTrigger(self, c, mode=None):
        """
        Get/set the current trigger mode.
        Can be one of   ('Internal', 'External', 'External Start',
                        'External Exposure', 'External FVB EM',
                        'Software Trigger', 'External Charge Shifting').
        Arguments:
            mode    (str)   : the trigger mode.
        Returns:
                    (str)   : the trigger mode.
        """
        mode = yield self._run('Mode Trigger', 'get_trigger_mode', 'set_trigger_mode', mode)
        self.notifyOtherListeners(c, ("trigger", mode), self.mode_updated)
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
        self.notifyOtherListeners(c, ("shutter", mode), self.mode_updated)
        returnValue(mode)


    """
    READOUT SETUP
    """
    @setting(211, "Setup EMCCD Gain", gain='i', returns='i')
    def setupEMCCDGain(self, c, gain=None):
        """
        Get/set the current EMCCD gain.
        Arguments:
            gain    (int)   : the EMCCD gain.
        Returns:
                    (int)   : the EMCCD gain.
        """
        gain = yield self._run('EMCCD Gain', 'get_emccd_gain', 'set_emccd_gain', gain)
        self.notifyOtherListeners(c, ("emccd_gain", str(gain)), self.parameter_updated)
        returnValue(gain)

    @setting(231, "Setup Exposure Time", time='v', returns='v')
    def setupExposureTime(self, c, time=None):
        """
        Get/set the current exposure time.
        Arguments:
            time    (float) : the exposure time to set (in seconds).
        Returns:
                    (float) : the current exposure time in seconds.
        """
        time = yield self._run('Exposure Time', 'get_exposure_time', 'set_exposure_time', time)
        self.notifyOtherListeners(c, ("exposure_time", str(time)), self.parameter_updated)
        returnValue(time)

    @setting(241, "Setup Vertical Shift Speed", idx_speed='i', returns='i')
    def setupVerticalShiftSpeed(self, c, idx_speed=None):
        """
        Get/set the vertical shift speed.
        # todo: describe how it works
        # todo: tell them they have to convert value to index
        Arguments:
            idx_ampl    (int)   : the vertical shift speed index.
        Returns:
                        (int)   : the vertical shift speed index.
        """
        idx_speed = yield self._run('Vertical Shift Speed',
                                   'get_vertical_shift_speed', 'set_vertical_shift_speed',
                                   idx_speed)
        self.notifyOtherListeners(c, ("vs_speed", str(idx_speed)), self.parameter_updated)
        returnValue(idx_speed)

    @setting(242, "Setup Vertical Shift Amplitude", idx_ampl='i', returns='i')
    def setupVerticalShiftAmplitude(self, c, idx_ampl=None):
        """
        Get/set the vertical shift amplitude.
        # todo: describe how it works
        # todo: tell them they have to convert value to index
        Arguments:
            idx_ampl    (int)   : the vertical shift amplitude/voltage index.
        Returns:
                        (int)   : the vertical shift amplitude/voltage index.
        """
        idx_ampl = yield self._run('Vertical Shift Amplitude',
                                   'get_vertical_shift_amplitude', 'set_vertical_shift_amplitude',
                                   idx_ampl)
        self.notifyOtherListeners(c, ("vs_ampl", str(idx_ampl)), self.parameter_updated)
        returnValue(idx_ampl)

    @setting(243, "Setup Horizontal Shift Speed", idx_speed='i', returns='i')
    def setupHorizontalShiftSpeed(self, c, idx_speed=None):
        """
        Get/set the horizontal shift speed.
        # todo: describe how it works
        # todo: tell them they have to convert value to index
        Arguments:
            idx_ampl    (int)   : the horizontal shift speed index.
        Returns:
                        (int)   : the horizontal shift speed index.
        """
        idx_speed = yield self._run('Horizontal Shift Amplitude',
                                   'get_horizontal_shift_speed', 'set_horizontal_shift_speed',
                                   idx_speed)
        self.notifyOtherListeners(c, ("hs_speed", str(idx_speed)), self.parameter_updated)
        returnValue(idx_speed)

    @setting(244, "Setup Horizontal Shift Preamp Gain", idx_gain='i', returns='i')
    def setupHorizontalShiftPreampGain(self, c, idx_gain=None):
        """
        Get/set the horizontal shift speed.
        # todo: describe how it works
        # todo: tell them they have to convert value to index
        Arguments:
            idx_ampl    (int)   : the horizontal shift speed index.
        Returns:
                        (int)   : the horizontal shift speed index.
        """
        idx_gain = yield self._run('Horizontal Shift Preamp Gain',
                                   'get_horizontal_shift_preamp_gain', 'set_horizontal_shift_preamp_gain',
                                   idx_gain)
        self.notifyOtherListeners(c, ("hs_preampgain", str(idx_gain)), self.parameter_updated)
        returnValue(idx_gain)
    # todo: frame transfer


    """
    IMAGE REGION
    """
    @setting(411, "Image Region Get", returns='*i')
    def getImageRegion(self, c):
        """
        Gets the current image region.
        Returns:
            [binx, biny, startx, stopx, starty, stopy]
        """
        return self.camera.get_image_region()

    @setting(412, "Image Region Set",
             horizontalBinning='i', verticalBinning='i',
             horizontalStart='i', horizontalEnd='i',
             verticalStart='i', verticalEnd='i',
             returns='')
    def setImageRegion(self, c,
                       horizontalBinning, verticalBinning,
                       horizontalStart, horizontalEnd,
                       verticalStart, verticalEnd):
        """
        Sets the current image region.
        Arguments:
            horizontalBinning   (int)   : the horizontal binning multiple.
            verticalBinning     (int)   : the vertical binning multiple.
            horizontalStart     (int)   : the horizontal start position.
            horizontalEnd       (int)   : the horizontal end position.
            verticalStart       (int)   : the vertical start position.
            verticalEnd         (int)   : the vertical end position.
        """
        print('acquiring: {}'.format(self.setImageRegion.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.setImageRegion.__name__))
            yield deferToThread(self.camera.set_image_region, horizontalBinning, verticalBinning, horizontalStart,
                                horizontalEnd, verticalStart, verticalEnd)
        finally:
            print('releasing: {}'.format(self.setImageRegion.__name__))
            self.lock.release()

    @setting(411, "Image Region Get", returns='*i')
    def getImageRegion(self, c):
        """
        Gets the current image region.
        Returns:
            [binx, biny, startx, stopx, starty, stopy]
        """
        return self.camera.get_image_region()

    @setting(421, "Image Rotate", rotation='s', returns='s')
    def imageRotate(self, c, rotation=None):
        """
        Get/set the rotation state of the camera image (90 degrees).
        Arguments:
            rotation    (str)   : the image rotation state. Can be one of ('None', 'Clockwise', 'Anticlockwise').
        Returns:
                        (str)   : the rotation state.
        """
        rotation_state = yield self._run('Image Rotate', 'get_image_rotate', 'set_image_rotate', rotation)
        # todo: notify other listeners
        returnValue(rotation_state)

    @setting(422, "Image Flip", flip_status='(bb)', returns='(bb)')
    def imageFlip(self, c, flip_status=None):
        """
        Get/set whether the camera image is flipped (90 degrees).
        Arguments:
            rotation    (bool, bool)    : horizontal and vertical image flip, respectively.
        Returns:
                        (bool, bool)    : horizontal and vertical image flip, respectively.
        """
        flip_status = yield self._run('Image Flip', 'get_image_flip', 'set_image_flip', flip_status)
        # todo: notify other listeners
        returnValue(flip_status)


    """
    Kinetic Series
    """
    @setting(511, "Kinetic Number", num='i', returns='i')
    def kineticNumber(self, c, num=None):
        """
        Get/set the number of scans in a kinetic cycle.
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
            yield wakeupCall(0.050)
        returnValue(False)


    """
    ACQUISITION - RUN
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
            yield wakeupCall(0.1)
            self.acquisition_running = True
        finally:
            print('releasing: {}'.format(self.acquisitionStart.__name__))
            self.lock.release()

        # todo: check if acquisition has finished somehow (e.g. if we run single scan)

    @setting(612, "Acquisition Stop", returns='')
    def acquisitionStop(self, c):
        """
        Stop acquisition.
        """
        print('acquiring: {}'.format(self.acquisitionStop.__name__))
        yield self.lock.acquire()
        try:
            print('acquired : {}'.format(self.acquisitionStop.__name__))
            yield deferToThread(self.camera.abort_acquisition)
            self.acquisition_running = False
        finally:
            print('releasing: {}'.format(self.acquisitionStop.__name__))
            self.lock.release()

    @setting(613, "Acquisition Wait", returns='')
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

    @setting(621, "Acquisition Status", returns='b')
    def acquisitionStatus(self, c):
        """
        Get acquisition status.
        Returns:
            (bool): whether acquisition is stopped or started.
        """
        return self.acquisition_running

    @setting(631, "Buffer Size", returns='i')
    def buffer_size(self, c):
        """
        Get the maximum number of images that the circular buffer can store
        based on the current settings.
        Returns:
            int: the maximum number of images that can be stored.
        """
        return self.camera.get_size_of_circular_buffer()

    @setting(632, "Buffer New Images", returns='(ii)')
    def buffer_new_images(self, c):
        """
        Get the total number of new images in the buffer.
        Returns:
            (int, int): the indices of the first and last new image, respectively.
        """
        return self.camera.get_number_new_images()


    """
    ACQUISITION - DATA
    """
    @setting(721, "Acquire Data", num_images='i', returns='*i')
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

    @setting(722, "Acquire Data Summed", num_images='i', returns='*i')
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
            # acquire images
            print('acquired: {}'.format(self.acquireDataSummed.__name__))
            images = yield deferToThread(self.camera.get_acquired_data, num_images)

            # sum image pixels
            hbin, vbin, hstart, hend, vstart, vend = self.camera.get_image_region()
            x_pixels = int((hend - hstart + 1.) / (hbin))
            y_pixels = int(vend - vstart + 1.) / (vbin)

            # idk, todo: document
            images = np.reshape(images, (num_images, y_pixels, x_pixels)).sum(axis=1)
            images = np.ravel(images, order='C')
        finally:
            print('releasing: {}'.format(self.acquireDataSummed.__name__))
            self.lock.release()
        returnValue(images.tolist())

    @setting(731, "Acquire Image Recent", returns='*i')
    def acquireImageRecent(self, c):
        """
        Returns the most recent image from the circular buffer.
        """
        # print('acquiring: {}'.format(self.getMostRecentImage.__name__))
        yield self.lock.acquire()
        try:
            # print('acquired : {}'.format(self.getMostRecentImage.__name__))
            image_data = yield deferToThread(self.camera.get_most_recent_image)
        finally:
            # print('releasing: {}'.format(self.getMostRecentImage.__name__))
            self.lock.release()

        # update listeners
        if np.all(image_data != self.last_image):
            self.last_image = image_data
            self.notifyOtherListeners(c, image_data, self.image_updated)
        returnValue(image_data)

    @setting(732, "Acquire Image Oldest", returns='*i')
    def acquireImageOldest(self, c):
        """
        Returns the oldest image from the circular buffer.
        Image will no longer be available after retrieval.
        """
        # get data
        # print('acquiring: {}'.format(self.getMostRecentImage.__name__))
        yield self.lock.acquire()
        try:
            # print('acquired : {}'.format(self.getMostRecentImage.__name__))
            image_data = yield deferToThread(self.camera.get_oldest_image)
        finally:
            # print('releasing: {}'.format(self.getMostRecentImage.__name__))
            self.lock.release()

        # update listeners
        if np.all(image_data != self.last_image):
            self.last_image = image_data
            self.notifyOtherListeners(c, image_data, self.image_updated)
        returnValue(image_data)


    """
    POLLING
    """
    @inlineCallbacks
    def _poll(self):
        """
        Polls the camera for image readout.
        """
        try:
            data = yield self.acquireImageRecent(None)
            #temp = yield self.temperature(None)
        except Exception as e:
            print('poll failure')
            print(e)
        # if there is a new image since the last update, send a signal to the clients
        # todo: maybe this is source of error
        # if data != self.last_image:
        #     self.last_image = data
        #     yield self.image_updated(data)


    """
    HELPER FUNCTIONS
    """
    @inlineCallbacks
    def _run(self, function_name, getter, setter=None, setter_val=None):
        """
        Runs a getter/setter combo.
        """
        # setter
        if (setter_val is not None) and (setter is not None):
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
