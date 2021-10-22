from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from twisted.internet.threads import deferToThread
from labrad.units import WithUnit
import numpy as np


class dds_access_locked(Error):
    def __init__(self):
        super(dds_access_locked, self).__init__(
            msg='DDS Access Locked: running a pulse sequence',
            code=1
        )

class DDS_artiq(LabradServer):

    """Contains the DDS functionality for the ARTIQ Pulser server"""

    on_dds_param = Signal(142006, 'signal: new dds parameter', '(ssv)')

    @inlineCallbacks
    def initializeDDS(self):
        self.ddsLock = False
        self.api.initializeDDS()
        for name, channel in self.ddsDict.items():
            channel.name = name
            freq, ampl, phase = (channel.frequency, channel.amplitude, channel.phase)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
            yield self.inCommunication.run(self._setDDSParam, channel, freq, ampl, phase)
        self.ddsSequenceARTIQ = {}
        #todo: get io update alignment

    @setting(41, "Get DDS Channels", returns = '*s')
    def getDDSChannels(self, c):
        """get the list of available channels"""
        return self.ddsDict.keys()

    @setting(42, "Amplitude", name= 's', amplitude = 'v[dBm]', returns = 'v[dBm]')
    def amplitude(self, c, name = None, amplitude = None):
        """Get or set the amplitude of the named channel or the selected channel"""
        #get the hardware channel
        if self.ddsLock and amplitude is not None:
            raise dds_access_locked()
        channel = self._getChannel(c, name)
        if amplitude is not None:
            #set amplitude
            amplitude = amplitude['dBm']
            self._checkRange('amplitude', channel, amplitude)
            if channel.state:
                #only send to hardware if channel is on
                yield self._setDDSParam(channel, amp=amplitude)
            channel.amplitude = amplitude
            self.notifyOtherListeners(c, (name, 'amplitude', channel.amplitude), self.on_dds_param)
        amplitude = WithUnit(channel.amplitude, 'dBm')
        returnValue(amplitude)

    @setting(43, "Frequency", name = 's', frequency = ['v[MHz]'], returns = ['v[MHz]'])
    def frequency(self, c, name = None, frequency = None):
        """Get or set the frequency of the named channel or the selected channel"""
        #get the hardware channel
        if self.ddsLock and frequency is not None:
            raise dds_access_locked()
        channel = self._getChannel(c, name)
        if frequency is not None:
            #set frequency
            frequency = frequency['MHz']
            self._checkRange('frequency', channel, frequency)
            if channel.state:
                #only send to hardware if the channel is on
                yield self._setDDSParam(channel, freq=frequency)
            channel.frequency = frequency
            self.notifyOtherListeners(c, (name, 'frequency', channel.frequency), self.on_dds_param)
        frequency = WithUnit(channel.frequency, 'MHz')
        returnValue(frequency)

    @setting(44, "Phase", name = 's', phase = ['v'], returns = ['v'])
    def phase(self, c, name = None, phase = None):
        """Get or set the phase of the named channel or the selected channel"""
        #get the hardware channel
        if self.ddsLock and phase is not None:
            raise dds_access_locked()
        channel = self._getChannel(c, name)
        if phase is not None:
            #set phase
            phase = phase['MHz']#todo: change units?
            self._checkRange('phase', channel, phase)
            if channel.state:
                #only send to hardware if the channel is on
                yield self._setDDSParam(channel, phase = phase)
            channel.phase = phase
            self.notifyOtherListeners(c, (name, 'phase', channel.phase), self.on_dds_param)
        returnValue(channel.phase)

    @setting(45, 'Output', name= 's', state = 'b', returns =' b')
    def output(self, c, name = None, state = None):
        """
        Turns the dds on and off. Turning off the DDS sets the frequency and amplitude
        to the off_parameters provided in the configuration.
        """
        if self.ddsLock and state is not None:
            raise dds_access_locked()
        channel = self._getChannel(c, name)
        if state is not None:
            channel.state = state
            # off to on
            if state and not channel.state:
                freq, ampl, phas = (channel.frequency, channel.amplitude, channel.phase)
                yield self.inCommunication.run(self._setDDSParam, channel, freq, ampl, phas)
            # on to off
            elif channel.state and not state:
                freq, ampl, phas = channel.off_parameters
                yield self.inCommunication.run(self._setDDSParam, channel, freq, ampl, phas)
            self.notifyOtherListeners(c, (name, 'state', channel.state), self.on_dds_param)
        returnValue(channel.state)

    @setting(46, 'Add DDS Pulses',  values = ['*(sv[s]v[s]v[MHz]v[dBm]v[deg]v[MHz]v[dB])'])
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
                self.ddsSequenceARTIQ.append((name, start, (freq, ampl, phase, ramp_rate, amp_ramp_rate), 'start'))
                self.ddsSequenceARTIQ.append((name, start + dur, (freq, ampl, phase, ramp_rate, amp_ramp_rate), 'start'))

    @setting(47, 'Get DDS Amplitude Range', name = 's', returns = '(vv)')
    def getDDSAmplRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedamplrange

    @setting(48, 'Get DDS Frequency Range', name = 's', returns = '(vv)')
    def getDDSFreqRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedfreqrange

    @setting(49, 'Clear DDS Lock')
    def clear_dds_lock(self, c):
        self.ddsLock = False

    @inlineCallbacks
    def _setDDSParam(self, channel, ampl = None, freq = None, phase = None):
        if ampl is None:
            ampl = self.dmb_to_fampl(channel.amplitude) #convert to fractional amplitude
            ampl = self.amplitude_to_asf(ampl)
        if freq is None:
            freq = self.frequency_to_ftw(channel.frequency/1000000) #MHz to Hz
        if phase is None:
            phase = self.turns_to_pow(channel.phase)
        yield self.inCommunication.run(self.api.setDDSParam, channel.channelnumber, freq, ampl, phase)

    def _artiqParseDDS(self, dds_seq):
        #get each DDS pulse as (name, time, RAM, on/off)
        dds_seq = sorted(self.ddsSettingList, key = lambda t: t[1])
        entries =
        if not self.userAddedDDS():
            return None
        state = self.parent._getCurrentDDS()
        #keeps track of end time and
        pulses_end = {}.fromkeys(state, (0, 'stop'))
        dds_program = {}.fromkeys(state, '')
        lastTime = 0
        #get each DDS pulse as (name, time, RAM, on/off)
        entries = sorted(self.ddsSettingList, key = lambda t: t[1] ) #sort by starting time
        possibleError = (0, '')
        while True:
            try:
                name, start, num, typ = entries.pop(0)
            except IndexError:
                if start  == lastTime:
                    #still have unprogrammed entries
                    self.addToProgram(dds_program, state)
                    self._addNewSwitch(lastTime, self.advanceDDS, 1)
                    self._addNewSwitch(lastTime + self.resetstepDuration, self.advanceDDS, -1)
                #add termination
                for name in iter(dds_program):
                    dds_program[name] += '\x00\x00'
                #at the end of the sequence, reset dds
                lastTTL = max(self.switchingTimes.keys())
                self._addNewSwitch(lastTTL, self.resetDDS, 1)
                self._addNewSwitch(lastTTL + self.resetstepDuration, self.resetDDS, -1)
                return dds_program
            end_time, end_typ = pulses_end[name]
            # the time has advanced, so need to program the previous state
            if start > lastTime:
                #raise exception if error exists and belongs to that time
                if possibleError[0] == lastTime and len(possibleError[1]):
                    raise Exception(possibleError[1])
                self.addToProgram(dds_program, state)
                #move RAM to next position
                if not lastTime == 0:
                    self._addNewSwitch(lastTime,self.advanceDDS,1)
                    self._addNewSwitch(lastTime + self.resetstepDuration, self.advanceDDS, -1)
                lastTime = start
            #move to next dds pulse
            if start == end_time:
                if end_typ == 'stop' and typ == 'start':
                    possibleError = (0, '')
                    state[name] = num
                    pulses_end[name] = (start, typ)
                elif end_typ == 'start' and typ == 'stop':
                    possibleError = (0, '')
            elif end_typ == typ:
                possibleError = (start, 'Found Overlap Of Two Pulses for channel {}'.format(name))
                state[name] = num
                pulses_end[name] = (start, typ)
            else:
                state[name] = num
                pulses_end[name] = (start, typ)

    #needed for compatibility with sequence object (sequence.py)

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