from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class RigolDG2052Wrapper(GPIBDeviceWrapper):

    # INITIALIZE
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_num = 1


    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def trigger(self):
        yield self.write(':TRIG{:d}'.format(self.channel_num))

    @inlineCallbacks
    def toggle(self, status):
        # setter
        if status is not None:
            yield self.write(':OUTP{:d} {:d}'.format(self.channel_num, status))

        # getter
        resp = yield self.query(':OUTP{:d}?'.format(self.channel_num))
        resp = resp.strip().upper()
        if resp == 'ON':
            returnValue(True)
        elif resp == 'OFF':
            returnValue(False)
        else:
            raise Exception("Error: invalid device response: {}".format(resp))

    def channel(self, chan_num):
        # setter
        if chan_num is not None:
            # check input
            if chan_num not in (1, 2):
                raise Exception('Error: invalid input. Channel must be one of (1, 2).')
            else:
                self.channel_num = chan_num

        # getter
        return self.channel_num


    # WAVEFORM
    @inlineCallbacks
    def function(self, shape):
        # setter
        if shape:
            shape = shape.upper()
            if shape in ("SIN", "SQU", "RAMP", "PULS", "NOIS", "DC"):
                yield self.write(':SOUR{:d}:FUNC {:s}'.format(self.channel_num, shape))
            else:
                raise Exception('Error: invalid input. Shape must be one of (SIN, SQU, RAMP, PULS, NOIS, DC).')

        # getter
        resp = yield self.query(':SOUR{:d}:FUNC?'.format(self.channel_num))
        resp = resp.strip().upper()
        returnValue(resp)

    @inlineCallbacks
    def frequency(self, freq):
        # setter
        if freq:
            if (freq <= 5e7) and (freq >= 1e-6):
                yield self.write(':SOUR{:d}:FREQ {:f}'.format(self.channel_num, freq))
            else:
                raise Exception('Error: invalid input. Frequency must be in range [1uHz, 50MHz].')

        # getter
        resp = yield self.query(':SOUR{:d}:FREQ?'.format(self.channel_num))
        returnValue(float(resp))

    @inlineCallbacks
    def amplitude(self, ampl):
        # setter
        if ampl:
            if (ampl <= 2e1) and (ampl >= 2e-3):
                yield self.write(':SOUR{:d}:VOLT {:f}'.format(self.channel_num, ampl))
            else:
                raise Exception('Error: invalid input. Amplitude must be in range [2mVpp, 20Vpp].')

        # getter
        resp = yield self.query(':SOUR{:d}:VOLT?'.format(self.channel_num))
        returnValue(float(resp))

    @inlineCallbacks
    def offset(self, off):
        # setter
        if off:
            if (abs(off) < 2e1) and (abs(off) > 1e-6):
                yield self.write(':SOUR{:d}:VOLT:OFFS {:f}'.format(self.channel_num, off))
            else:
                raise Exception('Error: invalid input. Amplitude offset must be in range [-1e1 Vpp, 1e1 Vpp].')

        # getter
        resp = yield self.query(':SOUR{:d}:VOLT:OFFS?'.format(self.channel_num))
        returnValue(float(resp))


    # TRIGGER
    @inlineCallbacks
    def triggerMode(self, mode):
        # setter
        if mode is not None:
            yield self.write(':TRIG{:d}:SOUR {:s}'.format(self.channel_num, mode))

        # getter
        resp = yield self.query(':TRIG{:d}:SOUR?'.format(self.channel_num))
        returnValue(resp)

    @inlineCallbacks
    def triggerSlope(self, slope):
        # setter
        if slope is not None:
            yield self.write(':TRIG{:d}:SLOP {:s}'.format(self.channel_num, slope))

        # getter
        resp = yield self.query(':TRIG{:d}:SLOP?'.format(self.channel_num))
        returnValue(resp)


    # MODES
    @inlineCallbacks
    def burst(self, status):
        # setter
        if status is not None:
            yield self.write(':SOUR{:d}:BURS {:d}'.format(self.channel_num, status))

        # getter
        resp = yield self.query(':SOUR{:d}:BURS?'.format(self.channel_num))
        resp = resp.strip().upper()
        if resp == 'ON':
            returnValue(True)
        elif resp == 'OFF':
            returnValue(False)
        else:
            raise Exception("Error: invalid device response: {}".format(resp))

    @inlineCallbacks
    def burstMode(self, mode):
        # setter
        if mode is not None:
            yield self.write(':SOUR{:d}:BURS:MODE {:s}'.format(self.channel_num, mode))
        ':SOUR{:d}:BURS {:d}'.format(1, True)
        # getter
        resp = yield self.query(':SOUR{:d}:BURS:MODE?'.format(self.channel_num))
        returnValue(resp)


    # SYNCHRONIZATION
    @inlineCallbacks
    def sync(self, status):
        # setter
        if status is not None:
            yield self.write(':OUTP{:d}:SYNC {:d}'.format(self.channel_num, status))

        # getter
        resp = yield self.query(':OUTP{:d}:SYNC?'.format(self.channel_num))
        resp = resp.strip().upper()
        if resp == 'ON':
            returnValue(True)
        elif resp == 'OFF':
            returnValue(False)
        else:
            raise Exception("Error: invalid device response: {}".format(resp))
