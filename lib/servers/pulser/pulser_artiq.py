"""
### BEGIN NODE INFO
[info]
name = ARTIQ Pulser
version = 3.0
description = Pulser using the ARTIQ box. Backwards compatible with old pulse sequences and experiments.
instancename = ARTIQ_Pulser

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

#labrad and server imports
from labrad.server import LabradServer, setting, Signal
from pulser_artiq_DDS import DDS_artiq
from pulser_artiq_linetrigger import LineTrigger_artiq

#async imports
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread

#wrapper imports
from sequence import Sequence

#function imports
import numpy as np

from devices import Devices

class Pulser_artiq(DDS_artiq, ARTIQ_LineTrigger):

    name = 'ARTIQ Pulser'
    regKey = 'ARTIQ_Pulser'

    onSwitch = Signal(611051, 'signal: switch toggled', '(ss)')

    def __init__(self, api):
        self.api = api

        #conversions
        self.seconds_to_mu = api.core.seconds_to_mu
        self.amplitude_to_asf = api.dds_list[0].amplitude_to_asf
        self.frequency_to_ftw = api.dds_list[0].frequency_to_ftw
        self.turns_to_ftw = api.dds_list[0].turns_to_ftw

        #start
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
        self.haveSecondPMT = hardwareConfiguration.secondPMT

        self.inCommunication = DeferredLock()

        #appropriated variables
        self.isProgrammed = False

        LineTrigger_artiq.initialize(self)
        yield self.initializeRemote()
        self.initializeSettings()
        self.listeners = set()

        #pulser variables
        self.maxRuns = 0
        self.programmed_sequence = None

    def initializeSettings(self):
        for channel in self.channelDict.values():
            channelnumber = channel.channelnumber
            if channel.ismanual:
                state = self.cnot(channel.manualinv, channel.manualstate)
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

    #TTL Sequence functions
    @setting(0, "New Sequence", returns = '')
    def newSequence(self, c):
        """
        Create New Pulse Sequence
        """
        c['sequence'] = Sequence(self)

    @setting(1, "Program Sequence", returns = '')
    def programSequence(self, c, sequence):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        sequence = c.get('sequence')
        if not sequence:
            raise Exception("Please create new sequence first")
        self.programmed_sequence = sequence
        dds, ttl = sequence.progRepresentation()
        yield self.inCommunication.acquire()
        if dds is None:
            dds = {}
        dds_single, dds_ramp = self.artiq_convert_dds(dds)
        yield deferToThread(self.api.programBoard, ttl, dds_single, dds_ramp)
        self.inCommunication.release()
        self.isProgrammed = True

    @setting(2, "Start Infinite", returns = '')
    def startInfinite(self, c):
        if not self.isProgrammed:
            raise Exception("No Programmed Sequence")
        yield self.inCommunication.acquire()
        self.maxRuns = np.inf
        yield deferToThread(self.api.runSequence, np.inf)
        self.inCommunication.release()

    @setting(3, "Complete Infinite Iteration", returns = '')
    def completeInfinite(self, c):
        if self.runInf is False:
            raise Exception("Not Running Infinite Sequence")
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.stopSequence)
        self.maxRuns = 0
        self.inCommunication.release()

    @setting(4, "Start Single", returns = '')
    def start(self, c):
        if not self.isProgrammed:
            raise Exception ("No Programmed Sequence")
        yield self.inCommunication.acquire()
        self.maxRuns = 1
        self.api.runSequence(1)
        self.inCommunication.release()

    @setting(5, 'Add TTL Pulse', channel = 's', start = 'v[s]', duration = 'v[s]')
    def addTTLPulse(self, c, channel, start, duration):
        """
        Add a TTL Pulse to the sequence, times are in seconds
        """
        if channel not in self.channelDict.keys(): raise Exception("Unknown Channel {}".format(channel))
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

    @setting(8, "Stop Sequence")
    def stopSequence(self, c):
        """
        Stops any currently running sequence
        """
        self.maxRuns = 0
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.stopSequence)
        yield deferToThread(self.api.eraseSequence)
        self.inCommunication.release()
        self.ddsLock = False

    @setting(9, "Start Number", repetitions = 'w')
    def startNumber(self, c, repetitions):
        """
        Starts the repetition number of iterations
        """
        if not self.isProgrammed:
            raise Exception("No Programmed Sequence")
        if not 1 <= repetitions <= (2**16 - 1):
            raise Exception("Incorrect number of pulses")
        yield self.inCommunication.acquire()
        self.api.maxRuns = repetitions
        self.maxRuns = repetitions
        self.api.runSequence()
        self.inCommunication.release()

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

    @setting(13, 'Switch Manual', channelName = 's', state= 'b')
    def switchManual(self, c, channelName, state = None):
        """
        Switches the given channel into the manual mode, by default will go into the last remembered state but can also
        pass the argument which state it should go into.
        """
        if channelName not in self.channelDict.keys():
            raise Exception("Incorrect Channel")
        channel = self.channelDict[channelName]
        channelNumber = channel.channelnumber
        channel.ismanual = True

        if state is not None:
            channel.manualstate = state
        else:
            state = channel.manualstate

        state = self.cnot(channel.manualinv, state)

        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setManual, channelNumber, state)
        self.inCommunication.release()

        if state:
            self.notifyOtherListeners(c, (channelName, 'ManualOn'), self.onSwitch)
        else:
            self.notifyOtherListeners(c, (channelName, 'ManualOff'), self.onSwitch)

    @setting(14, 'Switch Auto', channelName = 's', invert= 'b')
    def switchAuto(self, c, channelName, invert = None):
        """
        Switches the given channel into the automatic mode, with an optional inversion.
        """
        if channelName not in self.channelDict.keys():
            raise Exception("Incorrect Channel")
        channel = self.channelDict[channelName]
        channelNumber = channel.channelnumber
        channel.ismanual = False

        if invert is not None:
            channel.autoinv = invert
        else:
            invert = channel.autoinv

        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setAuto, channelNumber, invert)
        self.inCommunication.release()

        self.notifyOtherListeners(c, (channelName, 'Auto'), self.onSwitch)

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

    @setting(16, 'Wait Sequence Done', timeout = 'v', returns = 'b')
    def waitSequenceDone(self, c, timeout = None):
        """
        Returns true if the sequence has completed within a timeout period
        """
        if timeout is None:
            timeout = self.sequenceTimeRange[1]
        requestCalls = int(timeout*1000)
        for i in range(requestCalls):
            yield self.inCommunication.acquire()
            numRuns = yield deferToThread(self.api.numRepetitions)
            self.inCommunication.release()
            if numRuns >= self.maxRuns:
                returnValue(True)
            yield self.wait(0.001)
        returnValue(False)

    def wait(self, seconds, result=None):
        """Returns a deferred that will be fired later"""
        d = Deferred()
        reactor.callLater(seconds, d.callback, result)
        return d

    @setting(17, 'Repeatitions Completed', returns = 'w')
    def repeatitionsCompleted(self, c):
        """
        Check how many repetitions have been completed in the infinite or number modes
        """
        yield self.inCommunication.acquire()
        completed = self.api.numRuns
        self.inCommunication.release()
        returnValue(completed)

    #PMT functions
    #todo: ensure in ms for times pmt
    @setting(21, 'Set Mode', mode = 's', returns = '')
    def setMode(self, c, mode):
        """
        Set the counting mode, either 'Normal' or 'Differential'
        In 'Normal', the FPGA automatically sends the counts with a preset frequency
        In 'Differential', the FPGA uses triggers the pulse sequence
        frequency and to know when the repumping light is switched on or off.
        """
        if mode not in self.collectionTime.keys():
            raise Exception("Incorrect mode")
        self.collectionMode = mode
        countInterval = self.collectionTime[mode]
        yield self.inCommunication.acquire()
        if mode == 'Normal':
            #set the mode on the device and set update time for normal mode
            yield deferToThread(self.api.setMode, 0)
            yield deferToThread(self.api.setPMTCountInterval, countInterval)
        elif mode == 'Differential':
            yield deferToThread(self.api.setMode, 1)
        self.inCommunication.release()

    @setting(22, 'Set Collection Time', new_time = 'v', mode = 's', returns = '')
    def setCollectTime(self, c, new_time, mode):
        """
        Sets how long to collect photonslist in either 'Normal' or 'Differential' mode of operation
        """
        if not self.collectionTimeRange[0] <= new_time <= self.collectionTimeRange[1]:
            raise Exception('Incorrect collection time')
        if mode not in self.collectionTime.keys():
            raise Exception("Incorrect mode")

        self.collectionTime[mode] = new_time
        if mode == 'Normal':
            yield self.inCommunication.acquire()
            yield deferToThread(self.api.setPMTCountInterval, new_time)
            self.inCommunication.release()

    @setting(23, 'Get Collection Mode', returns = 's')
    def getMode(self, c):
        return self.collectionMode

    @setting(24, 'Get Collection Time', returns = '(vv)')
    def getCollectTime(self, c):
        return self.collectionTimeRange

    @setting(25, 'Get Readout Counts', returns = '*v')
    def getReadoutCounts(self, c):
        yield self.inCommunication.acquire()
        countlist = yield deferToThread(self.api.getReadoutCounts)
        self.inCommunication.release()
        returnValue(countlist)

    @setting(26, 'Reset Readout Counts')
    def resetReadoutCounts(self, c):
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.resetReadoutCounts)
        self.inCommunication.release()

    #DDS settings
    @setting(90, 'Internal Reset DDS', returns = '')
    def internal_reset_dds(self, c):
        """
        Reset all DDSs
        """
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.resetAllDDS)
        self.inCommunication.release()

    @setting(91, 'Internal Advance DDS', returns = '')
    def internal_advance_dds(self, c):
        """
        Advance DDSs to the next RAM position
        """
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.advanceAllDDS)
        self.inCommunication.release()

    @setting(92, "Reinitialize DDS", returns = '')
    def reinitializeDDS(self, c):
        """
        Reprograms the DDS chip to its initial state
        """
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.initializeDDS)
        self.inCommunication.release()

    def cnot(self, control, inp):
        if control:
            inp = not inp
        return inp

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
