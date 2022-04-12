import pyvisa as visa
import numpy as np
from labrad.server import setting
from labrad.gpib import GPIBDeviceWrapper
from labrad.errors import DeviceNotSelectedError
from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.servers import PollingServer

KNOWN_DEVICE_TYPES = ('GPIB', 'TCPIP', 'USB')


class GPIBBusServer(PollingServer):
    """
    Provides direct access to GPIB-enabled devices.
    """

    def refreshDevices(self):
        """
        Refresh the list of known devices on this bus.
        Currently supported are GPIB devices and GPIB over USB.
        """
        try:
            rm = visa.ResourceManager()
            addresses = [str(x) for x in rm.list_resources()]
            additions = set(addresses) - set(self.devices.keys())
            deletions = set(self.devices.keys()) - set(addresses)
            for addr in additions:
                try:
                    if not addr.startswith(KNOWN_DEVICE_TYPES):
                        continue
                    instr = rm.open_resource(addr)
                    instr.write_termination = ''
                    instr.clear()
                    if addr.endswith('SOCKET'):
                        instr.write_termination = '\n'
                    self.devices[addr] = instr
                    self.sendDeviceMessage('GPIB Device Connect', addr)
                except Exception as e:
                    print('Failed to add ' + addr + ':' + str(e))
                    raise
            for addr in deletions:
                del self.devices[addr]
                self.sendDeviceMessage('GPIB Device Disconnect', addr)
        except Exception as e:
            print('Problem while refreshing devices:', str(e))

    def sendDeviceMessage(self, msg, addr):
        print(msg + ': ' + addr)
        self.client.manager.send_named_message(msg, (self.name, addr))

    def initContext(self, c):
        c['timeout'] = self.defaultTimeout

    def getDevice(self, c):
        if 'addr' not in c:
            raise DeviceNotSelectedError("No GPIB address selected.")
        if c['addr'] not in self.devices:
            raise Exception('Could not find device ' + c['addr'])
        instr = self.devices[c['addr']]
        return instr

    @setting(0, addr='s', returns='s')
    def address(self, c, addr=None):
        """
        Get or set the GPIB address for this context.

        To get the addresses of available devices,
        use the list_devices function.
        """
        if addr is not None:
            c['addr'] = addr
        return c['addr']

    @setting(2, time='v[s]', returns='v[s]')
    def timeout(self, c, time=None):
        """Get or set the GPIB timeout."""
        if time is not None:
            c['timeout'] = time
        return c['timeout']

    @setting(3, data='s', returns='')
    def write(self, c, data):
        """Write a string to the GPIB bus."""
        self.getDevice(c).write(data)

    @setting(8, data='y', returns='')
    def write_raw(self, c, data):
        """Write a string to the GPIB bus."""
        self.getDevice(c).write_raw(data)

    @setting(4, n_bytes='w', returns='s')
    def read(self, c, n_bytes=None):
        """
        Read from the GPIB bus.

        Termination characters, if any, will be stripped.
        This includes any bytes corresponding to termination in
        binary data. If specified, reads only the given number
        of bytes. Otherwise, reads until the device stops sending.
        """
        instr = self.getDevice(c)
        if n_bytes is None:
            ans = instr.read_raw()
        else:
            ans = instr.read_raw(n_bytes)
        ans = ans.strip().decode()
        return ans

    @setting(5, data='s', returns='s')
    def query(self, c, data):
        """
        Make a GPIB query, a write followed by a read.

        This query is atomic.  No other communication to the
        device will occur while the query is in progress.
        """
        instr = self.getDevice(c)
        instr.write(data)
        ans = instr.read_raw()
        # convert from bytes to string for python 3
        ans = ans.strip().decode()
        return ans

    @setting(7, n_bytes='w', returns='y')
    def read_raw(self, c, n_bytes=None):
        """Read raw bytes from the GPIB bus.

        Termination characters, if any, will not be stripped.
        If n_bytes is specified, reads only that many bytes.
        Otherwise, reads until the device stops sending.
        """
        instr = self.getDevice(c)
        if n_bytes is None:
            ans = instr.read_raw()
        else:
            ans = instr.read_raw(n_bytes)
        return bytes(ans)


