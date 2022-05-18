"""
### BEGIN NODE INFO
[info]
name = Function Generator Server
version = 1.1.0
description = Talks to function generators.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.server import setting
from labrad.gpib import GPIBManagedServer

# import device wrappers
from Agilent33210A import Agilent33210AWrapper


class FunctionGeneratorServer(GPIBManagedServer):
    """
    Manages communication with all function generators..
    """

    name = 'Function Generator Server'

    deviceWrappers = {
        'AGILENT TECHNOLOGIES 33210A': Agilent33210AWrapper
    }


    # GENERAL
    @setting(111, 'Reset', returns='')
    def reset(self, c):
        """
        Reset the function generator.
        """
        yield self.selectedDevice(c).reset()

    @setting(121, 'Toggle', status=['b', 'i'], returns='b')
    def toggle(self, c, status=None):
        """
        Turn the function generator on/off.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).toggle(status)


    # WAVEFORM
    @setting(211, 'Function', shape='s', returns='s')
    def function(self, c, shape=None):
        """
        Get/set the function shape.
        Arguments:
            shape   (str) : the function shape.
        Returns:
                    (str) : the frequency shape.
        """
        return self.selectedDevice(c).function(shape)

    @setting(221, 'Frequency', freq='v', returns='v')
    def frequency(self, c, freq=None):
        """
        Get/set the function frequency (in Hz).
        Arguments:
            freq    (float) : the frequency (in Hz).
        Returns:
                    (float) : the frequency (in Hz).
        """
        return self.selectedDevice(c).frequency(freq)

    @setting(222, 'Amplitude', ampl='v', returns='v')
    def amplitude(self, c, ampl=None):
        """
        Get/set the function amplitude.
        Arguments:
            ampl    (float) : the amplitude (in V).
        Returns:
                    (float) : the amplitude (in V).
        """
        return self.selectedDevice(c).amplitude(ampl)
    
    @setting(223, 'Offset', off='v', returns='v')
    def offset(self, c, off=None):
        """
        Get/set the function amplitude offset.
        Arguments:
            off     (float) : the offset (in V).
        Returns:
                    (float) : the offset (in V).
        """
        return self.selectedDevice(c).amplitude(off)


    # MODULATION

    # SWEEP


if __name__ == '__main__':
    from labrad import util
    util.runServer(FunctionGeneratorServer())
