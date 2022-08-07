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
# todo: channels
# todo: output (series/parallel)


class PowerSupplyServer(GPIBManagedServer):
    """
    Manages communication with all power supplies.
    """

    name = 'Power Supply Server'

    deviceWrappers = {
        #'RIGOL TECHNOLOGIES DS1104Z Plus': Keithley2231AWrapper
    }


    # SYSTEM
    @setting(11, "Reset", returns='')
    def reset(self, c):
        """
        Reset the power supply to factory settings.
        """
        dev = self.selectedDevice(c)
        yield dev.reset()
        sleep(3)

    @setting(12, "Clear Buffers", returns='')
    def clear_buffers(self, c):
        """
        Clear device status buffers.
        """
        dev = self.selectedDevice(c)
        yield dev.clear_buffers()



    # OUTPUT
    @setting(111, 'Toggle', status=['b', 'i'], returns='b')
    def toggle(self, c, status=None):
        """
        Turn the power supply on/off.
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
        return self.selectedDevice(c).toggle(status)

    @setting(121, 'Voltage', voltage='v', returns='v')
    def voltage(self, c, voltage=None):
        """
        Get/set the voltage of the power supply.
        Arguments:
            voltage (float) : the voltage (in V).
        Returns:
                    (float) : the voltage (in V).
        """
        return self.selectedDevice(c).voltage(voltage)

    @setting(131, 'Current', current='v', returns='v')
    def current(self, c, current=None):
        """
        Get/set the current of the power supply.
        Arguments:
            current (float) : the current (in A).
        Returns:
                    (float) : the current (in A).
        """
        return self.selectedDevice(c).current(current)


if __name__ == '__main__':
    from labrad import util
    util.runServer(PowerSupplyServer())
