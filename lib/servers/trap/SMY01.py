from labrad import types as T, util
from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.types import Value
from labrad.units import mV, ns

import numpy as np

class SMY01Wrapper(GPIBDeviceWrapper):

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
