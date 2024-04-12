"""
### BEGIN NODE INFO
[info]
name = Power Meter Server
version = 1.0
description = Talks to the PM100D Power Meter
instancename = Power Meter Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from time import sleep
from labrad.server import setting
from labrad.gpib import GPIBManagedServer
from twisted.internet.defer import inlineCallbacks, returnValue

# import device wrappers
from PM100D import PM100DWrapper

# todo: sensor type



class PowerMeterServer(GPIBManagedServer):
    """
    Talks to power meters.
    """

    name = 'Power Meter Server'

    deviceWrappers = {
        'THORLABS PM100D': PM100DWrapper
    }


    # SYSTEM
    @setting(11, "Reset", returns='')
    def reset(self, c):
        """
        Reset the power supply to factory settings.
        """
        yield self.selectedDevice(c).reset()
        sleep(3)

    @setting(12, "Clear Buffers", returns='')
    def clear_buffers(self, c):
        """
        Clear device status buffers.
        """
        yield self.selectedDevice(c).clear_buffers()


    # CONFIGURE
    @setting(111, 'Configure Wavelength', wavelength='v', returns='v')
    def configureWavelength(self, c, wavelength=None):
        """
        Get/set the operating wavelength (in nm).
        Arguments:
            wavelength  (float) : the operating wavelength (in nm).
        Returns:
                        (float) : the operating wavelength (in nm).
        """
        return self.selectedDevice(c).configureWavelength(wavelength)

    @setting(121, 'Configure Averaging', averages='i', returns='i')
    def configureAveraging(self, c, averages=None):
        """
        Get/set the number of averages per measurement.
        Arguments:
            averages    (int)   : the number of averages per measurement.
        Returns:
                        (int)   : the number of averages per measurement.
        """
        return self.selectedDevice(c).configureAveraging(averages)

    @setting(131, 'Configure Autoranging', status=['i', 'b'], returns='b')
    def configureAutoranging(self, c, status=None):
        """
        Get/set the number of averages per measurement.
        Arguments:
            status  (bool)  : whether autoranging is on or off.
        Returns:
                    (bool)  : whether autoranging is on or off.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).configureAutoranging(status)

    @setting(132, 'Configure Range', range='v', returns='v')
    def configureRange(self, c, range=None):
        """
        Get/set the measurement range of the power meter (in W).
        Arguments:
            range   (float)  : the measurement range (in W).
        Returns:
                    (float)  : the measurement range (in W).
        """
        return self.selectedDevice(c).configureRange(range)

    @setting(141, 'Configure Mode', mode='s', returns='s')
    def configureMode(self, c, mode=None):
        """
        Get/set the measurement mode.
            Must be one of ('POW', 'CURR', 'VOLT').
        Arguments:
            mode    (str)  : the measurement mode.
        Returns:
                    (str)  : the measurement range.
        """
        if (mode is not None) and (mode not in ('POW', 'CURR', 'VOLT')):
            raise Exception("Invalid mode. Must be one of ('POW', 'CURR', 'VOLT').")
        return self.selectedDevice(c).configureMode(mode)


    # MEASUREMENT
    @setting(211, 'Measure', returns='v')
    def measure(self, c):
        """
        Get a power measurement from the power meter (in W).
        Returns:
            (float): the sensor power (in W).
        """
        return self.selectedDevice(c).measure()


if __name__ == '__main__':
    from labrad import util
    util.runServer(PowerMeterServer())