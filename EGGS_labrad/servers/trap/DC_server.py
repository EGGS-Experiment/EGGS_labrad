"""
### BEGIN NODE INFO
[info]
name = DC Server
version = 1.0.0
description = Communicates with the AMO8 box for control of all DC voltages.
instancename = DC Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.units import WithUnit
from labrad.util import wakeupCall
from labrad.server import setting, Signal, inlineCallbacks

from twisted.internet.defer import returnValue
from EGGS_labrad.servers import SerialDeviceServer, PollingServer

TERMINATOR = '\r\n'

# *** todo: implement input error checking so we don't have problems downstream


class DCServer(SerialDeviceServer, PollingServer):
    """
    Communicates with the AMO8 box for control of all DC voltages.
    """

    name =      'DC Server'
    regKey =    'DCServer'
    serNode =   'MongKok'
    port =      'COM3'

    timeout =   WithUnit(5.0, 's')
    baudrate =  38400

    POLL_INTERVAL_ON_STARTUP = 10


    # SIGNALS
    toggle_update =     Signal(999997, 'signal: toggle update', '(ib)')
    voltage_update =    Signal(999999, 'signal: voltage update', '(iv)')
    hv_update =         Signal(999998, 'signal: hv update', '(vv)')


    # GENERAL
    @setting(11, 'Clear', returns='s')
    def clear(self, c):
        """
        Clear all voltages & states.
        Returns:
            (str): response from device
        """
        yield self.ser.acquire()
        yield self.ser.write('clear.w\r\n')
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        returnValue(resp)

    @setting(12, 'Inputs', returns='(vv)')
    def inputs(self, c):
        """
        Read high voltage inputs and current draws.
        Returns:
            (vv): (HVin1, Iin1)
        """
        # getter
        yield self.ser.acquire()
        yield self.ser.write('HVin.r\r\n')
        # add delay to allow messages to finish transferring
        yield wakeupCall(0.2)
        v1 = yield self.ser.read_line('\n')
        i1 = yield self.ser.read_line('\n')
        self.ser.release()

        # parse input
        inputs = tuple([float((hv_val.strip().split(':'))[1]) for hv_val in (v1, i1)])
        self.hv_update(inputs)
        returnValue(inputs)

    @setting(13, 'Alarm', status=['b', 'i'], returns='b')
    def alarm(self, c, status=None):
        """
        Set the input alarm status.
            The input alarms shut off all outputs if
            the current draw exceeds a threshold value.
        Arguments:
            status  (bool)  : whether the input alarms are on/off.
        Returns:
                    (bool)  : whether the input alarms are on/off.
        """
        # ensure input is of correct type
        if (type(status) is int) and (status not in (0, 1)):
            raise Exception('Error: invalid input. Must be a boolean, 0, or 1.')

        # setter
        yield self.ser.acquire()
        if status is not None:
            yield self.ser.write('alarm.w {:d}\r\n'.format(status))
        else:
            yield self.ser.write('alarm.r\r\n')

        # get response
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        resp = resp.strip()

        # parse response
        if resp == 'ON':
            resp = True
        elif resp == 'OFF':
            resp = False
        else:
            raise Exception('Error: bad readback from device.')
        returnValue(resp)

    # todo: reflash amo8 to have remote readback and flash
    @setting(14, 'Remote', remote_status=['b', 'i'])
    def remote(self, c, remote_status):
        """
        Set remote mode of device.
        Arguments:
            remote_status   (bool)  : whether the device accepts serial commands
        Returns:
                            (bool)  : whether the device accepts serial commands
        """
        # ensure input has correct type/value
        if type(remote_status) is int:
            if remote_status not in (0, 1):
                raise Exception('Error: input must be a boolean, 0, or 1.')

        # setter
        if remote_status is not None:
            yield self.ser.acquire()
            yield self.ser.write('remote.w {:d}\r\n'.format(remote_status))
            yield self.ser.read_line('\n')
            self.ser.release()

        # # getter
        # yield self.ser.acquire()
        # yield self.ser.write('remote.r\r\n')
        # resp = yield self.ser.read_line('\n')
        # self.ser.release()
        #
        # # parse response
        # resp = resp.strip()
        # if resp == 'ON':
        #     resp = True
        # elif resp == 'OFF':
        #     resp = False
        # returnValue(resp)


    # ON/OFF
    @setting(111, 'Toggle', channel='i', power=['i','b'], returns='b')
    def toggle(self, c, channel, power=None):
        """
        Set a channel to be on or off.
        Arguments:
            channel (int)   : the channel to read/write. -1 does all channels
            power   (bool)  : whether channel is to be on or off
        Returns:
                    (bool)  : result
        """
        # ensure input is of correct type
        if (type(power) == int) and (power not in (0, 1)):
            raise Exception('Error: invalid input. Must be a boolean, 0, or 1.')

        # setter
        yield self.ser.acquire()
        if power is not None:
            yield self.ser.write('out.w {:d} {:d}\r\n'.format(channel, power))
        else:
            yield self.ser.write('out.r {:d}\r\n'.format(channel))

        # get response
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        resp = resp.strip()

        # parse response
        if resp == 'ON':
            resp = True
        elif resp == 'OFF':
            resp = False
        else:
            raise Exception('Error: bad readback from device.')

        # send signal to all other listeners
        self.toggle_update((channel, resp), self.getOtherListeners(c))
        returnValue(resp)

    @setting(121, 'Toggle All', power=['i', 'b'], returns=['', '*b'])
    def toggle_all(self, c, power=None):
        """
        Get/set power state of all channels.
        Arguments:
            power   (bool)  : whether channels are to be on or off.
        Returns:
                    (*bool) : power state of all channels.
        """
        # sanitize input
        if (type(power) is int) and (power not in (0, 1)):
            raise Exception('Error: invalid input. Must be a boolean, 0, or 1.')

        yield self.ser.acquire()

        # setter: power states (returns nothing)
        if power is not None:
            if power is True:
                yield self.ser.write('allon.w\r\n')
            elif power is False:
                yield self.ser.write('alloff.w\r\n')
            yield self.ser.read_line('\n')
            self.ser.release()
            return

        # getter: read power states (only if no setter)
        yield self.ser.write('out.r\r\n')
        yield wakeupCall(0.5)
        resp = yield self.ser.read()
        self.ser.release()

        # extract toggle state text for each channel
        resp = resp.strip().split('\r\n')
        resp = [val.split(': ')[1] for val in resp]
        # convert text to list of bools
        resp = [True if val == 'ON' else False for val in resp]
        returnValue(resp)


    # VOLTAGE
    @setting(211, 'Voltage', channel='i', voltage=['v', 'i'], returns='v')
    def voltage(self, c, channel=None, voltage=None):
        """
        Set the voltage of a channel.
        Arguments:
            channel (int)   : the channel to read/write.
            voltage (float) : the channel voltage to set.
        Returns:
                    (float) : the channel voltage.
        """
        # setter
        if voltage is not None:
            yield self.ser.acquire()
            yield self.ser.write('vout.w {:d} {:f}\r\n'.format(channel, voltage))
        # getter
        elif channel is not None:
            yield self.ser.acquire()
            yield self.ser.write('vout.r {:d}\r\n'.format(channel))
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        # parse response
        resp = float((resp.strip())[:-1])
        # send signal to all other listeners
        self.notifyOtherListeners(c, (channel, resp), self.voltage_update)
        returnValue(resp)

    @setting(212, 'Voltage Fast', channel='i', voltage=['v', 'i'], returns='v')
    def voltage_fast(self, c, channel, voltage):
        """
        Set the voltage of a channel quickly.
        Arguments:
            channel (int)   : the channel to read/write.
            voltage (float) : the channel voltage to set.
        Returns:
                    (float) : the channel voltage.
        """
        # quickly write and read response
        yield self.ser.acquire()
        yield self.ser.write('vf.w {:d} {:.1f}\r\n'.format(channel, voltage))
        resp = yield self.ser.read_line('\n')
        self.ser.release()

        # parse response
        resp = float((resp.strip())[:-1])

        # send signal to all other listeners
        # note: temporarily removed voltage updating for speed
        # self.voltage_update((channel, resp), self.getOtherListeners(c))
        returnValue(resp)

    @setting(213, 'Voltage Fast 2', channel='i', voltage=['v', 'i'], returns='')
    def voltage_fast_2(self, c, channel, voltage):
        """
        Set the voltage of a channel quickly - RDX.
        Arguments:
            channel (int)   : the channel to read/write.
            voltage (float) : the channel voltage to set.
        """
        # create voltage_fast message
        msg_voltagefast = b' '.join([
            b'x',
            bytes.fromhex('{:02x}'.format(channel)),
            bytes.fromhex('{:08x}'.format(round(voltage * 79.1026938)))
        ])

        # quickly write (no response reading)
        yield self.ser.acquire()
        yield self.ser.write(msg_voltagefast)
        self.ser.release()

        # send signal to all other listeners
        # note: temporarily removed voltage updating for speed
        # self.voltage_update((channel, resp), self.getOtherListeners(c))

    @setting(221, 'Voltage All', returns='*v')
    def voltage_all(self, c):
        """
        Get the voltages of all channels.
        Returns:
                    (*float) : voltages of all channels.
        """
        # getter: read voltages
        yield self.ser.acquire()
        yield self.ser.write('vout.r\r\n')
        yield wakeupCall(0.5)
        resp = yield self.ser.read()
        self.ser.release()

        # extract toggle state text for each channel
        resp = resp.strip().split('\r\n')
        resp = [val.split(': ')[1] for val in resp]
        # convert text to list of floats
        resp = [float(val[:-1]) for val in resp]
        returnValue(resp)


    # RAMP
    @setting(311, 'Ramp', channel='i', voltage=['v', 'i'], rate=['v', 'i'], returns='*s')
    def ramp(self, c, channel, voltage, rate):
        """
        Ramps the voltage of a channel at a given rate.
        Arguments:
            channel (int)   : the channel to read/write
            voltage (float) : the ramp endpoint (in Volts).
            rate    (float) : the rate to ramp at (in Volts/s)
        Returns:
                    (str)   : success string of ramp
        """
        # create message
        msg = 'ramp.w {:d} {:f} {:f}\r\n'.format(channel, voltage, rate)

        # send message to device and receive response
        yield self.ser.acquire()
        yield self.ser.write(msg)
        # add delay to allow messages to be completely read
        yield wakeupCall(0.2)
        resp = yield self.ser.read_line('\n')
        self.ser.release()
        resp = resp.strip().split(', ')
        # todo: process response
        returnValue(resp)

    @setting(312, 'Ramp Multiple', channels='*i', voltages=['*v', '*i'], rates=['*v', '*i'], returns='*s')
    def rampMultiple(self, c, channels, voltages, rates):
        """
        Simultaneously ramps the voltage of multiple channels.
        Arguments:
            channel (*int)  : the channels to read/write
            voltage (*float): the ramp endpoints (in Volts)
            rate    (*float): the rates to ramp at (in Volts/s)
        Returns:
                    (str)   : success strings of the ramps
        """
        # check parameters are specified for all channels
        if (len(channels) != len(voltages)) or (len(voltages) != len(rates)):
            raise Exception('Error: all parameters must be specified for all channels.')
        # reformat the input parameters
        param_list = zip(channels, voltages, rates)

        # send commands to device
        resp = []
        yield self.ser.acquire()
        for channel, voltage, rate in param_list:
            # create and write message
            msg = 'ramp.w {:d} {:f} {:f}\r\n'.format(channel, voltage, rate)
            yield self.ser.write(msg)
            # process response
            resp_tmp = yield self.ser.read_line('\n')
            resp.append(resp_tmp)
        self.ser.release()

        # todo: process response
        #resp_processing_func = lambda resp_tmp: resp_tmp.strip().split(': ')
        #resp = list((resp_processing_func, resp))
        #resp = [resp[0] for strings in resp]

        # send update signals to all other listeners
        # todo: make this use the response instead of arguments
        for channel, voltage, _ in param_list:
            self.notifyOtherListeners(c, (channel, voltage), self.voltage_update)
        returnValue(resp)


    # HELPERS
    @inlineCallbacks
    def _poll(self):
        # continually read device status in case of alarms
        yield self.inputs(None)


if __name__ == '__main__':
    from labrad import util
    util.runServer(DCServer())
