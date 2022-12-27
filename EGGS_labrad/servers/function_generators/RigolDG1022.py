from time import sleep
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue

_RIGOL_DG1022_QUERY_DELAY = 0.1


class RigolDG1022Wrapper(GPIBDeviceWrapper):

    # INITIALIZE
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.channel_num = 1
        self.channel_string = ''


    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    def trigger(self):
        raise NotImplementedError

    @inlineCallbacks
    def toggle(self, status):
        # setter
        if status is not None:
            if status is True:
                yield self.write('OUTP{} ON'.format(self.channel_string))
            else:
                yield self.write('OUTP{} OFF'.format(self.channel_string))

        # getter
        sleep(_RIGOL_DG1022_QUERY_DELAY)
        resp = yield self.query('OUTP{}?'.format(self.channel_string))
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

            # set channel string
            if chan_num == 1:
                self.channel_string = ''
            else:
                self.channel_string = ':CH2'

            # set value
            self.channel_num = chan_num

        # getter
        return self.channel_num

    @inlineCallbacks
    def sync(self, status):
        # setter
        if status is not None:
            if status is True:
                yield self.write('OUTP:SYNC ON')
            else:
                yield self.write('OUTP:SYNC OFF')

        # getter
        sleep(_RIGOL_DG1022_QUERY_DELAY)
        resp = yield self.query('OUTP:SYNC?')
        resp = resp.split(' ')[-1].strip()
        if resp == 'ON':
            returnValue(True)
        elif resp == 'OFF':
            returnValue(True)
        else:
            raise Exception("Error: invalid device response: {}".format(resp))


    # WAVEFORM
    @inlineCallbacks
    def function(self, shape):
        # setter
        if shape:
            shape = shape.upper()
            if shape in ("SIN", "SQU", "RAMP", "PULS", "NOIS", "DC"):
                yield self.write('FUNC{} {:s}'.format(self.channel_string, shape))
            else:
                raise Exception('Error: invalid input. Shape must be one of (SIN, SQU, RAMP, PULS, NOIS, DC).')

        # getter
        sleep(_RIGOL_DG1022_QUERY_DELAY)
        resp = yield self.query('FUNC{}?'.format(self.channel_string))
        resp = resp.split(':')[-1].strip()
        returnValue(resp)

    @inlineCallbacks
    def frequency(self, freq):
        # setter
        if freq:
            if (freq < 2e7) and (freq > 1e-3):
                yield self.write('FREQ{} {:f}'.format(self.channel_string, freq))
            else:
                raise Exception('Error: invalid input. Frequency must be in range [1mHz, 20MHz].')

        # getter
        sleep(_RIGOL_DG1022_QUERY_DELAY)
        resp = yield self.query('FREQ{}?'.format(self.channel_string))
        resp = resp.split(':')[-1].strip()
        returnValue(float(resp))

    @inlineCallbacks
    def amplitude(self, ampl):
        # setter
        if ampl:
            if (ampl < 1e1) and (ampl > 1e-2):
                yield self.write('VOLT{} {:f}'.format(self.channel_string, ampl))
            else:
                raise Exception('Error: invalid input. Amplitude must be in range [1e-2 Vpp, 1e1 Vpp].')

        # getter
        sleep(_RIGOL_DG1022_QUERY_DELAY)
        resp = yield self.query('VOLT{}?'.format(self.channel_string))
        resp = resp.split(':')[-1].strip()
        returnValue(float(resp))

    @inlineCallbacks
    def offset(self, off):
        # setter
        if off:
            if (off < 1e1) and (off > 1e-2):
                yield self.write('VOLT:OFFS{} {:f}'.format(self.channel_string, off))
            else:
                raise Exception('Error: invalid input. Amplitude offset must be in range [-1e1 Vpp, 1e1 Vpp].')

        # getter
        sleep(_RIGOL_DG1022_QUERY_DELAY)
        resp = yield self.query('VOLT:OFFS{}?'.format(self.channel_string))
        returnValue(float(resp))


    # MODULATION
    # todo

    # SWEEP
    # todo
