"""
API for Andor Cameras.
Uses Andor's SDK2.
"""
import os
import ctypes as c

from EGGS_labrad.config.andor_config import AndorConfig as config
# todo: migrate the text-to-value dicts to enums; also supports reverse lookup
# todo: migrate API functions to have same style as dll - i was stupid to format them differently
# todo: i.e. make it SetVSAmplitude instead of set_vertical_shift_amplitude


class AndorInfo(object):
    """
    Stores information about the Andor Camera.
    """

    def __init__(self):
        self.serial_number =            None
        self.width =                    None
        self.height =                   None

        self.min_temp =                 None
        self.max_temp =                 None
        self.cooler_state =             None
        self.temperature_setpoint =     None
        self.temperature =              None


        self.min_gain =                 None
        self.max_gain =                 None
        self.emccd_gain =               None


        self.vertical_shift_speed_values =      None
        self.vertical_shift_speed =             None
        self.vertical_shift_amplitude_values =  None
        self.vertical_shift_amplitude =         None

        self.horizontal_shift_speed_values =        None
        self.horizontal_shift_speed =               None
        self.horizontal_shift_preamp_gain_values =  None
        self.horizontal_shift_preamp_gain =         None


        self.read_mode =                None
        self.acquisition_mode =         None
        self.trigger_mode =             None
        self.shutter_mode =             None


        self.exposure_time =            None
        self.accumulate_cycle_time =    None
        self.kinetic_cycle_time =       None
        self.number_kinetics =          None


        self.image_region =             None
        self.image_rotate =             None
        self.image_flip_vertical =      None
        self.image_flip_horizontal =    None



