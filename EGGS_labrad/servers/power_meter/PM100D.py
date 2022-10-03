from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
# calibration
# adjustment
    # averaging
    # peak detect
    # input att CORR:LOSS:INPUT:MAGN
    # input wavelength CORR:WAV:MIN/MAX
# measure
    # mode (energy/power/current/voltage) (CONF:POW/CURR:VOLT/ENER/FREQ) CONF?
    # range
    # autorange
    # actual (READ?)
# fd
    # sensor type

# todo: get limits for values


class PM100DWrapper(GPIBDeviceWrapper):

    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self, c):
        yield self.write('*CLS')


    # CONFIGURE
    @inlineCallbacks
    def configureWavelength(self, wavelength=None):
        # setter
        if wavelength is not None:
            if (wavelength < 400) or (wavelength > 1100):
                raise Exception("Invalid wavelength. Must be between [400, 1100]nm.")
            yield self.write('CORR:WAV {:f}'.format(wavelength))

        # getter
        resp = yield self.query('CORR:WAV?')
        returnValue(float(resp))

    @inlineCallbacks
    def configureAveraging(self, averages=None):
        # setter
        if averages is not None:
            if (averages < 0) or (averages > 300):
                raise Exception("Invalid number of averages. Must be between [0, 300].")
            yield self.write('AVER {:d}'.format(averages))

        # getter
        resp = yield self.query('AVER?')
        returnValue(int(resp))

    @inlineCallbacks
    def configureAutoranging(self, status=None):
        # setter
        if status is not None:
            yield self.write('POW:RANG:AUTO {:d}'.format(status))

        # getter
        resp = yield self.query('POW:RANG:AUTO?')
        returnValue(int(resp))

    @inlineCallbacks
    def configureRange(self, range=None):
        # setter
        if range is not None:
            if (range < 1e-5) or (range > 2):
                raise Exception("Invalid number of averages. Must be between [0, 300].")
            yield self.write('POW:RANG {:f}'.format(range))

        # getter
        resp = yield self.query('POW:RANG?')
        returnValue(int(resp))

    @inlineCallbacks
    def configureMode(self, mode=None):
        # setter
        if mode is not None:
            yield self.write('CONF {:f}'.format(mode))

        # getter
        resp = yield self.query('CONF?')
        returnValue(resp.strip())

    # MEASURE
    @inlineCallbacks
    def measure(self):
        resp = yield self.query('READ?')
        returnValue(float(resp))
