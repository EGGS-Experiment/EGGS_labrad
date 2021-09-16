from labrad import types as T, util
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.types import Value
from labrad.units import mV, ns

import numpy as np

CHANNELS = ['A', 'B', 'C', 'D', '0']

class Lakeshore336Wrapper(GPIBDeviceWrapper):

    #SYSTEM
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self,):
        yield self.write('*CLS')


    #READ TEMPERATURE
    @inlineCallbacks
    def read_temperature(self, channel = None):
        if channel not in CHANNELS:
            raise Exception('Channel must be one of: ' + str(CHANNELS))
        resp = yield self.query('KRDG? %d' % channel)
        resp = np.array(resp.split(','))
        returnValue(resp)