class AndorAPI(object):
    """
    Python interface for functions defined in Andor's SDK2.
    Since Python lacks pass by reference for immutable variables, some of these variables are stored as class members.
    For example, the temperature, gain, gainRange, status etc. are stored in the class.
    """

    def __init__(self):
        try:
            # load and initialize DLL
            print('Loading DLL')
            self.dll = c.windll.LoadLibrary(config.path_to_dll)
            print('Initializing Camera...')
            error = self.dll.Initialize(os.path.dirname(__file__))
            print('Initialization Complete: {}'.format(ERROR_CODE[error]))

            # get camera capabilities and related info
            self.info = AndorInfo()
            # todo: who should be andorinfo and who should simply be returned?
            # note: seems like settings that map text-to-num are stored to avoid
            # difficulty of reversing the conversion dict
            self.get_detector_dimensions()
            self.get_temperature_range()
            self.acquire_camera_serial_number()
            self.get_camera_em_gain_range()
            # get information about vertical/horizontal pixel shift capabilities
            # note: these may differ by camera
            self.get_vertical_shift_speed_values()
            self.get_vertical_shift_amplitude_values()
            self.get_horizontal_shift_speed_values()
            self.get_horizontal_shift_preamp_gain_values()


            # set up Andor camera per config file and populate
            # AndorInfo data structure with default/current values
            self.set_read_mode(config.read_mode)
            self.set_acquisition_mode(config.acquisition_mode)
            self.set_trigger_mode(config.trigger_mode)
            self.set_shutter_mode(config.shutter_mode)

            self.set_emccd_gain(config.emccd_gain)
            self.get_emccd_gain()
            self.set_exposure_time(config.exposure_time)
            self.set_vertical_shift_amplitude(config.vertical_shift_amplitude)
            self.set_vertical_shift_speed(config.vertical_shift_speed)
            self.set_horizontal_shift_preamp_gain(config.horizontal_shift_preamp_gain)
            self.set_horizontal_shift_speed(config.horizontal_shift_speed)

            # set image to full size with default binning
            self.set_image_region(config.binning[0], config.binning[0], 1, self.info.width, 1, self.info.height)
            self.set_image_rotate(config.image_rotate)
            self.set_image_flip((config.image_flip_horizontal, config.image_flip_vertical))

            # get default temperature config
            self.set_cooler_state(True)
            self.set_temperature_setpoint(config.set_temperature)
            self.get_cooler_state()
            self.get_temperature_setpoint()
            self.get_temperature_actual()

        except Exception as e:
            print('Error Initializing Camera:', e)
            raise Exception(e)


    """
    GENERAL/INFO
    """
    def print_get_software_version(self):
        """
        Gets the version of the SDK.
        """
        eprom = c.c_int()
        cofFile = c.c_int()
        vxdRev = c.c_int()
        vxdVer = c.c_int()
        dllRev = c.c_int()
        dllVer = c.c_int()
        self.dll.GetSoftwareVersion(c.byref(eprom), c.byref(cofFile), c.byref(vxdRev), c.byref(vxdVer), c.byref(dllRev),
                                    c.byref(dllVer))
        print('Software Version')
        print(eprom)
        print(cofFile)
        print(vxdRev)
        print(vxdVer)
        print(dllRev)
        print(dllVer)

    def print_get_capabilities(self):
        """
        Gets the exact capabilities of the connected Andor camera.
        """

        class AndorCapabilities(c.Structure):
            _fields_ = [('ulSize',              c.c_ulong),
                        ('ulAcqModes',          c.c_ulong),
                        ('ulReadModes',         c.c_ulong),
                        ('ulTriggerModes',      c.c_ulong),
                        ('ulCameraType',        c.c_ulong),
                        ('ulPixelMode',         c.c_ulong),
                        ('ulSetFunctions',      c.c_ulong),
                        ('ulGetFunctions',      c.c_ulong),
                        ('ulFeatures',          c.c_ulong),
                        ('ulPCICard',           c.c_ulong),
                        ('ulEMGainCapability',  c.c_ulong),
                        ('ulFTReadModes',       c.c_ulong),
                        ]

        caps = AndorCapabilities()
        caps.ulSize = c.c_ulong(c.sizeof(caps))
        error = self.dll.GetCapabilities(c.byref(caps))
        print('ulAcqModes', '{:07b}'.format(caps.ulAcqModes))
        print('ulReadModes', '{:06b}'.format(caps.ulReadModes))
        print('ulTriggerModes', '{:08b}'.format(caps.ulTriggerModes))
        print('ulCameraType', '{}'.format(caps.ulCameraType))
        print('ulPixelMode', '{:032b}'.format(caps.ulPixelMode))
        print('ulSetFunctions', '{:025b}'.format(caps.ulSetFunctions))
        print('ulGetFunctions', '{:016b}'.format(caps.ulGetFunctions))
        print('ulFeatures', '{:020b}'.format(caps.ulFeatures))
        print('ulPCICard', '{}'.format(caps.ulPCICard))
        print('ulEMGainCapability', '{:020b}'.format(caps.ulEMGainCapability))
        print('ulFTReadModes', '{:06b}'.format(caps.ulFTReadModes))

    def get_detector_dimensions(self):
        """
        Returns the dimensions of the detector.
        Returns:
            (int, int)  : the width and height (in pixels).
        """
        detector_width, detector_height = c.c_int(), c.c_int()
        self.dll.GetDetector(c.byref(detector_width), c.byref(detector_height))
        self.info.width = detector_width.value
        self.info.height = detector_height.value
        return [self.info.width, self.info.height]

    def acquire_camera_serial_number(self):
        """
        Acquire the camera's serial number and set it as a
        class attribute.
        Should only be called during initialization.
        """
        serial_number = c.c_int()
        error = self.dll.GetCameraSerialNumber(c.byref(serial_number))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.serial_number = serial_number.value
        else:
            raise Exception(ERROR_CODE[error])

    def get_camera_serial_number(self):
        """
        Returns the camera's serial number.
        Returns:
            int :   the camera's serial number.
        """
        return self.info.serial_number

    def get_status(self):
        status = c.c_int()
        error = self.dll.GetStatus(c.byref(status))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            return ERROR_CODE[status.value]
        else:
            raise Exception(ERROR_CODE[error])

    def shut_down(self):
        error = self.dll.ShutDown()
        return ERROR_CODE[error]


    """
    TEMPERATURE-RELATED
    """
    def get_temperature_range(self):
        """
        Gets the range of available temperatures.
        Returns:
            (int, int): the min and max camera temperatures (in Celsius).
        """
        min_temp, max_temp = c.c_int(), c.c_int()
        self.dll.GetTemperatureRange(c.byref(min_temp), c.byref(max_temp))
        self.info.min_temp = min_temp.value
        self.info.max_temp = max_temp.value
        return [self.info.min_temp, self.info.max_temp]

    def get_temperature_actual(self):
        temperature = c.c_int()
        error = self.dll.GetTemperature(c.byref(temperature))
        if ERROR_CODE[error] in ('DRV_TEMP_STABILIZED', 'DRV_TEMP_NOT_REACHED', 'DRV_TEMP_DRIFT', 'DRV_TEMP_NOT_STABILIZED'):
            self.info.temperature = temperature.value
            return temperature.value
        else:
            raise Exception(ERROR_CODE[error])

    def set_temperature_setpoint(self, temperature):
        error = self.dll.SetTemperature(c.c_int(int(temperature)))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.temperature_setpoint = int(temperature)
        else:
            raise Exception(ERROR_CODE[error])

    def get_temperature_setpoint(self):
        return self.info.temperature_setpoint

    def set_cooler_state(self, state):
        """
        Sets state of the camera's TEC cooler.
        """
        error = None
        if state:
            error = self.dll.CoolerON()
        else:
            error = self.dll.CoolerOFF()
        if not (ERROR_CODE[error] == 'DRV_SUCCESS'):
            raise Exception(ERROR_CODE[error])

    def get_cooler_state(self):
        """
        Reads the state of the cooler.
        """
        cooler_state = c.c_int()
        error = self.dll.IsCoolerOn(c.byref(cooler_state))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.cooler_state = bool(cooler_state)
            return self.info.cooler_state
        else:
            raise Exception(ERROR_CODE[error])


    """
    EMCCD GAIN
    """
    def get_camera_em_gain_range(self):
        min_gain = c.c_int()
        max_gain = c.c_int()
        error = self.dll.GetEMGainRange(c.byref(min_gain), c.byref(max_gain))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.min_gain = min_gain.value
            self.info.max_gain = max_gain.value
            return (min_gain.value, max_gain.value)
        else:
            raise Exception(ERROR_CODE[error])

    def set_emccd_gain(self, gain):
        error = self.dll.SetEMCCDGain(c.c_int(int(gain)))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.emccd_gain = gain
        else:
            raise Exception(ERROR_CODE[error])

    def get_emccd_gain(self):
        gain = c.c_int()
        error = self.dll.GetEMCCDGain(c.byref(gain))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.emccd_gain = gain.value
            return gain.value
        else:
            raise Exception(ERROR_CODE[error])


    """
    READ MODE
    """
    def get_read_mode(self):
        return self.info.read_mode

    def set_read_mode(self, mode):
        try:
            mode_number = READ_MODE[mode]
        except KeyError:
            raise Exception("Incorrect read mode {}".format(mode))

        error = self.dll.SetReadMode(c.c_int(mode_number))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.read_mode = mode
        else:
            raise Exception(ERROR_CODE[error])


    """
    SHUTTER MODE
    """
    def set_shutter_mode(self, mode):
        try:
            mode_number = SHUTTER_MODE[mode]
        except KeyError:
            raise Exception("Incorrect shutter mode {}".format(mode))

        error = self.dll.SetShutter(c.c_int(1), c.c_int(mode_number), c.c_int(0), c.c_int(0))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.shutter_mode = mode
        else:
            raise Exception(ERROR_CODE[error])

    def get_shutter_mode(self):
        return self.info.shutter_mode


    """
    ACQUISITION MODE
    """
    def set_acquisition_mode(self, mode):
        try:
            mode_number = ACQUISITION_MODE[mode]
        except KeyError:
            raise Exception("Incorrect acquisition mode {}".format(mode))

        error = self.dll.SetAcquisitionMode(c.c_int(mode_number))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.acquisition_mode = mode
        else:
            raise Exception(ERROR_CODE[error])

    def get_acquisition_mode(self):
        return self.info.acquisition_mode

    def get_acquisition_timings(self):
        exposure = c.c_float()
        accumulate = c.c_float()
        kinetic = c.c_float()
        error = self.dll.GetAcquisitionTimings(c.byref(exposure), c.byref(accumulate), c.byref(kinetic))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.exposure_time = exposure.value
            self.info.accumulate_cycle_time = accumulate.value
            self.info.kinetic_cycle_time = kinetic.value
        else:
            raise Exception(ERROR_CODE[error])


    """
    TRIGGER MODE
    """
    def set_trigger_mode(self, mode):
        try:
            mode_number = TRIGGER_MODE[mode]
        except KeyError:
            raise Exception("Incorrect trigger mode {}".format(mode))

        error = self.dll.SetTriggerMode(c.c_int(mode_number))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.trigger_mode = mode
        else:
            raise Exception(ERROR_CODE[error])

    def get_trigger_mode(self):
        return self.info.trigger_mode


    """
    EXPOSURE TIME
    """
    def set_exposure_time(self, time):
        error = self.dll.SetExposureTime(c.c_float(time))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.get_acquisition_timings()
        else:
            raise Exception(ERROR_CODE[error])

    def get_exposure_time(self):
        return self.info.exposure_time


    """
    SHIFTING - VERTICAL/HORIZONTAL
    """
    def set_vertical_shift_speed(self, index_speed):
        error = self.dll.SetVSSpeed(c.c_int(int(index_speed)))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.vertical_shift_speed = int(index_speed)
        else:
            raise Exception(ERROR_CODE[error])

    def get_vertical_shift_speed(self):
        return self.info.vertical_shift_speed

    def set_vertical_shift_amplitude(self, index_amplitude):
        error = self.dll.SetVSAmplitude(c.c_int(int(index_amplitude)))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.vertical_shift_amplitude = int(index_amplitude)
        else:
            raise Exception(ERROR_CODE[error])

    def get_vertical_shift_amplitude(self):
        return self.info.vertical_shift_amplitude

    def set_horizontal_shift_speed(self, index_speed):
        error = self.dll.SetHSSpeed(c.c_int(0), c.c_int(int(index_speed)))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.horizontal_shift_speed = int(index_speed)
        else:
            raise Exception(ERROR_CODE[error])

    def get_horizontal_shift_speed(self):
        return self.info.horizontal_shift_speed

    def set_horizontal_shift_preamp_gain(self, index_gain):
        error = self.dll.SetPreAmpGain(c.c_int(int(index_gain)))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.horizontal_shift_preamp_gain = int(index_gain)
        else:
            raise Exception(ERROR_CODE[error])

    def get_horizontal_shift_preamp_gain(self):
        return self.info.horizontal_shift_preamp_gain


    """
    IMAGE REGION
    """
    def set_image_region(self, hbin, vbin, hstart, hend, vstart, vend):
        hbin, vbin, hstart, hend, vstart, vend = map(int, (hbin, vbin, hstart, hend, vstart, vend))
        error = self.dll.SetImage(c.c_int(hbin), c.c_int(vbin), c.c_int(hstart),
                                  c.c_int(hend), c.c_int(vstart), c.c_int(vend))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.image_region = [hbin, vbin, hstart, hend, vstart, vend]
        else:
            raise Exception(ERROR_CODE[error])

    def get_image_region(self):
        return self.info.image_region

    def set_image_rotate(self, state):
        """
        Set the image rotation status.
        """
        try:
            state_number = ROTATION_SETTING[state]
        except KeyError:
            raise Exception("Incorrect rotation state: {}".format(state))

        error = self.dll.SetImageRotate(c.c_int(state_number))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.image_rotate = state
        else:
            raise Exception(ERROR_CODE[error])

    def get_image_rotate(self):
        """
        Get the image rotation status.
        """
        return self.info.image_rotate

    def set_image_flip(self, flip_status):
        """
        Set the image flip status.
        """
        flip_horizontal, flip_vertical = flip_status
        error = self.dll.SetImageFlip(c.c_int(flip_horizontal), c.c_int(flip_vertical))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.image_flip_horizontal = bool(flip_horizontal)
            self.info.image_flip_vertical = bool(flip_vertical)
        else:
            raise Exception(ERROR_CODE[error])

    def get_image_flip(self):
        """
        Get the image flip status (horizontal, vertical).
        """
        return (self.info.image_flip_horizontal, self.info.image_flip_vertical)


    """
    ACQUISITION - RUN
    """
    def prepare_acqusition(self):
        error = self.dll.PrepareAcquisition()
        if ERROR_CODE[error] == "DRV_SUCCESS":
            return
        else:
            raise Exception(ERROR_CODE[error])

    def start_acquisition(self):
        error = self.dll.StartAcquisition()
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            return
        else:
            raise Exception(ERROR_CODE[error])

    def wait_for_acquisition(self):
        error = self.dll.WaitForAcquisition()
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            return
        else:
            raise Exception(ERROR_CODE[error])

    def abort_acquisition(self):
        error = self.dll.AbortAcquisition()
        if ERROR_CODE[error] in ['DRV_SUCCESS', 'DRV_IDLE']:
            return
        else:
            raise Exception(ERROR_CODE[error])


    """
    ACQUISITION - DATA
    """
    def get_size_of_circular_buffer(self):
        index = c.c_long()
        error = self.dll.GetSizeOfCircularBuffer(c.byref(index))
        if ERROR_CODE[error] == "DRV_SUCCESS":
            return index.value
        else:
            raise Exception(ERROR_CODE[error])

    def get_total_number_images_acquired(self):
        index = c.c_long()
        error = self.dll.GetTotalNumberImagesAcquired(c.byref(index))
        if ERROR_CODE[error] == "DRV_SUCCESS":
            return index.value
        else:
            raise Exception(ERROR_CODE[error])

    def get_number_new_images(self):
        first = c.c_long()
        last = c.c_long()
        error = self.dll.GetNumberNewImages(c.byref(first), c.byref(last))
        if ERROR_CODE[error] == "DRV_SUCCESS":
            return first.value, last.value
        else:
            raise Exception(ERROR_CODE[error])

    def get_acquired_data(self, num_images):
        hbin, vbin, hstart, hend, vstart, vend = self.info.image_region
        dim = (hend - hstart + 1) * (vend - vstart + 1) / float(hbin * vbin)
        dim = int(num_images * dim)

        image_struct = c.c_int * dim
        image = image_struct()
        error = self.dll.GetAcquiredData(c.pointer(image), dim)

        if ERROR_CODE[error] == 'DRV_SUCCESS':
            image = image[:]
            return image
        else:
            raise Exception(ERROR_CODE[error])

    def get_most_recent_image(self):
        hbin, vbin, hstart, hend, vstart, vend = self.info.image_region
        dim = (hend - hstart + 1) * (vend - vstart + 1) / float(hbin * vbin)
        dim = int(dim)

        image_struct = c.c_uint32 * dim
        image = image_struct()
        error = self.dll.GetMostRecentImage(c.pointer(image), dim)

        if ERROR_CODE[error] == 'DRV_SUCCESS':
            image = image[:]
            return image
        else:
            raise Exception(ERROR_CODE[error])

    def get_oldest_image(self):
        hbin, vbin, hstart, hend, vstart, vend = self.info.image_region
        dim = (hend - hstart + 1) * (vend - vstart + 1) / float(hbin * vbin)
        dim = int(dim)

        image_struct = c.c_uint32 * dim
        image = image_struct()
        error = self.dll.GetOldestImage(c.pointer(image), dim)

        if ERROR_CODE[error] == 'DRV_SUCCESS':
            image = image[:]
            return image
        else:
            raise Exception(ERROR_CODE[error])


    """
    KINETIC SERIES
    """
    def set_number_kinetics(self, numKin):
        error = self.dll.SetNumberKinetics(c.c_int(int(numKin)))
        if ERROR_CODE[error] == 'DRV_SUCCESS':
            self.info.number_kinetics = numKin
        else:
            raise Exception(ERROR_CODE[error])

    def get_number_kinetics(self):
        # todo - bug: needs to have been set before first call
        return self.info.number_kinetics

    def get_series_progress(self):
        acc = c.c_long()
        series = c.c_long()
        error = self.dll.GetAcquisitionProgress(c.byref(acc), c.byref(series))
        if ERROR_CODE[error] == "DRV_SUCCESS":
            return acc.value, series.value
        else:
            raise Exception(ERROR_CODE[error])


    """
    Retrieve Camera Capabilities
    """
    def get_vertical_shift_speed_values(self):
        # get number of vertical shift speed values
        num_vs_speed_vals = c.c_int()
        error = self.dll.GetNumberVSSpeeds(c.byref(num_vs_speed_vals))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            raise Exception(ERROR_CODE[error])
        # convert result back to python value
        num_vs_speed_vals = num_vs_speed_vals.value

        # convert indices to actual shift speed values
        vs_speed_vals = [0.] * num_vs_speed_vals
        for i in range(num_vs_speed_vals):
            speed_val = c.c_float()
            error = self.dll.GetVSSpeed(c.c_int(i), c.byref(speed_val))
            if ERROR_CODE[error] == 'DRV_SUCCESS':
                vs_speed_vals[i] = speed_val.value
            else:
                raise Exception(ERROR_CODE[error])

        # store results in AndorInfo
        self.info.vertical_shift_speed_values = vs_speed_vals

    def get_vertical_shift_amplitude_values(self):
        # get number of vertical shift amplitude values
        num_vs_ampl_vals = c.c_int()
        error = self.dll.GetNumberVSAmplitudes(c.byref(num_vs_ampl_vals))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            raise Exception(ERROR_CODE[error])
        # convert result back to python value
        num_vs_ampl_vals = num_vs_ampl_vals.value

        # convert indices to shift amplitude string values
        vs_ampl_strings = [''] * num_vs_ampl_vals
        for i in range(num_vs_ampl_vals):
            ampl_string = c.create_string_buffer(32)
            error = self.dll.GetVSAmplitudeString(c.c_int(i), ampl_string)
            if ERROR_CODE[error] == 'DRV_SUCCESS':
                # vs_ampl_strings[i] = repr(ampl_string.value)
                vs_ampl_strings[i] = ampl_string.value.decode("utf-8")
            else:
                raise Exception(ERROR_CODE[error])

        # store results in AndorInfo
        self.info.vertical_shift_amplitude_values = vs_ampl_strings

    def get_horizontal_shift_speed_values(self):
        # get number of horizontal shift speed values
        num_hs_speed_vals = c.c_int()
        # note - restrict use case to single-channel, default amplifier
        error = self.dll.GetNumberHSSpeeds(c.c_int(0), c.c_int(0), c.byref(num_hs_speed_vals))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            raise Exception(ERROR_CODE[error])
        # convert result back to python value
        num_hs_speed_vals = num_hs_speed_vals.value

        # tmp remove
        # get number of horizontal shift speed values
        num_adc_channels = c.c_int()
        # note - restrict use case to single-channel, default amplifier
        error = self.dll.GetNumberADChannels(c.byref(num_adc_channels))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            raise Exception(ERROR_CODE[error])
        # convert result back to python value
        num_adc_channels = num_adc_channels.value
        print('\n\t\tnum adc channels: {}'.format(num_adc_channels))
        # tmp remove

        # tmp remove
        # get number of horizontal shift speed values
        num_amps = c.c_int()
        # note - restrict use case to single-channel, default amplifier
        error = self.dll.GetNumberAmp(c.byref(num_amps))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            raise Exception(ERROR_CODE[error])
        # convert result back to python value
        num_amps = num_amps.value
        print('\n\t\tnum amplifiers: {}'.format(num_amps))
        # tmp remove

        # convert indices to actual shift speed values
        hs_speed_vals = [0.] * num_hs_speed_vals
        for i in range(num_hs_speed_vals):
            speed_val = c.c_float()
            # note - restrict use case to single-channel, default amplifier
            error = self.dll.GetHSSpeed(c.c_int(0), c.c_int(0), c.c_int(i), c.byref(speed_val))
            if ERROR_CODE[error] == 'DRV_SUCCESS':
                hs_speed_vals[i] = speed_val.value
            else:
                raise Exception(ERROR_CODE[error])

        # store results in AndorInfo
        self.info.horizontal_shift_speed_values = hs_speed_vals

    def get_horizontal_shift_preamp_gain_values(self):
        # get number of horizontal shift preamp gain values
        num_preamp_gain_vals = c.c_int()
        error = self.dll.GetNumberPreAmpGains(c.byref(num_preamp_gain_vals))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            raise Exception(ERROR_CODE[error])
        # convert result back to python value
        num_preamp_gain_vals = num_preamp_gain_vals.value

        # convert indices to actual preamp gain values
        preamp_gain_vals = [0.] * num_preamp_gain_vals
        for i in range(num_preamp_gain_vals):
            gain_val = c.c_float()
            error = self.dll.GetPreAmpGain(c.c_int(i), c.byref(gain_val))
            if ERROR_CODE[error] == 'DRV_SUCCESS':
                preamp_gain_vals[i] = gain_val.value
            else:
                raise Exception(ERROR_CODE[error])

        # store results in AndorInfo
        self.info.horizontal_shift_preamp_gain_values = preamp_gain_vals


