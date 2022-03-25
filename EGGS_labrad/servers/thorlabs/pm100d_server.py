"""
### BEGIN NODE INFO
[info]
name = Lakeshore336 Server
version = 1.0
description = Talks to the PM100D Power Meter
instancename = Lakeshore336 Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.units import WithUnit
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.servers import PollingServer, SerialDeviceServer

POWERSIGNAL = 646517
TERMINATOR = '\n'


class PM100DServer(SerialDeviceServer, PollingServer):
    """
    Talks to the PM100D Power Meter.
    """

    name = 'PM100D Server'
    regKey = 'PM100D Server'
    serNode = 'MongKok'
    #port = 'COM24'

    timeout = WithUnit(5.0, 's')

    # SIGNALS
    power_update = Signal(POWERSIGNAL, 'signal: power update', 'v')


    # SYSTEM
    @setting(11, "Reset", returns='')
    def reset(self, c):
        """
        Reset the device to factory settings.
        """
        yield self.ser.acquire()
        yield self.ser.write('*RST')
        self.ser.release


    @setting(12, "Clear Buffers", returns='')
    def clear_buffers(self, c):
        """
        Clear device status buffers.
        """
        yield self.ser.acquire()
        yield self.ser.write('*CLS')
        self.ser.release

    @setting(13, "Identify", returns='s')
    def identify(self, c):
        """
        Get the identity of the device.
        """
        yield self.ser.acquire()
        yield self.ser.write('*IDN?')
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(resp)


    # ACQUISITION
    @setting(111, 'Averaging', rate='v', returns='*1v')
    def averaging(self, c, rate=None):
        """
        Get the sensor averaging rate (1 sample takes ~3ms).
        Arguments:
            rate    (float): the averaging rate.
        Returns:
                    (float): the averaging rate.
        """
        # set
        if rate is not None:
            if (rate <= 0) or (rate >= 3000):
                yield self.ser.acquire()
                yield self.ser.write('SENS:AVER:COUN {:d}'.format(rate) + TERMINATOR)
                self.ser.release()
            else:
                raise Exception('Invalid input: averaging rate must be in ***todo value***.')
        # query
        yield self.ser.acquire()
        yield self.ser.write('SENS:AVER:COUN?' + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(resp)

    @setting(112, 'Ranging', range='v', returns='v')
    def ranging(self, c, range=None):
        """
        Get the sensor range.
        Arguments:
            range   (float): the averaging range.
        Returns:
                    (float): the averaging range.
        """
        # set
        if range is not None:
            #todo: fix value 3000
            if (range <= 0) or (range >= 3000):
                yield self.ser.acquire()
                yield self.ser.write('POW:RANG: {:d}'.format(range) + TERMINATOR)
                self.ser.release()
            else:
                raise Exception('Invalid input: range must be in ***todo: get value***')
        # query
        yield self.ser.acquire()
        yield self.ser.write('POW:RANG?' + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(resp)


    # CONFIG
    @setting(211, 'Wavelength', wavelength='v', returns='v')
    def wavelength(self, c, wavelength=None):
        """
        Get/set the operating wavelength (in nm).
        Arguments:
            wavelength  (float) : the operating wavelength (in nm).
        Returns:
                        (float) : the operating wavelength (in nm).
        """
        # setter
        if wavelength is not None:
            if (wavelength <= 400) or (wavelength >= 1100):
                yield self.ser.acquire()
                yield self.ser.write('CORR:WAV {:d}'.format(wavelength) + TERMINATOR)
                self.ser.release()
            else:
                raise Exception('Invalid input: wavelength must be in range (400nm, 1100nm).')
        # query
        yield self.ser.acquire()
        yield self.ser.write('CORR:WAV?' + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(resp)


    # MEASUREMENT
    @setting(311, 'Measure Start', returns='')
    def measureStart(self, c):
        """
        Configure measurement and start.
        Returns:
            (float): the sensor power (in mW).
        """
        # configure power measurement
        yield self.ser.acquire()
        yield self.ser.write('CONF:POW' + TERMINATOR)
        self.ser.release()
        # start measurement
        yield self.ser.acquire()
        yield self.ser.write('MEAS:FREQ' + TERMINATOR)
        self.ser.release()

    @setting(321, 'Power', returns='v')
    def power(self, c):
        """
        Get the sensor power.
        Returns:
            (float): the sensor power (in mW).
        """
        # query
        yield self.ser.acquire()
        yield self.ser.write('FETC?' + TERMINATOR)
        resp = yield self.ser.read_line()
        self.ser.release()
        # update value
        resp = float(resp)
        self.power_update(resp)
        returnValue(resp)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for temperature readout.
        """
        yield self.power(None)


if __name__ == '__main__':
    from labrad import util
    util.runServer(PM100DServer())