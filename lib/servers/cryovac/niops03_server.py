"""
### BEGIN NODE INFO
[info]
name = NIOPS03 Server
version = 1.0.0
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

from EGGS_labrad.lib.servers.polling_server import PollingServer
from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

TERMINATOR = '\r\n'
_NI03_QUERY_msg = '\x05'
_NI03_ACK_msg = '\x06'

class NIOPS03Server(SerialDeviceServer, PollingServer):
    """
    Controls the NIOPS03 power supply for the ion pump and getter.
    """

    name = 'NIOPS03 Server'
    regKey = 'NIOPS03Server'
    serNode = 'MongKok'
    port = 'COM55'

    timeout = WithUnit(3.0, 's')
    baudrate = 115200


    # SIGNALS
    pressure_update = Signal(999999, 'signal: pressure update', 'v')
    voltage_update = Signal(999998, 'signal: voltage update', 'i')
    temperature_update = Signal(999997, 'signal: temperature update', '(vv)')
    ip_power_update = Signal(999996, 'signal: ip power update', 'b')
    np_power_update = Signal(999995, 'signal: np power update', 'b')


    # STARTUP
    def initServer(self):
        # call parent initserver to support further subclassing
        super().initServer()
        # interlock stuff
        self.tt = None
        self.interlock_active = False
        self.interlock_pressure = None


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
    @setting(111, 'IP Toggle', power='b', returns='s')
    def toggle_ip(self, c, power):
        """
        Set ion pump power.
        Args:
            power   (bool)  : whether pump is to be on or off
        Returns:
                    (str)   : response from device
        """
        # setter & getter
        yield self.ser.acquire()
        if power:
            yield self.ser.write('G' + TERMINATOR)
        else:
            yield self.ser.write('B' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()
        # parse
        if resp == _NI03_ACK_msg:
            self.ip_power_update(power, self.getOtherListeners(c))
        returnValue(resp)

    @setting(112, 'NP Toggle', power='b', returns='s')
    def toggle_np(self, c, power):
        """
        Set getter power.
        Args:
            power   (bool)  : getter power status
        Returns:
                    (str)   : response from device
        """
        # setter
        yield self.ser.acquire()
        if power:
            yield self.ser.write('GN' + TERMINATOR)
        else:
            yield self.ser.write('BN' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        self.ser.release()
        # parse
        if resp == _NI03_ACK_msg:
            self.np_power_update(power, self.getOtherListeners(c))
        returnValue(resp)

    @setting(121, 'NP Mode', mode='i', returns='s')
    def np_mode(self, c, mode):
        """
        Set getter mode.
        Args:
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
        # convert from hex to int
        resp = int(resp, 16)
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


    # INTERLOCK
    @setting(311, 'IP Interlock', status='b', press='v', returns='')
    def interlock_ip(self, c, status, press):
        """
        Activates an interlock, switching off the ion pump
        if pressure exceeds a given value.
        Pressure is taken from the Twistorr74 turbo pump server.
        Arguments:
            press   (float) : the maximum pressure in mbar
        """
        # create connection to twistorr pump as needed
        try:
            self.tt = yield self.client.twistorr74_server
        except KeyError:
            self.tt = None
            raise Exception('Twistorr74 server not available for interlock.')
        # set interlock parameters
        self.interlock_active = status
        self.interlock_pressure = press


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for pressure readout.
        """
        # query
        yield self.ser.acquire()
        yield self.ser.write('Tb\r\n')
        ip_pressure = yield self.ser.read_line('\r')
        yield self.ser.write('TC\r\n')
        temp_resp = yield self.ser.read_line('\r')
        yield self.ser.write('u\r\n')
        volt_resp = yield self.ser.read_line('\r')
        self.ser.release()

        # update pressure
        self.pressure_update(float(ip_pressure))
        # process & update temperature
        temp = temp_resp.split()
        self.temperature_update((float(temp[1]), float(temp[3])))
        # process & update voltage
        self.voltage_update(int(volt_resp, 16))
        # interlock: checks
        if self.interlock_active:
            # switch off ion pump if pressure is above a certain value
            press_tmp = yield self.tt.read_pressure()
            if press_tmp >= self.interlock_pressure:
                print('problem')
                # yield self.ser.write('B' + TERMINATOR)
                # yield self.ser.read_line()


if __name__ == '__main__':
    from labrad import util
    util.runServer(NIOPS03Server())