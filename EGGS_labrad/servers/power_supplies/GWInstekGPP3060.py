from labrad.gpib import GPIBDeviceWrapper
from twisted.internet.defer import inlineCallbacks, returnValue


class GWInstekGPP3060(GPIBDeviceWrapper):

    # GENERAL
    @inlineCallbacks
    def reset(self):
        yield self.write('*RST')

    @inlineCallbacks
    def clear_buffers(self, c):
        yield self.write('*CLS')

    @inlineCallbacks
    def remote(self, c, status=None):
        pass


    # CHANNEL OUTPUT
    @inlineCallbacks
    def channelToggle(self, c, channel, status=None):
        pass

    @inlineCallbacks
    def channelMode(self, c, channel, mode=None):
        pass

    @inlineCallbacks
    def channelVoltage(self, c, channel, voltage=None):
        pass

    @inlineCallbacks
    def channelCurrent(self, c, channel, current=None):
        pass


    # MEASURE
    @inlineCallbacks
    def measureVoltage(self, c, channel):
        pass

    @inlineCallbacks
    def measureCurrent(self, c, channel):
        pass
