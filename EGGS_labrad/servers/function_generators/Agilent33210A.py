from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class Agilent33210AWrapper(GPIBDeviceWrapper):

    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def trigger(self):
        yield self.write('*TRG')

    @inlineCallbacks
    def toggle(self, status):
        # setter
        if status is not None:
            yield self.write('OUTP {:d}'.format(status))

        # getter
        resp = yield self.query('OUTP?')
        resp = bool(int(resp))
        returnValue(resp)

    def channel(self, chan_num):
        return 1

    # WAVEFORM
    @inlineCallbacks
    def function(self, shape):
        if shape:
            shape = shape.upper()
            if shape in ("SIN", "SQU", "RAMP", "PULS", "NOIS", "DC"):
                yield self.write('FUNC {:s}'.format(shape))
            else:
                raise Exception('Error: invalid input. Shape must be one of (SIN, SQU, RAMP, PULS, NOIS, DC).')

        resp = yield self.query('FUNC?')
        returnValue(resp)

    @inlineCallbacks
    def frequency(self, freq):
        # setter
        if freq:
            if (freq < 1e7) and (freq > 1e-3):
                yield self.write('FREQ {:f}'.format(freq))
            else:
                raise Exception('Error: invalid input. Frequency must be in range [1mHz, 10MHz].')

        # getter
        resp = yield self.query('FREQ?')
        returnValue(float(resp))

    @inlineCallbacks
    def amplitude(self, ampl):
        # setter
        if ampl:
            if (ampl <= 1e1) and (ampl >= 1e-2):
                yield self.write('VOLT {:f}'.format(ampl))
            else:
                raise Exception('Error: invalid input. Amplitude must be in range [1e-2 Vpp, 1e1 Vpp].')
        # getter
        resp = yield self.query('VOLT?')
        returnValue(float(resp))

    @inlineCallbacks
    def offset(self, off):
        # setter
        if off:
            if ((abs(off) < 1e1) and (abs(off) > 1e-2)) or (off == 0):
                yield self.write('VOLT:OFFS {:f}'.format(off))
            else:
                raise Exception('Error: invalid input. Amplitude offset must be in range [-1e1 Vpp, 1e1 Vpp].')
        # getter
        resp = yield self.query('VOLT:OFFS?')
        returnValue(float(resp))


    # TRIGGER
    @inlineCallbacks
    def triggerMode(self, mode):
        # setter
        if mode is not None:
            yield self.write('TRIG:SOUR {:s}'.format(mode))

        # getter
        resp = yield self.query('TRIG:SOUR?')
        returnValue(resp)

    @inlineCallbacks
    def triggerSlope(self, slope):
        # setter
        if slope is not None:
            yield self.write('TRIG:SLOP {:s}'.format(slope))

        # getter
        resp = yield self.query('TRIG:SLOP?')
        returnValue(resp)


    # MODES
    @inlineCallbacks
    def burst(self, status):
        # setter
        if status is not None:
            yield self.write('BURS:STAT {:d}'.format(status))

        # getter
        resp = yield self.query('BURS:STAT?')
        resp = bool(int(resp))
        returnValue(resp)

    @inlineCallbacks
    def burstMode(self, mode):
        # setter
        if mode is not None:
            yield self.write('BURS:MODE {:s}'.format(mode))

        # getter
        resp = yield self.query('BURS:MODE?')
        returnValue(resp)


    # SYNCHRONIZATION
    @inlineCallbacks
    def sync(self, status):
        # setter
        if status is not None:
            yield self.write('OUTP:SYNC {:d}'.format(status))

        # getter
        resp = yield self.query('OUTP:SYNC?')
        resp = bool(int(resp))
        returnValue(resp)