class TektronixMSO2000(GPIBDeviceWrapper):

    # SYSTEM
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self):
        yield self.write('*CLS')

    # CHANNEL
    @inlineCallbacks
    def channel_info(self, channel):
        onoff = yield self.channel_toggle(channel)
        probeAtten = yield self.channel_probe(channel)
        scale = yield self.channel_scale(channel)
        offset = yield self.channel_offset(channel)
        coupling = yield self.channel_coupling(channel)
        invert = yield self.channel_invert(channel)
        returnValue((onoff, probeAtten, scale, offset, coupling, invert))

    @inlineCallbacks
    def channel_coupling(self, channel, coupling=None):
        chString = 'CH{:d}:COUP'.format(channel)
        if coupling is not None:
            coupling = coupling.upper()
            if coupling in ('AC', 'DC', 'GND'):
                yield self.write(chString + ' ' + coupling)
            else:
                raise Exception('Coupling must be one of: ' + str(('AC', 'DC', 'GND')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def channel_scale(self, channel, scale=None):
        chString = 'CH{:d}:SCA'.format(channel)
        if scale is not None:
            if (scale > 1e-3) and (scale < 1e1):
                yield self.write(chString + ' ' + str(scale))
            else:
                raise Exception('Scale must be in range: [1e-3, 1e1]')
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def channel_probe(self, channel, atten=None):
        chString = 'CH{:d}:PRO:GAIN'.format(channel)
        if atten is not None:
            if atten in (0.1, 1, 10):
                yield self.write(chString + ' ' + str(1 / atten))
            else:
                raise Exception('Probe attenuation must be one of: ' + str((0.1, 1, 10)))
        resp = yield self.query(chString + '?')
        returnValue(1 / float(resp))

    @inlineCallbacks
    def channel_toggle(self, channel, state=None):
        chString = 'SEL:CH{:d}'.format(channel)
        if state is not None:
            yield self.write(chString + ' ' + str(int(state)))
        resp = yield self.query(chString + '?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def channel_invert(self, channel, invert=None):
        chString = 'CH{:d}:INV'.format(channel)
        if invert is not None:
            yield self.write(chString + ' ' + str(int(invert)))
        resp = yield self.query(chString + '?')
        returnValue(bool(int(resp)))

    @inlineCallbacks
    def channel_offset(self, channel, offset=None):
        # value is in volts
        chString = 'CH{:d}:OFFS'.format(channel)
        if offset is not None:
            if (offset == 0) or ((offset > 1e-4) and (offset < 1e1)):
                yield self.write(chString + ' ' + str(offset))
            else:
                raise Exception('Scale must be in range: [1e-3, 1e1]')
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    # TRIGGER
    @inlineCallbacks
    def trigger_channel(self, channel=None):
        # note: target channel must be on
        chString = 'TRIG:A:EDGE:SOU'
        if channel is not None:
            if channel in (1, 2, 3, 4):
                yield self.write(chString + ' CH' + str(channel))
            else:
                raise Exception('Trigger channel must be one of: ' + str((1, 2, 3, 4)))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def trigger_slope(self, slope=None):
        print('yzde')
        chString = 'TRIG:A:EDGE:SLOP'
        if slope is not None:
            slope = slope.upper()
            if slope in ('RIS', 'FALL'):
                yield self.write(chString + ' ' + slope)
            else:
                raise Exception('Slope must be one of: ' + str(('RIS', 'FALL')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    @inlineCallbacks
    def trigger_level(self, channel, level=None):
        if channel not in (1, 2, 3, 4):
            raise Exception('Channel must be one of: ' + str((1, 2, 3, 4)))
        chString = 'TRIG:A:LEV:CH{:d}'.format(channel)
        if level is not None:
            vscale_tmp = yield self.channel_scale(channel)
            level_max = 5 * vscale_tmp
            if (level == 0) or (abs(level) <= level_max):
                yield self.write(chString + ' ' + str(level))
            else:
                raise Exception('Trigger level must be in range: ' + str((-level_max, level_max)))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def trigger_mode(self, mode=None):
        chString = 'TRIG:A:MOD'
        if mode is not None:
            if mode in ('AUTO', 'NORM'):
                yield self.write(chString + ' ' + mode)
            else:
                raise Exception('Trigger mode must be one of: ' + str(('AUTO', 'NORM')))
        resp = yield self.query(chString + '?')
        returnValue(resp.strip())

    # HORIZONTAL
    @inlineCallbacks
    def horizontal_offset(self, offset=None):
        chString = 'HOR:DEL:TIM'
        if offset is not None:
            if (offset == 0) or ((abs(offset) > 1e-6) and (abs(offset) < 1e0)):
                yield self.write(chString + ' ' + str(offset))
            else:
                raise Exception('Horizontal offset must be in range: ' + str('(1e-6, 1e0)'))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    @inlineCallbacks
    def horizontal_scale(self, scale=None):
        chString = 'HOR:SCA'
        if scale is not None:
            if (scale > 1e-6) and (scale < 50):
                yield self.write(chString + ' ' + str(scale))
            else:
                raise Exception('Horizontal scale must be in range: ' + str('(1e-6, 50)'))
        resp = yield self.query(chString + '?')
        returnValue(float(resp))

    # ACQUISITION
    @inlineCallbacks
    def get_trace(self, channel, points=None):
        # configure trace
        yield self.write('DAT:SOUR CH%d' % channel)
        yield self.write('DAT:STAR 1')
        yield self.write('DAT:ENC ASCI')
        yield self.write('DAT:STOP {:d}'.format(points))

        # get preamble
        preamble = yield self.query('WFMO?')
        # get waveform
        data = yield self.query('CURV?')
        # parse waveform preamble
        points, xincrement, xorigin, yincrement, yorigin, yreference = self._parsePreamble(preamble)
        # parse data
        trace = self._parseByteData(data)
        # format data
        xAxis = np.arange(points) * xincrement + xorigin
        yAxis = (trace - yorigin) * yincrement + yreference
        returnValue((xAxis, yAxis))

    # MEASURE
    @inlineCallbacks
    def measure_start(self, c):
        # (re-)start measurement statistics
        self.write('MEAS:STAT:RES')

    # HELPER
    def _parsePreamble(preamble):
        '''
        <preamble_block> ::= <format 16-bit NR1>,
                         <type 16-bit NR1>,
                         <points 32-bit NR1>,
                         <count 32-bit NR1>,
                         <xorigin 64-bit floating point NR3>,
                         <xreference 32-bit NR1>,
                         <yincrement 32-bit floating point NR3>,
                         <yorigin 32-bit floating point NR3>,
        '''
        fields = preamble.split(';')
        points = int(fields[6])
        xincrement, xorigin, xreference = list(map(float, fields[9: 12]))
        yincrement, yorigin, yreference = list(map(float, fields[13: 16]))
        return (points, xincrement, xorigin, yincrement, yorigin, yreference)

    def _parseByteData(data):
        """
        Parse byte data
        """
        trace = np.array(data.split(','), dtype=float)
        return trace
