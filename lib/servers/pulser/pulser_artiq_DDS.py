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
            frequency = frequency['Hz']
            self._checkRange('frequency', channel, frequency)
            if channel.state:
                #only send to hardware if the channel is on
                yield self._setDDSParam(channel, freq=frequency)
            channel.frequency = frequency
            self.notifyOtherListeners(c, (name, 'frequency', channel.frequency), self.on_dds_param)
        frequency = WithUnit(channel.frequency, 'Hz')
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
            num = self._settingstoRAM(channel, freq, ampl, phase, ramp_rate, amp_ramp_rate)
            num_off = self._settingstoRAM(channel, freq, ampl_off, phase, ramp_rate, amp_ramp_rate)
            #note < sign, because start can not be 0.
            #this would overwrite the 0 position of the ram, and cause the dds to change before pulse sequence is launched
            if not self.sequenceTimeRange[0] < start <= self.sequenceTimeRange[1]:
                raise Exception("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start))
            if not self.sequenceTimeRange[0] < start + dur <= self.sequenceTimeRange[1]:
                raise Exception("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start + dur))
            if not dur == 0:    #0 length pulses are ignored
                sequence.addDDS(name, start, num, 'start')
                sequence.addDDS(name, start + dur, num_off, 'stop')

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
            freq = self.frequency_to_ftw(channel.frequency)
        if phase is None:
            phase = self.turns_to_pow(channel.phase)
        yield self.inCommunication.run(self.api.setDDSParam, channel.channelnumber, freq, ampl, phase)

    #not used
    def _settingstoRAM(self, channel, freq, ampl, phase = 0.0, ramp_rate = 0.0, amp_ramp_rate = 0.0):
        """
        Converts the DDS settings to RAM data
        """
        freq = self.frequency_to_ftw(freq)
        ampl = self.dbm_to_fampl(ampl)
        ampl = self.amplitude_to_asw(ampl)
        phase = self.turns_to_pow(phase)
        #no need if only 8 profiles and no ramp
        if (ramp_rate == 0) and (amp_ramp_rate == 0):
            return (freq, ampl, phase)

    def _artiqParseDDS(self, dds_seq):
        #get each DDS pulse as (name, time, RAM, on/off)
        dds_seq = sorted(self.ddsSettingList, key = lambda t: t[1])
        entries =

    #needed for compatibility with sequence object (sequence.py)
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