"""
HARDWARE STATUS CODES
"""
# todo: migrate this stupid fucking implementation to a fucking enum
ERROR_CODE = {
    20001: "DRV_ERROR_CODES",
    20002: "DRV_SUCCESS",
    20003: "DRV_VXNOTINSTALLED",
    20006: "DRV_ERROR_FILELOAD",
    20007: "DRV_ERROR_VXD_INIT",
    20010: "DRV_ERROR_PAGELOCK",
    20011: "DRV_ERROR_PAGE_UNLOCK",
    20013: "DRV_ERROR_ACK",
    20024: "DRV_NO_NEW_DATA",
    20026: "DRV_SPOOLERROR",
    20034: "DRV_TEMP_OFF",
    20035: "DRV_TEMP_NOT_STABILIZED",
    20036: "DRV_TEMP_STABILIZED",
    20037: "DRV_TEMP_NOT_REACHED",
    20038: "DRV_TEMP_OUT_RANGE",
    20039: "DRV_TEMP_NOT_SUPPORTED",
    20040: "DRV_TEMP_DRIFT",
    20050: "DRV_COF_NOTLOADED",
    20053: "DRV_FLEXERROR",
    20066: "DRV_P1INVALID",
    20067: "DRV_P2INVALID",
    20068: "DRV_P3INVALID",
    20069: "DRV_P4INVALID",
    20070: "DRV_INIERROR",
    20071: "DRV_COERROR",
    20072: "DRV_ACQUIRING",
    20073: "DRV_IDLE",
    20074: "DRV_TEMPCYCLE",
    20075: "DRV_NOT_INITIALIZED",
    20076: "DRV_P5INVALID",
    20077: "DRV_P6INVALID",
    20083: "P7_INVALID",
    20089: "DRV_USBERROR",
    20091: "DRV_NOT_SUPPORTED",
    20099: "DRV_BINNING_ERROR",
    20990: "DRV_NOCAMERA",
    20991: "DRV_NOT_SUPPORTED",
    20992: "DRV_NOT_AVAILABLE"
}

READ_MODE = {
    'Full Vertical Binning':    0,
    'Multi-Track':              1,
    'Random-Track':             2,
    'Single-Track':             3,
    'Image':                    4
}

ACQUISITION_MODE = {
    'Single Scan':      1,
    'Accumulate':       2,
    'Kinetics':         3,
    'Fast Kinetics':    4,
    'Run till abort':   5
}

TRIGGER_MODE = {
    'Internal':                 0,
    'External':                 1,
    'External Start':           6,
    'External Exposure':        7,
    'External FVB EM':          9,
    'Software Trigger':         10,
    'External Charge Shifting': 12
}

SHUTTER_MODE = {
    'Auto':     0,
    'Open':     1,
    'Close':    2
}

ROTATION_SETTING = {
    'None':             0,
    'Clockwise':        1,
    'Anticlockwise':    2
}

