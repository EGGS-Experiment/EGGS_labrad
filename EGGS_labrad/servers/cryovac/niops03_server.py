"""
### BEGIN NODE INFO
[info]
name = NIOPS03 Server
version = 1.1.0
description = Controls NIOPS03 Power Supply which controls the ion pump and getter
instancename = NIOPS03 Server

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

TERMINATOR = '\r\n'
_NI03_QUERY_msg = '\x05'
_NI03_ACK_msg = '$'
_NI03_MAX_PRESSURE = 1e-4
_NI03_MIN_PRESSURE = 1e-10


class NIOPS03Server(SerialDeviceServer, PollingServer):
    """
    Controls the NIOPS03 power supply for the ion pump and getter.
    """

    name =      'NIOPS03 Server'
    regKey =    'NIOPS03 Server'
    serNode =   'MongKok'
    port =      'COM38'

    timeout =   WithUnit(3.0, 's')
    baudrate =  115200

    POLL_ON_STARTUP = True


    # SIGNALS
    pressure_update =       Signal(999999,  'signal: pressure update', 'v')
    voltage_update =        Signal(999998,  'signal: voltage update', 'i')
    temperature_update =    Signal(999997,  'signal: temperature update', '(vv)')
    ip_power_update =       Signal(999996,  'signal: ip power update', 'b')
    np_power_update =       Signal(999995,  'signal: np power update', 'b')


    # STATUS
    @setting(11, 'Status', returns='s')
    def get_status(self, c):
        """
        Get controller status
        Returns:
            (str): power status of all alarms and devices
        """
        yield self.ser.acquire()
        yield self.ser.write('TS' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()
        returnValue(resp)


    # ON/OFF
    @setting(111, 'IP Toggle', status=['b', 'i'], returns='s')
    def toggle_ip(self, c, status):
        """
        Set ion pump power status.
        Arguments:
            status  (bool)  : ion pump power status.
        Returns:
                    (str)   : response from device
        """
        # ensure input is bool or valid int
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)

        # setter & getter
        yield self.ser.acquire()
        if status:
            yield self.ser.write('G' + TERMINATOR)
        else:
            yield self.ser.write('B' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()

        # parse
        if resp == _NI03_ACK_msg:
            self.notifyOtherListeners(c, status, self.ip_power_update)
        returnValue(resp)

    @setting(112, 'NP Toggle', status=['b', 'i'], returns='s')
    def toggle_np(self, c, status):
        """
        Set getter power status.
        Arguments:
            power   (bool)  : getter power status.
        Returns:
                    (str)   : response from device
        """
        # ensure input is bool or valid int
        if type(status) is int:
            if status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')
            else:
                status = bool(status)

        # setter
        yield self.ser.acquire()
        if status:
            yield self.ser.write('GN' + TERMINATOR)
        else:
            yield self.ser.write('BN' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()

        # parse
        if resp == _NI03_ACK_msg:
            self.notifyOtherListeners(c, status, self.np_power_update)
        returnValue(resp)

    @setting(121, 'NP Mode', mode='i', returns='s')
    def np_mode(self, c, mode):
        """
        Set getter mode.
        Arguments:
            mode (int)  : NP mode. [1=activation, 2=timed activation,
                                    3=conditioning, 4=timed conditioning]
        Returns:
                (str)  : response from device
        """
        yield self.ser.acquire()
        yield self.ser.write('M' + str(mode) + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()
        returnValue(resp)


    # PARAMETERS
    @setting(211, 'IP Pressure', returns='v')
    def pressure_ip(self, c):
        """
        Get ion pump pressure in mbar.
        Returns:
            (float): ion pump pressure
        """
        # getter
        yield self.ser.acquire()
        yield self.ser.write('Tb' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()
        # update values
        resp = float(resp)
        self.pressure_update(resp)
        returnValue(resp)

    @setting(221, 'IP Voltage', voltage='i', returns='i')
    def voltage_ip(self, c, voltage=None):
        """
        Get/set ion pump voltage.
        Arguments:
            voltage (int) : pump voltage in V
        Returns:
                    (int): ion pump voltage in V
        """
        # setter
        if voltage is not None:
            # convert voltage to hex
            voltage = hex(voltage)[2:]
            padleft = '0'*(4-len(voltage))
            yield self.ser.acquire()
            yield self.ser.write('U' + padleft + voltage + TERMINATOR)
            yield self.ser.read_line('\r')
            self.ser.release()

        # getter
        yield self.ser.acquire()
        yield self.ser.write('u' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()
        # parse response (in hex) and return
        resp = int(resp, 16)
        self.voltage_update(resp)
        returnValue(resp)

    @setting(231, 'Working Time', returns='*2i')
    def working_time(self, c):
        """
        Get working time of IP & NP.
        Returns:
            [[int, int], [int, int]]: working time of ion pump and getter
        """
        # query
        yield self.ser.acquire()
        yield self.ser.write('TM' + TERMINATOR)
        ip_time = yield self.ser.read_line('\r')
        np_time = yield self.ser.read_line('\r')
        self.ser.release()
        # parse
        ip_time = ip_time[16:-8].split(' Hours ')
        np_time = np_time[16:-8].split(' Hours ')
        ip_time = [int(val) for val in ip_time]
        np_time = [int(val) for val in np_time]
        resp = [ip_time, np_time]
        returnValue(resp)

    @setting(241, 'Temperature', returns='(vv)')
    def temperature(self, c):
        """
        Get ion pump and getter temperature in C.
        Returns:
            (vv): ion pump and getter temperature in C
        """
        # getter
        yield self.ser.acquire()
        yield self.ser.write('TC\r\n')
        resp = yield self.ser.read_line('\r')
        self.ser.release()

        # update values
        temp = resp.split()
        temp_list = (float(temp[1]), float(temp[3]))
        self.temperature_update(temp_list)
        returnValue(temp_list)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for pressure readout and checks the interlock.
        """
        # query device hardware
        yield self.pressure_ip(None)
        yield self.voltage_ip(None, None)
        yield self.temperature(None)


if __name__ == '__main__':
    from labrad import util
    util.runServer(NIOPS03Server())
