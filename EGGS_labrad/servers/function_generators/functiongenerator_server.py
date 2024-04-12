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
from RigolDG1022 import RigolDG1022Wrapper
from RigolDG2052 import RigolDG2052Wrapper


class FunctionGeneratorServer(GPIBManagedServer):
    """
    Manages communication with all function generators.
    """

    name = 'Function Generator Server'
    deviceWrappers = {
        'AGILENT TECHNOLOGIES 33210A':      Agilent33210AWrapper,
        'RIGOL TECHNOLOGIES DG1022A':       RigolDG1022Wrapper,
        'RIGOL TECHNOLOGIES DG2052':        RigolDG2052Wrapper
    # '^RIGOL TECHNOLOGIES DG2([\d\w])+$'
    }


    # GENERAL
    @setting(111, 'Reset', returns='')
    def reset(self, c):
        """
        Reset the function generator.
        """
        yield self.selectedDevice(c).reset()

    @setting(112, 'Trigger', returns='')
    def trigger(self, c):
        """
        Send a trigger command to the function generator.
        """
        yield self.selectedDevice(c).trigger()

    @setting(121, 'Toggle', status=['b', 'i'], returns='b')
    def toggle(self, c, status=None):
        """
        Turn the function generator on/off.
        Arguments:
            status  (bool)  : whether the function generator is on/off.
        Returns:
                    (bool)  : whether the function generator is on/off.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).toggle(status)

    @setting(131, 'Channel', chan_num='i', returns='i')
    def channel(self, c, chan_num=None):
        """
        Set the channel number. Default is 0.
            This function allows the server to accommodate function generators with multiple outputs
            without having to specify a channel number in each function argument.
            If the function generator only has one output, this function does nothing.
        Arguments:
            status  (int)   : the channel number.
        Returns:
                    (int)   : the channel number.
        """
        return self.selectedDevice(c).channel(chan_num)

    @setting(141, 'Impedance', imp='v', returns='v')
    def impedance(self, c, imp=None):
        """
        Get/set the channel load impedance.
        This function only affects the interface values,
            and does not change the output range of the
            function generator.
        Arguments:
            imp     (float) : the load impedance.
        Returns:
                    (float) : the load impedance.
        """
        return self.selectedDevice(c).impedance(imp)


    # WAVEFORM
    @setting(211, 'Function', shape='s', returns='s')
    def function(self, c, shape=None):
        """
        Get/set the output function type.
        Shape must be one of (SIN, SQU, RAMP, PULS, NOIS, DC)
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

    @setting(223, 'Phase', phase='v', returns='v')
    def phase(self, c, phase=None):
        """
        Get/set the function phase. When output is toggled,
            the waveform will begin with this phase value.
        Arguments:
            phase   (float) : the phase (in degrees).
        Returns:
                    (float) : the phase (in degrees).
        """
        return self.selectedDevice(c).phase(phase)
    
    @setting(224, 'Offset', off='v', returns='v')
    def offset(self, c, off=None):
        """
        Get/set the function amplitude offset.
        Arguments:
            off     (float) : the offset (in V).
        Returns:
                    (float) : the offset (in V).
        """
        return self.selectedDevice(c).offset(off)


    # TRIGGER
    @setting(311, 'Trigger Mode', mode='s', returns='s')
    def triggerMode(self, c, mode=None):
        """
        Get/set the triggering mode. Can be one of:
            "IMM": Internal triggering (i.e. continuous output).
            "EXT": External triggering via TTL input.
            "BUS": External triggering via bus (e.g. USB).
        Arguments:
            mode    (str)   : the current trigger mode.
        Returns:
                    (str)   : the current trigger mode.
        """
        # check valid input
        if type(mode) == str:
            mode = mode.upper()
            if mode not in ('IMM', 'EXT', 'BUS'):
                raise Exception('Error: input must be one of ("IMM", "EXT", "BUS").')

        return self.selectedDevice(c).triggerMode(mode)

    @setting(321, 'Trigger Slope', slope='s', returns='s')
    def triggerSlope(self, c, slope=None):
        """
        Get/set the triggering slope (applies only when external triggering is enabled).
        Can be one of:
            "POS": Trigger on positive (rising) edge.
            "NEG": Trigger on negative (falling) edge.
        Arguments:
            slope   (str)   : the current trigger slope.
        Returns:
                    (str)   : the current trigger slope.
        """
        # check valid input
        if type(slope) == str:
            slope = slope.upper()
            if slope not in ('POS', 'NEG'):
                raise Exception('Error: input must be one of ("POS", "NEG").')

        return self.selectedDevice(c).triggerSlope(slope)


    # MODES
    @setting(411, 'Burst', status=['b', 'i'], returns='b')
    def burst(self, c, status=None):
        """
        Activate/deactivate burst mode.
        Arguments:
            status  (bool) : the status of burst mode.
        Returns:
                    (bool) : the status of burst mode.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)

        return self.selectedDevice(c).burst(status)

    @setting(412, 'Burst Mode', mode='s', returns='s')
    def burstMode(self, c, mode=None):
        """
        Get/set the burst mode (applies only when burst mode is enabled).
        Can be one of:
            "TRIG": fd
            "GAT":  fd
        Arguments:
            mode    (str)   : the current burst mode.
        Returns:
                    (str)   : the current burst mode.
        """
        # check valid input
        if type(mode) == str:
            mode = mode.upper()
            if mode not in ('TRIG', 'GAT'):
                raise Exception('Error: input must be one of ("TRIG", "GAT").')

        return self.selectedDevice(c).burstMode(mode)


    # todo: SWEEP
    # todo: MODULATION

    # SYNCHRONIZATION
    @setting(611, 'Sync', status=['b', 'i'], returns='b')
    def sync(self, c, status=None):
        """
        Toggle output of the TTL sync signal.
        Arguments:
            status  (bool)  : the status of the SYNC output signal.
        Returns:
                    (bool)  : the status of the SYNC output signal.
        """
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)

        return self.selectedDevice(c).sync(status)

    @setting(621, 'Clock Reference', source='s', returns='s')
    def clock_reference(self, c, source=None):
        """
        Set the reference clock source.
        Can be one of:
            "INT": the function generator's internal clock.
            "EXT": an external clock source.
        Arguments:
            status  (str)  : the source of the reference clock.
        Returns:
                    (str)  : the source of the reference clock.
        """
        # check valid input
        if type(source) is str:
            source = source.upper()
            if source not in ('INT', 'EXT'):
                raise Exception('Error: input must be one of ("INT", "EXT").')

        return self.selectedDevice(c).clock_reference(source)


if __name__ == '__main__':
    from labrad import util
    util.runServer(FunctionGeneratorServer())
