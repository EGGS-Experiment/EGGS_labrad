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

    name = 'NIOPS03 Server'
    regKey = 'NIOPS03 Server'
    serNode = 'MongKok'
    port = 'COM52'

    timeout = WithUnit(3.0, 's')
    baudrate = 115200

    POLL_ON_STARTUP = True


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
        # interlock
        self.interlock_active = True
        self.interlock_pressure = _NI03_MAX_PRESSURE
        # interlock 2
        self.interlock2_active = False
        self.interlock2_pressure = _NI03_MIN_PRESSURE


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
        Arguments:
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
        Arguments:
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
        # convert from hex to int
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


    # INTERLOCK
    @setting(311, 'Interlock', status='b', press='v', returns='(bv)')
    def interlock(self, c, status=None, press=None):
        """
        Activates an interlock, switching off the ion pump
        and getter if pressure exceeds a given value.
        Pressure is taken from the Twistorr74 turbo pump server.
        Arguments:
            status  (bool)  : the interlock status.
            press   (float) : the maximum pressure (in mbar).
        Returns:
                    (bool)  : the interlock status.
                    (float) :  the maximum pressure (in mbar).
        """
        # empty call returns getter
        if (status is None) and (press is None):
            return (self.interlock_active, self.interlock_pressure)
        # ensure pressure is valid
        if press is None:
            pass
        elif (press < 1e-11) or (press > 1e-4):
            raise Exception('Error: invalid pressure interlock range. Must be between (1e-11, 1e-4) mbar.')
        else:
            self.interlock_pressure = press
        # set interlock parameters
        self.interlock_active = status
        return (self.interlock_active, self.interlock_pressure)
    
    @setting(312, 'Interlock 2', status='b', press='v', returns='(bv)')
    def interlock2(self, c, status=None, press=None):
        """
        Activates an interlock, switching ON the getter
        if pressure goes below a given value.
        Pressure is taken from the Twistorr74 turbo pump server.
        This is designed to allow completely self-regulating
        getter activation sequences.
        Arguments:
            status  (bool)  : the interlock status.
            press   (float) : the minimum pressure (in mbar).
        Returns:
                    (bool)  : the interlock status.
                    (float) :  the minimum pressure (in mbar).
        """
        # empty call returns getter
        if (status is None) and (press is None):
            return (self.interlock2_active, self.interlock2_pressure)
        # ensure pressure is valid
        if press is None:
            pass
        elif (press < 1e-11) or (press > 1e-4):
            raise Exception('Error: invalid pressure interlock range. Must be between (1e-11, 1e-4) mbar.')
        else:
            self.interlock2_pressure = press
        # set interlock parameters
        self.interlock2_active = status
        return (self.interlock2_active, self.interlock2_pressure)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls the device for pressure readout and checks the interlock.
        """
        # check interlock
        if self.interlock_active:
            try:
                # try to get twistorr74 server
                yield self.client.refresh()
                tt = yield self.client.twistorr74_server
                # switch off ion pump if pressure is above a certain value
                press_tmp = yield tt.pressure()
                if press_tmp >= self.interlock_pressure:
                    print('Error: Twistorr74 pressure reads {:.2e} mbar.'.format(press_tmp))
                    print('\tAbove threshold of {:.2e} mbar for Ion Pump to be on.'.format(self.interlock_pressure))
                    print('\tSending shutoff signal to ion pump and getter.')
                    try:
                        # send shutoff signals; don't use ser.acquire() since
                        # shutoff needs to happen NOW
                        yield self.ser.acquire() #tmp remove
                        yield self.ser.write('B' + TERMINATOR)
                        yield self.ser.read_line('\r')
                        yield self.ser.write('BN' + TERMINATOR)
                        yield self.ser.read_line('\r')
                        self.ser.release()
                        # update listeners on power status
                        self.ip_power_update(False)
                        self.np_power_update(False)
                        # disable interlock 2 to minimize overhead once activated
                        self.interlock2_active = False
                        # ensure interlock active
                        self.interlock_active = True
                    except Exception as e:
                        print('Error: unable to shut off ion pump and/or getter.')
                elif (press_tmp <= self.interlock2_pressure) and (self.interlock2_active):
                    print('Below pressure for getter activation.')
                    print('\tSending activation signal to getter.')
                    try:
                        # set NP activation mode
                        yield self.ser.acquire()
                        yield self.ser.write('M1' + TERMINATOR)
                        yield self.ser.read_line('\r')
                        # switch on NP
                        yield self.ser.write('GN' + TERMINATOR)
                        yield self.ser.read_line('\r')
                        self.ser.release()
                        # update listeners on power status
                        self.np_power_update(True)
                        # disable interlock 2 to minimize overhead once activated
                        self.interlock2_active = False
                        # ensure interlock active
                        self.interlock_active = True
                    except Exception as e:
                        print('Error: unable to activate getter.')
            except KeyError:
                print('Warning: Twistorr74 server not available for interlock.')
            except Exception as e:
                print('Warning: unable to read pressure from Twistorr74 server.')
                print('\tSkipping this loop.')
        # query
        yield self.pressure_ip(None)
        yield self.voltage_ip(None, None)
        yield self.temperature(None)


if __name__ == '__main__':
    from labrad import util
    util.runServer(NIOPS03Server())
