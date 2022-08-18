"""
### BEGIN NODE INFO
[info]
name = Power Supply Server
version = 1.0.0
description = Talks to power supplies

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

# import device wrappers
from Keithley2231A import Keithley2231AWrapper
from GWInstekGPP3060 import GWInstekGPP3060Wrapper
# todo: channels
# todo: output (series/parallel)


class PowerSupplyServer(GPIBManagedServer):
    """
    Manages communication with all power supplies.
    """

    name = 'Power Supply Server'

    deviceWrappers = {
        'KEITHLEY INSTRUMENTS 2231A-30-3': Keithley2231AWrapper,
        'GW INSTEK GPP-3060': GWInstekGPP3060Wrapper
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

    @setting(21, "Remote", status=['i', 'b'], returns='')
    def remote(self, c, status):
        """
        Set remote mode to enable/disable remote communication.
        Arguments:
            status  (bool)  : the power state of the power supply.
        Returns:
                    (bool)  : the power state of the power supply.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).remote(status)


    # CHANNEL OUTPUT
    @setting(111, 'Channel Toggle', channel='i', status=['b', 'i'], returns='b')
    def channelToggle(self, c, channel, status=None):
        """
        Turn the power supply on/off.
        Arguments:
            channel (int)   : the channel number.
            status  (bool)  : the power state of the power supply.
        Returns:
                    (bool)  : the power state of the power supply.
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)
        return self.selectedDevice(c).channelToggle(channel, status)

    @setting(112, 'Channel Mode', channel='i', mode='s', returns='b')
    def channelMode(self, c, channel, mode=None):
        """
        too&&&
        Arguments:
            channel (int)   : the channel number.
            mode    (bool)  : the power state of the power supply.
        Returns:
                    (bool)  : the power state of the power supply.
        """
        return self.selectedDevice(c).channelMode(channel, mode)

    @setting(121, 'Channel Voltage', channel='i', voltage='v', returns='v')
    def channelVoltage(self, c, channel, voltage=None):
        """
        Get/set the target voltage of the power supply.
        Arguments:
            channel (int)   : the channel number.
            voltage (float) : the target voltage (in V).
        Returns:
                    (float) : the target voltage (in V).
        """
        return self.selectedDevice(c).channelVoltage(channel, voltage)

    @setting(122, 'Channel Current', channel='i', current='v', returns='v')
    def channelCurrent(self, c, channel, current=None):
        """
        Get/set the target current of the power supply.
        Arguments:
            channel (int)   : the channel number.
            current (float) : the target current (in A).
        Returns:
                    (float) : the target current (in A).
        """
        return self.selectedDevice(c).channelCurrent(channel, current)


    # MEASURE
    @setting(211, 'Measure Voltage', channel='i', returns='v')
    def measureVoltage(self, c, channel):
        """
        Get the measured output voltage of the channel.
        Arguments:
            channel (int)   : the channel number.
        Returns:
                    (float) : the measured voltage (in V).
        """
        return self.selectedDevice(c).channelVoltageMeasure(channel)

    @setting(212, 'Measure Current', channel='i', returns='v')
    def measureCurrent(self, c, channel):
        """
        Get the measured output current of the channel.
        Arguments:
            channel (int)   : the channel number.
        Returns:
                    (float) : the measured current (in A).
        """
        return self.selectedDevice(c).channelCurrentMeasure(channel)


if __name__ == '__main__':
    from labrad import util
    util.runServer(PowerSupplyServer())
