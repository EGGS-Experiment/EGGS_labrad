"""
### BEGIN NODE INFO
[info]
name = Rigol DS1104 Oscilloscope
version = 0.9.1
description = Talks to the Rigol DS1104 Oscilloscope

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""


from labrad import types as T, util
from labrad.gpib import GPIBManagedServer, GPIBDeviceWrapper
from labrad.server import setting
from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.types import Value
from struct import unpack
from labrad.units import mV, ns

import time
import numpy, re

COUPLINGS = ['AC', 'DC', 'GND']
TRIG_CHANNELS = ['EXT','CHAN1','CHAN2','CHAN3','CHAN4','LINE']
VERT_DIVISIONS = 8.0
HORZ_DIVISIONS = 10.0
SCALES = []
PROBE_FACTORS = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]

class RigolDS1000ZWrapper(GPIBDeviceWrapper):
    pass

class RigolDS1000ZServer(GPIBManagedServer):
    name = 'Rigol DS1104Z Oscilloscope'
    #deviceName = 'Rigol DS1104Z Oscilloscope'
    deviceName = 'RIGOL TECHNOLOGIES,DS1104Z Plus,DS1ZC221401223,00.04.04.SP4'  # returned from *IDN?
    deviceWrapper = RigolDS1000ZWrapper

    #Base settings
    @setting(11, returns=[])
    def reset(self, c):
        dev = self.selectedDevice(c)
        yield dev.write('*RST')
        # TODO wait for reset to complete

    @setting(12, returns=[])
    def clear_buffers(self, c):
        dev = self.selectedDevice(c)
        yield dev.write('*CLS')

    #Channel settings: main
    @setting(100, channel = 'i', returns = '(vvvvsvss)')
    def channel_info(self, c, channel):
        """channel(int channel)
        Get information on one of the scope channels.
        OUTPUT
        Tuple of (probeAtten, termination, scale, position, coupling, bwLimit, invert, units)
        """
        dev = self.selectedDevice(c)
        resp = yield dev.query(':CHAN%d?' %channel)
        #example of resp:
        #a=':CHAN1:RANG +40.0E+00;OFFS +0.00000E+00;COUP DC;IMP ONEM;DISP 1;BWL 0;INV 0;LAB "1";UNIT VOLT;PROB +10E+00;PROB:SKEW +0.00E+00;STYP SING'
        vals=[]
        for part in resp.split(';'):
            vals.append( part.split(' ')[1] ) # the last part contains the numbers
        scale=vals[0]
        position=vals[1]
        coupling=vals[2]
        termination=vals[3]
        if termination=='ONEM':
            termination=1e6
        else:
            termination=50
        bwLimit=vals[5]
        invert=vals[6]
        unit=vals[8]
        probeAtten=vals[9]
        #Convert strings to numerical data when appropriate
        probeAtten = T.Value(float(probeAtten),'')
        termination = T.Value(float(termination),'')
        scale = T.Value(float(scale),'')
        position = T.Value(float(position),'')
        coupling = coupling
        bwLimit = T.Value(float(bwLimit),'')
        invert = invert
        returnValue((probeAtten,termination,scale,position,coupling,bwLimit,invert,unit))

    @setting(111, channel = 'i', coupling = 's', returns=['s'])
    def channel_coupling(self, c, channel, coupling = None):
        """
        Get/set the coupling of a specified channel
        Coupling can be "AC", "DC", or "GND"
        """
        chString = ':CHAN%d:COUP' %channel
        dev = self.selectedDevice(c)

        if coupling is None:
            resp = yield dev.query(chString + '?')
        else:
            coupling = coupling.upper()
            if coupling not in COUPLINGS:
                raise Exception('Coupling must be either: "AC", "DC", "GND"')
            else:
                yield dev.write(chString + ' ' + coupling)
                resp = yield dev.query(chString + '?')
        returnValue(resp)

    @setting(112, channel = 'i', scale = 'v', returns = ['v'])
    def channel_scale(self, c, channel, scale = None):
        """
        Get/set the vertical scale per div of a channel in Volts
        """
        dev = self.selectedDevice(c)
        chString = ':CHAN%d:SCAL' %channel

        if scale is None:
            resp = yield dev.query(chString + '?')
        else:
            scale = format(scale['V'],'E')
            yield dev.write(chString + str(scale) + 'V')
            resp = yield dev.query(':CHAN%d:SCAL?' %channel)

        scale = (Value(float(resp),'V'))
        returnValue(scale)

    @setting(113, channel = 'i', factor = 'i', returns = ['s'])
    def channel_probe(self, c, channel, factor = None):
        """
        Get/set the probe attenuation factor.
        """
        dev = self.selectedDevice(c)
        chString = ':CHAN%d:PROB' %channel

        if factor is None:
            resp = yield dev.query(chString + '?')
        elif factor in PROBE_FACTORS:
            yield dev.write(chString+':PROB%d' %factor)
            resp = yield dev.query(chString+':PROB?')
        else:
            raise Exception('Probe attenuation factor not in ' + str(PROBE_FACTORS))
        returnValue(resp)

    @setting(114, channel = 'i', state = 'i', returns = '')
    def channel_OnOff(self, c, channel, state = None):
        """
        Get/set whether channel display is on/off
        """
        dev = self.selectedDevice(c)
        chString = ':CHAN%d:DISP' %channel

        if state is None:
            resp = yield dev.query(chString + '?')
        elif state in [0, 1]:
            yield dev.write(chString + str(state))
        else:
            raise Exception('state must be either 0 or 1')
        returnValue(resp)

    @setting(115, channel = 'i', invert = 'i', returns = '')
    def channel_invert(self, c, channel, invert = None):
        """
        Get/set the inversion status of a channel
        """
        dev = self.selectedDevice(c)
        chString = ":CHAN:%d:INV" %channel

        if invert is None:
            resp = yield dev.query(chString + '?')
        elif invert in [0, 1]:
            yield dev.write(chString + str(invert))
        else:
            raise Exception('state must be either 0 (disable) or 1 (enable)')
        returnValue(invert)

    @setting(116, channel = 'i', position = 'v', returns = ['v'])
    def channel_offset_y(self, c, channel, position = None):
        """
        Get/set the vertical zero of a channel in divs - for Tektronix compatibility
        """
        dev = self.selectedDevice(c)
        resp = yield dev.query(':CHAN%d:SCAL?' %channel)
        scale_V = float(resp)

        if position is None:
            resp = yield dev.query(':CHAN%d:OFFS?' %channel)
        else:
            pos_V = - position * scale_V
            yield dev.write((':CHAN%d:OFFS %g V') % (channel, pos_V))
            resp = yield dev.query(':CHAN%d:OFFS?' % channel)
        position = float(resp) / scale_V
        returnValue(position)


    #trigger settings
    @setting(131, slope = 's', returns = ['s'])
    def trigger_slope(self, c, slope = None):
        """
        Turn on or off a scope channel display
        Must be 'RISE' or 'FALL'
        only edge triggering is implemented here
        """
        chString = ':TRIG:EDG:SLOP'
        dev = self.selectedDevice(c)

        if slope is None:
            resp = yield dev.query(chString + '?')
        else:
            slope = slope.upper()
            if slope not in ['RFAL', 'POS', 'NEG']:
                raise Exception('Slope must be either: "RFAL", "POS", "NEG" ')
            else:
                if slope == 'RFAL':
                    slope = 'POS'
                else:
                    slope = 'NEG'
                yield dev.write(chString + ' ' + slope)
                resp = yield dev.query(chString + '?')
        returnValue(resp)

    @setting(132, level = 'v', returns = ['v'])
    def trigger_level(self, c, level = None):
        """
        Get/set the vertical zero position of a channel in voltage
        """
        dev = self.selectedDevice(c)
        chString = ':TRIG:EDG:LEV'

        if level is None:
            resp = yield dev.query(chString + '?')
        else:
            yield dev.write(chString + ' ' + level)
            resp = yield dev.query(chString + '?')
        level = Value(float(resp), 'V')
        returnValue(level)

    @setting(133, channel = '?', returns = ['s'])
    def trigger_channel(self, c, channel = None):
        """
        Get/set the trigger source
        Must be one of "EXT","LINE", 1, 2, 3, 4, CHAN1, CHAN2...
        """
        dev = self.selectedDevice(c)

        if channel in ['CH1','CH2','CH3','CH4']:
            channel = int(channel[-1])
        if isinstance(channel, str):
            channel = channel.upper()
        if isinstance(channel, int):
            channel = 'CHAN%d' %channel

        if channel is None:
            resp = yield dev.query(':TRIG:EDG:SOUR?')
        elif channel in TRIG_CHANNELS:
            yield dev.write(':TRIG:EDG:SOUR '+channel)
            resp = yield dev.query(':TRIG:EDG:SOUR?')
        else:
            raise Exception('Select valid trigger channel')
        returnValue(resp)

    @setting(134, mode = 's', returns = ['s'])
    def trigger_mode(self, c, mode=None):
        """
        Get/set the trigger mode.
        Allowed values = AUTO, NONE, SING
        """
        dev = self.selectedDevice(c)
        chString = ':TRIG:SWE'

        if mode is None:
            resp = yield dev.query(chString + '?')
        elif mode in ['AUTO', 'NONE', 'SING']:
            resp = yield dev.write(chString + ' ' + mode)

        if mode == 'AUTO':
            yield dev.write(chString + ' ' + mode)
        elif mode == 'NORM':
            yield dev.write(':TRIG:SWE NORM')
        ans = yield dev.query(":TRIG:SWE?")
        returnValue(str(ans))


    #horizontal settings
    @setting(151, offset = 'v', returns = ['v'])
    def horiz_offset(self, c, offset = None):
        """
        Get/set the horizontal trigger offset in seconds
        """
        dev = self.selectedDevice(c)
        if offset is None:
            resp = yield dev.query(':TIM:OFFS?')
        else:
            yield dev.write(':TIM:OFFS %g' %pos)
            resp = yield dev.query(':TIM:OFFS?')
        offset = float(resp)
        returnValue(offset)

    @setting(152, scale = 'v', returns = ['v'])
    def horiz_scale(self, c, scale = None):
        """
        Get/set the horizontal scale value in s per div
        """
        dev = self.selectedDevice(c)
        chString = ':TIM:SCAL'

        if scale is None:
            resp = yield dev.query(chString + '?')
        else:
            yield dev.write(chString + ' ' + scale)
            resp = yield dev.query(chString + '?')
        scale = float(resp)
        returnValue(scale)


    #Data acquisition settings
    @setting(201, channel = 'i', returns='*v[ns] {time axis} *v[mV] {scope trace}')
    def get_trace(self, c, channel):
        """
        Get a trace from the scope.
        OUTPUT - (array voltage in volts, array time in seconds)
        removed start and stop: start = 'i', stop = 'i' (,start=1, stop=10000)
        """
        dev = self.selectedDevice(c)

        #set trace parameters
        yield dev.write(':WAV:SOUR CHAN%d' %channel)
        #trace mode (default normal since easiest right now)
        yield dev.write(':WAV:MODE NORM')
        #return format (default byte since easiest right now)
        yield dev.write(':WAV:FORM BYTE')

        #transfer waveform preamble
        preamble = yield dev.query(':WAV:PRE?')
        offset = yield dev.query(':TIM:OFFS?')

        #get waveform data
        data = yield dev.query(':WAV:DATA?')

        #parse waveform preamble
        points, xincrement, xorigin, xreference, yincrement, yorigin, yreference = _parsePreamble(preamble)

        #parse data
        trace = _parseByteData(data)

        #timeUnitScaler = 1 #Value(1, timeUnits)['s']
        voltUnitScaler = 1000.0 * mV
        timeUnitScaler = 1.0e9 * ns

        #convert data to volts
        traceVolts = (trace - yreference) * yincrement * voltUnitScaler
        timeAxis = (numpy.arange(points) * xincrement + xorigin) * timeUnitScaler
        returnValue((timeAxis, traceVolts))

    @setting(210)
    def measure_start(self, c):
        '''
        (re-)start measurement statistics
        (see measure)
        '''
        dev = self.selectedDevice(c)
        dev.write(":MEAS:STAT:RES")

    # @setting(211, count = 'i{count}', wait='v', returns='*(s{name} v{current} v{min} v{max} v{mean} v{std dev} v{count})')
    # def measure(self, c, count=0, wait=Value(0.5, 's')):
    #     '''
    #     returns the values from the measure function of the scope. if count >0, wait until
    #     scope has >= count stats before returning, waiting _wait_ time between calls.
    #
    #     Note that the measurement must be set manually on the scope for this to work.
    #     '''
    #     dev = self.selectedDevice(c)
    #
    #     #take all statistics
    #     yield dev.write(":MEAS:STAT ON")
    #
    #     def parse(s):
    #         s = s.split(',')
    #         d = []
    #         while s:
    #             d += [[s[0]] + [float(x) for x in s[1:7]]]
    #             s = s[7:]
    #         return d
    #
    #     d = []
    #     while True:
    #         d = yield dev.query(":MEAS:RES?")
    #         d = parse(d)
    #         counts = [x[-1] for x in d]
    #         if min(counts) >= count:
    #             break
    #         yield util.wakeupCall(wait['s'])
    #     returnValue(d)

def _parsePreamble(preamble):
    '''
    Check
    <preamble_block> ::= <format 16-bit NR1>,
                     <type 16-bit NR1>,
                     <points 32-bit NR1>,
                     <count 32-bit NR1>,
                     <xincrement 64-bit floating point NR3>,
                     <xorigin 64-bit floating point NR3>,
                     <xreference 32-bit NR1>,
                     <yincrement 32-bit floating point NR3>,
                     <yorigin 32-bit floating point NR3>,
                     <yreference 32-bit NR1>
    '''
    fields = preamble.split(',')
    points = int(fields[2])
    xincrement = float(fields[4])
    xorigin = float(fields[5])
    xreference = int(fields[6])
    yincrement = float(fields[7])
    yorigin = float(fields[8])
    yreference = int(fields[9])
    return (points, xincrement, xorigin, xreference, yincrement, yorigin, yreference)

def _parseByteData(data):
    """
    Parse byte data
    """
    #get tmc header in #NXXXXXXXXX format
    tmc_N = data[1]
    tmc_length = data[2: 2 + tmc_N]

    return data[2 + tmc_N:2 + tmc_N + tmc_length]

__server__ = RigolDS1000ZServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)