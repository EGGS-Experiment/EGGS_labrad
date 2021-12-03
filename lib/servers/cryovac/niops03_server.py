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

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.serial.serialdeviceserver import SerialDeviceServer

import time

TERMINATOR = '\r\n'
_NI03_QUERY_msg = '\x05'
_NI03_ACK_msg = '\x06'

class NIOPS03Server(SerialDeviceServer):
    """
    Controls NIOPS03 Power Supply which controls ion pumps.
    """
    name = 'NIOPS03 Server'
    regKey = 'NIOPS03Server'
    serNode = 'MongKok'
    port = 'COM55'

    timeout = WithUnit(3.0, 's')
    baudrate = 115200

    # SIGNALS
    pressure_update = Signal(999999, 'signal: pressure update', 'v')
    workingtime_update = Signal(999998, 'signal: workingtime update', '*2i')
    ip_power_update = Signal(999997, 'signal: ip power update', 'b')
    np_power_update = Signal(999996, 'signal: np power update', 'b')

    # STARTUP
    def initServer(self):
        super().initServer()
        self.listeners = set()
        # polling stuff
        self.tt = None
        self.interlock_active = False
        self.interlock_pressure = None
        self.refresher = LoopingCall(self.poll)
        from twisted.internet.reactor import callLater
        callLater(1, self.refresher.start, 5)

    def stopServer(self):
        if hasattr(self, 'refresher'):
            self.refresher.stop()
        super().stopServer()

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        """Remove a context object."""
        self.listeners.remove(c.ID)

    def getOtherListeners(self, c):
        """Get all listeners except for the context owner."""
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified


    #STATUS
    @setting(11, 'Status', returns='s')
    def get_status(self, c):
        """
        Get controller status
        Returns:
            (str): power status of all alarms and devices
        """
        yield self.ser.write('TS' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
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
        if power:
            yield self.ser.write('G' + TERMINATOR)
        else:
            yield self.ser.write('B' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
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
        if power:
            yield self.ser.write('GN' + TERMINATOR)
        else:
            yield self.ser.write('BN' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
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
        yield self.ser.write('M' + str(mode) + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        returnValue(resp)


    #PARAMETERS
    @setting(211, 'IP Pressure', returns='v')
    def pressure_ip(self, c):
        """
        Get ion pump pressure in mbar.
        Returns:
            (float): ion pump pressure
        """
        yield self.ser.write('Tb' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        resp = float(resp)
        self.pressure_update(resp)
        returnValue(resp)

    @setting(221, 'IP Voltage', voltage='v', returns='v')
    def voltage_ip(self, c, voltage=None):
        """
        Get/set ion pump voltage.
        Arguments:
            voltage (float) : pump voltage in V
        Returns:
                    (float): ion pump voltage in V
        """
        if voltage is not None:
            #convert voltage to hex
            voltage = hex(voltage)[2:]
            padleft = '0'*(4-len(voltage))
            yield self.ser.write('u' + padleft + voltage + TERMINATOR)
        yield self.ser.write('u' + TERMINATOR)
        resp = yield self.ser.read_line('\r')
        #convert from hex to int
        resp = int(resp, 16)
        returnValue(resp)

    @setting(231, 'Working Time', returns='*2i')
    def working_time(self, c):
        """
        Get working time of IP & NP.
        Returns:
            [[int, int], [int, int]]: working time of ion pump and getter
        """
        yield self.ser.write('TM' + TERMINATOR)
        ip_time = yield self.ser.read_line('\r')
        np_time = yield self.ser.read_line('\r')
        ip_time = ip_time[16:-8].split(' Hours ')
        np_time = np_time[16:-8].split(' Hours ')
        ip_time = [int(val) for val in ip_time]
        np_time = [int(val) for val in np_time]
        resp = [ip_time, np_time]
        self.workingtime_update(resp)
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
        #create connection to twistorr pump as needed
        try:
            self.tt = yield self.client.twistorr74_server
        except KeyError:
            self.tt = None
            raise Exception('Twistorr74 server not available for interlock.')
        #set interlock parameters
        self.interlock_active = status
        self.interlock_pressure = press


    # POLLING
    @setting(911, 'Set Polling', status='b', interval='v', returns='(bv)')
    def set_polling(self, c, status, interval):
        """
        Configure polling of device for values.
        """
        #ensure interval is valid
        if (interval < 1) or (interval > 60):
            raise Exception('Invalid polling interval.')
        #only start/stop polling if we are not already started/stopped
        if status and (not self.refresher.running):
            self.refresher.start(interval)
        elif status and self.refresher.running:
            self.refresher.interval = interval
        elif (not status) and (self.refresher.running):
            self.refresher.stop()
        return (self.refresher.running, self.refresher.interval)

    @setting(912, 'Get Polling', returns='(bv)')
    def get_polling(self, c):
        """
        Get polling parameters.
        """
        return (self.refresher.running, self.refresher.interval)

    @inlineCallbacks
    def poll(self):
        """
        Polls the device for pressure readout.
        """
        #get results all together
        yield self.ser.write('Tb' + TERMINATOR)
        pressure = yield self.ser.read_line()
        yield self.ser.write('TM' + TERMINATOR)
        ip_time = yield self.ser.read_line('\r')
        np_time = yield self.ser.read_line('\r')
        #update pressure
        self.pressure_update(float(pressure))
        # update workingtime
        ip_time = ip_time[16:-8].split(' Hours ')
        np_time = np_time[16:-8].split(' Hours ')
        ip_time = [int(val) for val in ip_time]
        np_time = [int(val) for val in np_time]
        self.workingtime_update([ip_time, np_time])
        #interlock
        if self.interlock_active:
            press_tmp = yield self.tt.read_pressure()
            if press_tmp >= self.interlock_pressure:
                print('problem')
                # yield self.ser.write('B' + TERMINATOR)
                # yield self.ser.read_line()


if __name__ == '__main__':
    from labrad import util
    util.runServer(NIOPS03Server())