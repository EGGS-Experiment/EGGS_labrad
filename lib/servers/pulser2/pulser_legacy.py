#labrad and artiq imports
from labrad.server import LabradServer, setting, Signal
#from pulser_artiq_DDS import DDS_artiq
#from pulser_artiq_linetrigger import LineTrigger_artiq

#async imports
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread

#wrapper imports
from sequence import Sequence

#function imports
import numpy as np

class Pulser_legacy(LabradServer):

    """Contains legacy functionality for Pulser"""

    onSwitch = Signal(611051, 'signal: switch toggled', '(ss)')

    def __init__(self):
        LabradServer.__init__(self)

    def initServer(self):
        self.channelDict = hardwareConfiguration.channelDict
        self.collectionTime = hardwareConfiguration.collectionTime
        self.collectionMode = hardwareConfiguration.collectionMode
        self.timeResolution = float(hardwareConfiguration.timeResolution)
        self.ddsDict = hardwareConfiguration.ddsDict
        self.timeResolvedResolution = hardwareConfiguration.timeResolvedResolution
        self.remoteChannels = hardwareConfiguration.remoteChannels
        self.collectionTimeRange = hardwareConfiguration.collectionTimeRange
        self.sequenceTimeRange = hardwareConfiguration.sequenceTimeRange
        self.inCommunication = DeferredLock()

        #appropriated variables
        self.isProgrammed = False

        yield self.initializeRemote()
        self.initializeSettings()
        self.listeners = set()


    def initializeSettings(self):
        #initialize TTLs
        for channel in self.channelDict.values():
            channelnumber = channel.channelnumber
            if channel.ismanual:
                state = channel.manualin ^ channel.manualstate
                self.api.setManual(channelnumber, state)
            else:
                self.api.setAuto(channelnumber, channel.autoinv)

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

    @setting(5, 'Add TTL Pulse', channel = 's', start = 'v[s]', duration = 'v[s]')
    def addTTLPulse(self, c, channel, start, duration):
        """
        Add a TTL Pulse to the sequence, times are in seconds
        """
        if channel not in self.channelDict.keys():
            raise Exception("Unknown Channel {}".format(channel))
        hardwareAddr = self.channelDict.get(channel).channelnumber
        sequence = c.get('sequence')
        start = start['s']
        duration = duration['s']
        #simple error checking
        if not ((self.sequenceTimeRange[0] <= start <= self.sequenceTimeRange[1]) and
                 (self.sequenceTimeRange[0] <= start + duration <= self.sequenceTimeRange[1])):
            raise Exception("Time boundaries are out of range")
        if not duration >= self.timeResolution:
            raise Exception("Incorrect duration")
        if not sequence:
            raise Exception("Please create new sequence first")
        sequence.addPulse(hardwareAddr, start, duration)

    @setting(6, 'Add TTL Pulses', pulses = '*(sv[s]v[s])')
    def addTTLPulses(self, c, pulses):
        """
        Add multiple TTL Pulses to the sequence, times are in seconds. The pulses are a list in the same format as 'add ttl pulse'.
        """
        for pulse in pulses:
            channel = pulse[0]
            start = pulse[1]
            duration = pulse[2]
            yield self.addTTLPulse(c, channel, start, duration)

    @setting(7, "Extend Sequence Length", timeLength = 'v[s]')
    def extendSequenceLength(self, c, timeLength):
        """
        Allows to optionally extend the total length of the sequence beyond the last TTL pulse.
        """
        sequence = c.get('sequence')
        if not (self.sequenceTimeRange[0] <= timeLength['s'] <= self.sequenceTimeRange[1]):
            raise Exception("Time boundaries are out of range")
        if not sequence:
            raise Exception("Please create new sequence first")
        sequence.extendSequenceLength(timeLength['s'])

    @setting(10, "Human Readable TTL", getProgrammed = 'b', returns = '*2s')
    def humanReadableTTL(self, c, getProgrammed = None):
        """
        Args:
            getProgrammed (bool): False/None(default) to get the sequence added by current context,
                              True to get the last programmed sequence
        Returns:
            a readable form of TTL sequence
        """
        sequence = c.get('sequence')
        if getProgrammed:
            sequence = self.programmed_sequence
        if not sequence:
            raise Exception ("Please create new sequence first")
        ttl, dds = sequence.humanRepresentation()
        return ttl.tolist()

    @setting(11, "Human Readable DDS", getProgrammed = 'b', returns = '*(svv)')
    def humanReadableDDS(self, c, getProgrammed = None):
        """
        Args:
            getProgrammed (bool): False/None(default) to get the sequence added by current context,
                              True to get the last programmed sequence
        Returns:
            a readable form of DDS sequence
        """
        sequence = c.get('sequence')
        if getProgrammed:
            sequence = self.programmed_sequence
        if not sequence:
            raise Exception("Please create new sequence first")
        ttl, dds = sequence.humanRepresentation()
        return dds

    @setting(12, 'Get Channels', returns = '*(sw)')
    def getChannels(self, c):
        """
        Returns all available channels, and the corresponding hardware numbers
        """
        d = self.channelDict
        keys = d.keys()
        numbers = [d[key].channelnumber for key in keys]
        return zip(keys, numbers)

    @setting(15, 'Get State', channelName = 's', returns = '(bbbb)')
    def getState(self, c, channelName):
        """
        Returns the current state of the switch: in the form (Manual/Auto, ManualOn/Off, ManualInversionOn/Off, AutoInversionOn/Off)
        """
        if channelName not in self.channelDict.keys():
            raise Exception("Incorrect Channel")
        channel = self.channelDict[channelName]
        answer = (channel.ismanual, channel.manualstate, channel.manualinv, channel.autoinv)
        return answer

    #Signal/Context functions
    def notifyOtherListeners(self, context, message, f):
        """
        Notifies all listeners except the one in the given context, executing function f
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        f(message, notified)

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)
