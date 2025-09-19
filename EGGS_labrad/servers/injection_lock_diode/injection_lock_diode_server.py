"""
### BEGIN NODE INFO
[info]
name =Injection Lock Diode Current Server(
version = 1.0.0
description = Controls the MFF101 Flipper Mount from ThorLabs.
instancename = Injection Lock Diode Current Server

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
import pyserial

from EGGS_labrad.servers import SerialDeviceServer, serial


#
class InjectionLockDiodeCurrentServer(SerialDeviceServer):
    """
    Controls the current controller for the 729 injection lock diode.
    """

    name = 'Injection Lock Diode Current Server'
    regKey = 'InjectionLockDiodeCurrentServer'
    serNode = 'mongkok'
    port = 'COM5'

    timeout = WithUnit(5.0, 's')
    baudrate = 38400

    # CORE
    @setting(13, 'Set State', state = 'i' returns='s')
    def set_state(self, c, state):
        """
        Sets the current of the device in nA
        Returns:
            (str): the response from the current controller
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write(f'out.w {state} \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        self.ser.release()
        returnValue(resp)

    @setting(12, 'Set Current nA', current= 'v', returns='s')
    def set_current_nA(self, c, current):
        """
        Sets the current of the device in nA
        Returns:
            (str): the response from the current controller
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write(f'iout.na.w {current} \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        self.ser.release()
        returnValue(resp)

    # CORE
    @setting(13, 'Set Current uA', current= 'v', returns='s')
    def set_current_uA(self, c, current):
        """
        Sets the current of the device in uA
        Returns:
            (str): the response from the current controller
        """
        # get status
        current = current*1e3
        yield self.ser.acquire()
        yield self.ser.write(f'iout.na.w {current} \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        self.ser.release()
        returnValue(resp)

    @setting(14, 'Set Current mA', current= 'v', returns='s')
    def set_current_mA(self, c, current):
        """
        Sets the current of the device in mA
        Returns:
            (str): the response from the current controller
        """
        # get status
        current = current*1e6
        yield self.ser.acquire()
        yield self.ser.write(f'iout.na.w {current} \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        self.ser.release()
        returnValue(resp)

    @setting(15, 'Set Current Limit mA', current= 'v', returns='s')
    def set_current_limit_mA(self, c, current):
        """
        Sets the current limit of the device in mA
        Returns:
            (str): the response from the current controller
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write(f'ilim.ma.w {current} \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        self.ser.release()
        returnValue(resp)

    ### Read from current controller

    @setting(21, 'Get State', returns='s')
    def get_state(self, c):
        """
        Sets the current limit of the device in mA
        Returns:
            (str): the response from the current controller
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write(f'out.r \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        self.ser.release()
        returnValue(resp)

    @setting(22, 'Get Current nA', returns='v')
    def get_current_nA(self, c):
        """
        Get the current of the device in nA
        Returns:
            (str): the response from the current controller
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write(f'iout.na.r \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        resp = float(resp)
        self.ser.release()
        returnValue(resp)

    @setting(23, 'Get Current uA', returns='v')
    def get_current_uA(self, c):
        """
        Get the current of the device in uA
        Returns:
            (str): the response from the current controller
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write(f'iout.na.r \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        resp = float(resp)/1e3
        self.ser.release()
        returnValue(resp)


    @setting(24, 'Get Current mA', returns='v')
    def get_current_mA(self, c):
        """
        Get the current of the device in mA
        Returns:
            (str): the response from the current controller
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write(f'iout.na.r \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        resp = float(resp)/1e6
        self.ser.release()
        returnValue(resp)


    @setting(26, 'Get Diode Status', returns='s')
    def get_diode_status(self, c):
        """
        Gets the current and voltage applied to the diode
        Returns:
            (str): the response from the current controller
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write(f'diode.r \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        self.ser.release()
        returnValue(resp)

    @setting(27, 'Get Device ID', returns='s')
    def get_device_id(self, c):
        """
        Gets the current and voltage applied to the diode
        Returns:
            (str): the response from the current controller
        """
        # get status
        yield self.ser.acquire()
        yield self.ser.write(f'id? \n'.encode('utf-8'))
        resp = yield self.ser.read_line('\n').decode('utf-8')
        self.ser.release()
        returnValue(resp)

if __name__ == '__main__':
    from labrad import util
    util.runServer(FlipperServer())
