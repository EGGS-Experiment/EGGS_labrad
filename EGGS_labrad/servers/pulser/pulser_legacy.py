#labrad and artiq imports
from labrad.server import LabradServer, setting, Signal
from labrad.units import WithUnit
from sequence import Sequence

#function imports
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
import numpy as np


class Pulser_legacy(LabradServer):

    """Contains legacy functionality for Pulser"""

    def initServer(self):
        #device storage
            #DDSs
        for name, channel in self.ddsDict.items():
            channel.name = name
            freq, ampl, phase = (channel.frequency, channel.amplitude, channel.phase)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
            yield self.inCommunication.run(self._setDDSParam, channel, freq, ampl, phase)

        #Remote channels
        self.remoteChannels = hardwareConfiguration.remoteChannels
        yield self.initializeRemote()

    @inlineCallbacks
    def initializeRemote(self):
        self.remoteConnections = {}
        if len(self.remoteChannels):
            from labrad.wrappers import connectAsync
            for name, rc in self.remoteChannels.items():
                try:
                    self.remoteConnections[name] = yield connectAsync(rc.ip)
                    print('Connected to {}'.format(name))
                except:
                    print('Not Able to connect to {}'.format(name))
                    self.remoteConnections[name] = None

    @setting(117, 'Get State', channel_name = 's', returns = '(bbbb)')
    def getState(self, c, channel_name):
        """
        Returns the current state of the TTL: in the form (Manual/Auto, ManualOn/Off, ManualInversionOn/Off, AutoInversionOn/Off)
        """
        if channel_name not in self.ttlDict.keys():
            raise Exception("Incorrect Channel")
        channel = self.ttlDict[channel_name]
        answer = (channel.ismanual, channel.manualstate, channel.manualinv, channel.autoinv)
        return answer

    #DDS functions
    @setting(123, 'Get DDS Amplitude Range', name = 's', returns = '(vv)')
    def getDDSAmplRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedamplrange

    @setting(124, 'Get DDS Frequency Range', name = 's', returns = '(vv)')
    def getDDSFreqRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedfreqrange

    #Backwards compatibility
    @inlineCallbacks
    def _setDDSRemote(self, channel, addr, buf):
        cxn = self.remoteConnections[channel.remote]
        remote_info = self.remoteChannels[channel.remote]
        server, reset, program = remote_info.server, remote_info.reset, remote_info.program
        try:
            yield cxn.servers[server][reset]()
            yield cxn.servers[server][program]([(channel.channelnumber, buf)])
        except (KeyError, AttributeError):
            print('Not programming remote channel {}'.format(channel.remote))
