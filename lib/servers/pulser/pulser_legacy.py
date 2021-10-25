#labrad and artiq imports
from labrad.server import LabradServer, setting, Signal

#async imports
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred

#wrapper imports
from sequence import Sequence

#function imports
import numpy as np

class Pulser_legacy(LabradServer):

    """Contains legacy functionality for Pulser"""

    onSwitch = Signal(611051, 'signal: switch toggled', '(ss)')
    on_dds_param = Signal(142006, 'signal: new dds parameter', '(ssv)')
    on_line_trigger_param = Signal(142007, 'signal: new line trigger parameter', '(bv)')

    def initServer(self):
        #todo: appropriate these variables
            #device storage
        self.channelDict = hardwareConfiguration.channelDict
        self.ddsDict = hardwareConfiguration.ddsDict
        self.remoteChannels = hardwareConfiguration.remoteChannels
            #pmt
        self.collectionTime = hardwareConfiguration.collectionTime
        self.collectionMode = hardwareConfiguration.collectionMode
        self.collectionTimeRange = hardwareConfiguration.collectionTimeRange
            #ttl
        self.timeResolution = float(hardwareConfiguration.timeResolution)
        self.sequenceTimeRange = hardwareConfiguration.sequenceTimeRange
        yield self.initializeRemote()
        self.listeners = set()

        #TTLs
        for channel in self.channelDict.values():
            channelnumber = channel.channelnumber
            if channel.ismanual:
                state = channel.manualin ^ channel.manualstate
                self.api.setManual(channelnumber, state)
            else:
                self.api.setAuto(channelnumber, channel.autoinv)

        #DDS
        self.ddsLock = False
        self.api.initializeDDS()

        for name, channel in self.ddsDict.items():
            channel.name = name
            freq, ampl, phase = (channel.frequency, channel.amplitude, channel.phase)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
            yield self.inCommunication.run(self._setDDSParam, channel, freq, ampl, phase)

        #Linetrigger
        self.linetrigger_limits = [WithUnit(v, 'us') for v in hardwareConfiguration.lineTriggerLimits]


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

    @setting(111, 'Add TTL Pulse', channel = 's', start = 'v[s]', duration = 'v[s]')
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

    @setting(112, 'Add TTL Pulses', pulses = '*(sv[s]v[s])')
    def addTTLPulses(self, c, pulses):
        """
        Add multiple TTL Pulses to the sequence, times are in seconds. The pulses are a list in the same format as 'add ttl pulse'.
        """
        for pulse in pulses:
            channel = pulse[0]
            start = pulse[1]
            duration = pulse[2]
            yield self.addTTLPulse(c, channel, start, duration)

    @setting(113, "Extend Sequence Length", timeLength = 'v[s]')
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

    @setting(114, "Human Readable TTL", getProgrammed = 'b', returns = '*2s')
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

    @setting(115, "Human Readable DDS", getProgrammed = 'b', returns = '*(svv)')
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

    @setting(116, 'Get Channels', returns = '*(sw)')
    def getChannels(self, c):
        """
        Returns all available channels, and the corresponding hardware numbers
        """
        d = self.channelDict
        keys = d.keys()
        numbers = [d[key].channelnumber for key in keys]
        return zip(keys, numbers)

    @setting(117, 'Get State', channelName = 's', returns = '(bbbb)')
    def getState(self, c, channelName):
        """
        Returns the current state of the switch: in the form (Manual/Auto, ManualOn/Off, ManualInversionOn/Off, AutoInversionOn/Off)
        """
        if channelName not in self.channelDict.keys():
            raise Exception("Incorrect Channel")
        channel = self.channelDict[channelName]
        answer = (channel.ismanual, channel.manualstate, channel.manualinv, channel.autoinv)
        return answer

    #DDS functions
    @setting(121, "Get DDS Channels", returns = '*s')
    def getDDSChannels(self, c):
        """get the list of available channels"""
        return self.ddsDict.keys()

    @setting(122, 'Add DDS Pulses',  values = ['*(sv[s]v[s]v[MHz]v[dBm]v[deg]v[MHz]v[dB])'])
    def addDDSPulses(self, c, values):
        '''
        input in the form of a list [(name, start, duration, frequency, amplitude, phase, ramp_rate, amp_ramp_rate)]
        '''
        sequence = c.get('sequence')
        if not sequence:
            raise Exception("Please create new sequence first")
        for value in values:
            try:
                name, start, dur, freq, ampl = value
                phase = 0.0
                ramp_rate = 0.0
            except ValueError:
                name, start, dur, freq, ampl, phase, ramp_rate, amp_ramp_rate = value
            try:
                channel = self.ddsDict[name]
            except KeyError:
                raise Exception("Unknown DDS channel {}".format(name))
            start = start['s']
            dur = dur['s']
            freq = freq['MHz']
            ampl = ampl['dBm']
            phase = phase['deg']
            ramp_rate = ramp_rate['MHz']
            amp_ramp_rate = amp_ramp_rate['dB']
            freq_off, ampl_off = channel.off_parameters
            #only check range if dds won't be off
            if (freq == 0) or (ampl == 0):
                freq, ampl = freq_off, ampl_off
            else:
                self._checkRange('frequency', channel, freq)
                self._checkRange('amplitude', channel, ampl)
            #convert DDS settings to RAM data
            num = self.settings_to_num(channel, freq, ampl, phase, ramp_rate, amp_ramp_rate)
            num_off = self.settings_to_num(channel, freq, ampl_off, phase, ramp_rate, amp_ramp_rate)
            #note < sign, because start can not be 0.
            #this would overwrite the 0 position of the ram, and cause the dds to change before pulse sequence is launched
            if not self.sequenceTimeRange[0] < start <= self.sequenceTimeRange[1]:
                raise Exception("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start))
            if not self.sequenceTimeRange[0] < start + dur <= self.sequenceTimeRange[1]:
                raise Exception("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start + dur))
            if not dur == 0:    #0 length pulses are ignored
                sequence.addDDS(name, start, num, 'start')
                sequence.addDDS(name, start + dur, num_off, 'stop')

    @setting(123, 'Get DDS Amplitude Range', name = 's', returns = '(vv)')
    def getDDSAmplRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedamplrange

    @setting(124, 'Get DDS Frequency Range', name = 's', returns = '(vv)')
    def getDDSFreqRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedfreqrange

    @setting(125, 'Clear DDS Lock')
    def clear_dds_lock(self, c):
        self.ddsLock = False

    @setting(60, "Get Line Trigger Limits", returns='*v[us]')
    def getLineTriggerLimits(self, c):
        """get limits for duration of line triggering"""
        return self.linetrigger_limits


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

    #Legacy/compatibility functions
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

    def _getCurrentDDS(self):
        '''
        Returns a dictionary {name:num} with the representation of the current dds state
        '''
        return dict([(name, self._channel_to_num(channel)) for (name, channel) in self.ddsDict.items()])

    def _checkRange(self, t, channel, val):
        if t == 'amplitude':
            r = channel.allowedamplrange
        elif t == 'frequency':
            r = channel.allowedfreqrange
        if not r[0] <= val <= r[1]:
            raise Exception("channel {0} : {1} of {2} is outside the allowed range".format(channel.name, t, val))

    def _getChannel(self, c, name):
        try:
            channel = self.ddsDict[name]
        except KeyError:
            raise Exception("Channel {0} not found".format(name))
        return channel

    def settings_to_num(self, channel, freq, ampl, phase = 0.0, ramp_rate = 0.0, amp_ramp_rate = 0.0):
        if not channel.phase_coherent_model:
            num = self._valToInt(channel, freq, ampl)
        else:
            num = self._valToInt_coherent(channel, freq, ampl, phase, ramp_rate, amp_ramp_rate)
        return num

    def _valToInt_coherent(self, channel, freq, ampl, phase=0, ramp_rate=0, amp_ramp_rate=0):  ### add ramp for ramping functionality
        '''
        takes the frequency and amplitude values for the specific channel and returns integer representation of the dds setting
        freq is in MHz
        power is in dbm
        '''
        ans = 0
        ## changed the precision from 32 to 64 to handle super fine frequency tuning
        for val, r, m, precision in [(freq, channel.boardfreqrange, 1, 64),
                                     (ampl, channel.boardamplrange, 2 ** 64, 16),
                                     (phase, channel.boardphaserange, 2 ** 80, 16)]:
            minim, maxim = r
            # print r
            resolution = (maxim - minim) / float(2 ** precision - 1)
            # print resolution
            seq = int((val - minim) / resolution)  # sequential representation
            # print seq
            ans += m * seq

        ### add ramp rate
        minim, maxim = channel.boardramprange
        resolution = (maxim - minim) / float(2 ** 16 - 1)
        if ramp_rate < minim:  ### if the ramp rate is smaller than the minim, thenn treat it as no rampp
            seq = 0
        elif ramp_rate > maxim:
            seq = 2 ** 16 - 1
        else:
            seq = int((ramp_rate - minim) / resolution)

        ans += 2 ** 96 * seq

        ### add amp ramp rate

        minim, maxim = channel.board_amp_ramp_range
        minim_slope = 1 / maxim
        maxim_slope = 1 / minim
        resolution = (maxim_slope - minim_slope) / float(2 ** 16 - 1)
        if (amp_ramp_rate < minim):
            seq_amp_ramp = 0
        elif (amp_ramp_rate > maxim):
            seq_amp_ramp = 1
        else:
            slope = 1 / amp_ramp_rate
            seq_amp_ramp = int(np.ceil((slope - minim_slope) / resolution))  # return ceiling of the number

        ans += 2 ** 112 * seq_amp_ramp

        return ans

    def _intToBuf_coherent(self, num):
        '''
        takes the integer representing the setting and returns the buffer string for dds programming
        '''

        freq_num = (
                    num % 2 ** 64)  # change according to the new DDS which supports 64 bit tuning of the frequency. Used to be #freq_num = (num % 2**32)*2**32
        b = bytearray(8)  # initialize the byte array to sent to the pusler later
        for i in range(8):
            b[i] = (freq_num // (2 ** (i * 8))) % 256
            # print i, "=", (freq_num//(2**(i*8)))%256

        # phase
        phase_num = (num // 2 ** 80) % (2 ** 16)
        phase = bytearray(2)
        phase[0] = phase_num % 256
        phase[1] = (phase_num // 256) % 256

        ### amplitude
        ampl_num = (num // 2 ** 64) % (2 ** 16)
        amp = bytearray(2)
        amp[0] = ampl_num % 256
        amp[1] = (ampl_num // 256) % 256

        ### ramp rate. 16 bit tunability from roughly 116 Hz/ms to 7.5 MHz/ms
        ramp_rate = (num // 2 ** 96) % (2 ** 16)
        ramp = bytearray(2)
        ramp[0] = ramp_rate % 256
        ramp[1] = (ramp_rate // 256) % 256

        ##  amplitude ramp rate
        amp_ramp_rate = (num // 2 ** 112) % (2 ** 16)
        # print "amp_ramp is" , amp_ramp_rate
        amp_ramp = bytearray(2)
        amp_ramp[0] = amp_ramp_rate % 256
        amp_ramp[1] = (amp_ramp_rate // 256) % 256

        ##a = bytearray.fromhex(u'0000') + amp + bytearray.fromhex(u'0000 0000')
        a = phase + amp + amp_ramp + ramp

        ans = a + b
        return ans