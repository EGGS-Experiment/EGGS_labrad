from labrad import types as T, util
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.types import Value
from labrad.units import mV, ns

import time
import numpy, re

COUPLINGS = ['AC', 'DC', 'GND']
TRIG_CHANNELS = ['EXT','CHAN1','CHAN2','CHAN3','CHAN4','LINE']
VERT_DIVISIONS = 8.0
HORZ_DIVISIONS = 10.0
SCALES = []
PROBE_FACTORS = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
TRIGGER_MODES = ['AUTO', 'NONE', 'SING']

class RigolDS1000ZWrapper(GPIBDeviceWrapper):

    #system
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')
        # TODO wait for reset to complete

    @inlineCallbacks
    def clear_buffers(self):
        yield self.write('*CLS')

    #channel
    @inlineCallbacks
    def channel_info(self, channel):
        #returns a tuple of (probeAtten, termination, scale, position, coupling, bwLimit, invert, units)
        resp = yield self.query(':CHAN%d?' %channel)
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

    @inlineCallbacks
    def channel_coupling(self, channel, coupling = None):
        chString = ':CHAN%d:COUP' %channel
        if coupling is not None:
            coupling = coupling.upper()
            if coupling not in COUPLINGS:
                raise Exception('Coupling must be either: ' + str(COUPLINGS))
            else:
                yield self.write(chString + ' ' + coupling)
        resp = yield self.query(chString + '?')
        returnValue(resp)

    @inlineCallbacks
    def channel_scale(self, channel, scale = None):
        #value is in volts
        chString = ':CHAN%d:SCAL' %channel
        if scale is not None:
            scale = format(scale['V'],'E')
            yield self.write(chString + ' ' + str(scale) + 'V')
            resp = yield self.query(':CHAN%d:SCAL?' %channel)
        resp = yield self.query(chString + '?')
        scale = (Value(float(resp),'V'))
        returnValue(scale)

    @inlineCallbacks
    def channel_probe(self, channel, factor = None):
        chString = ':CHAN%d:PROB' %channel
        if factor in PROBE_FACTORS:
            yield self.write(chString + ' ' + str(factor))
        elif factor is not None:
            raise Exception('Probe attenuation factor not in ' + str(PROBE_FACTORS))
        resp = yield self.query(chString + '?')
        returnValue(resp)

    @inlineCallbacks
    def channel_onoff(self, channel, state = None):
        chString = ':CHAN%d:DISP' %channel
        if state in [0, 1]:
            yield self.write(chString + ' ' + str(state))
        elif state is not None:
            raise Exception('state must be either 0 or 1')
        resp = yield self.query(chString + '?')
        returnValue(bool(resp))

    @inlineCallbacks
    def channel_invert(self, channel, invert = None):
        chString = ":CHAN:%d:INV" %channel
        if invert in [0, 1]:
            yield self.write(chString + ' ' + str(invert))
        elif invert is not None:
            raise Exception('state must be either 0 (disable) or 1 (enable)')
        resp = yield self.query(chString + '?')
        returnValue(bool(resp))

    @inlineCallbacks
    def channel_offset(self, channel, position = None):
        #value is in divs
        resp = yield self.query(':CHAN%d:SCAL?' %channel)
        scale_V = float(resp)
        if position is not None:
            pos_V = - position * scale_V
            yield self.write((':CHAN%d:OFFS %g') % (channel, pos_V))
        resp = yield self.query(':CHAN%d:OFFS?' % channel)
        position = float(resp) / scale_V
        returnValue(position)


    #trigger settings
    @inlineCallbacks
    def trigger_channel(self, channel = None):
        #trigger source must be one of "EXT","LINE", 1, 2, 3, 4, CHAN1, CHAN2...
        if channel in TRIG_CHANNELS:
            channel = int(channel[-1])
            if isinstance(channel, str):
                channel = channel.upper()
            if isinstance(channel, int):
                channel = 'CHAN%d' %channel
            yield self.write(':TRIG:EDG:SOUR '+ str(channel)) # ***
        else:
            raise Exception('Select valid trigger channel')
        resp = yield self.query(':TRIG:EDG:SOUR?')
        returnValue(resp)

    @inlineCallbacks
    def trigger_slope(self, slope = None):
        #trigger can only be 'RFAL', 'POS', 'NEG'; only edge triggering is implemented here
        chString = ':TRIG:EDG:SLOP'
        if slope is not None:
            slope = slope.upper()
            if slope not in ['RFAL', 'POS', 'NEG']:
                raise Exception('Slope must be either: "RFAL", "POS", "NEG" ')
            else:
                if slope == 'RFAL':
                    slope = 'POS'
                else:
                    slope = 'NEG'
                yield self.write(chString + ' ' + slope)
        resp = yield self.query(chString + '?')
        returnValue(resp)

    @inlineCallbacks
    def trigger_level(self, level = None):
        #Get/set the vertical zero position of a channel in voltage
        chString = ':TRIG:EDG:LEV'
        if level is not None:
            yield self.write(chString + ' ' + str(level))
        resp = yield self.query(chString + '?')
        level = Value(float(resp), 'V')
        returnValue(level)

    @inlineCallbacks
    def trigger_mode(self, mode=None):
        chString = ':TRIG:SWE'
        if mode in TRIGGER_MODES:
            yield self.write(chString + ' ' + mode)
        elif mode is not None:
            raise Exception('Select valid trigger mode')
        resp = yield self.query(":TRIG:SWE?")
        returnValue(resp)


    #horizontal settings
    @inlineCallbacks
    def horiz_offset(self, offset = None):
        #Get/set the horizontal trigger offset in seconds
        chString = ':TIM:OFFS'
        if offset is not None:
            yield self.write(chString + ' ' + offset)
        resp = yield self.query(chstring + '?')
        offset = float(resp)
        returnValue(offset)

    @inlineCallbacks
    def horiz_scale(self, scale = None):
        #Get/set the horizontal scale value in s per div
        chString = ':TIM:SCAL'
        if scale is not None:
            yield self.write(chString + ' ' + scale)
        resp = yield self.query(chString + '?')
        scale = float(resp)
        returnValue(scale)


    #data acquisition settings
    @inlineCallbacks
    def get_trace(self, channel):
        #returns (array voltage in volts, array time in seconds)
        #removed start and stop: start = 'i', stop = 'i' (,start=1, stop=10000)

        #set trace parameters
        yield self.write(':WAV:SOUR CHAN%d' %channel)
        #trace mode (default normal since easiest right now)
        yield self.write(':WAV:MODE NORM')
        #return format (default byte since easiest right now)
        yield self.write(':WAV:FORM BYTE')

        #transfer waveform preamble
        preamble = yield self.query(':WAV:PRE?')
        offset = yield self.query(':TIM:OFFS?')

        #get waveform data
        data = yield self.query(':WAV:DATA?')

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

    @inlineCallbacks
    def measure_start(self, c):
        #(re-)start measurement statistics
        self.write(":MEAS:STAT:RES")

    # @setting(211, count = 'i{count}', wait='v', returns='*(s{name} v{current} v{min} v{max} v{mean} v{std dev} v{count})')
    # def measure(self, count=0, wait=Value(0.5, 's')):
    #     '''
    #     returns the values from the measure function of the scope. if count >0, wait until
    #     scope has >= count stats before returning, waiting _wait_ time between calls.
    #
    #     Note that the measurement must be set manually on the scope for this to work.
    #     '''
    #     dev = self.selectedDevice(c)
    #
    #     #take all statistics
    #     yield self.write(":MEAS:STAT ON")
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
    #         d = yield self.query(":MEAS:RES?")
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