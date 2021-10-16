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
            freq, ampl = (channel.frequency, channel.amplitude)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
            yield self.inCommunication.run(self._setParameters, channel, freq, ampl)
        #todo: convert time to mu and dbm amplitude to fractional value

    @setting(41, "Get DDS Channels", returns = '*s')
    def getDDSChannels(self, c):
        """get the list of available channels"""
        return self.ddsDict.keys()

    @setting(43, "Amplitude", name= 's', amplitude = 'v[dBm]', returns = 'v[dBm]')
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

    @setting(44, "Frequency", name = 's', frequency = ['v[MHz]'], returns = ['v[MHz]'])
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

    @setting(45, 'Add DDS Pulses',  values = ['*(sv[s]v[s]v[MHz]v[dBm]v[deg]v[MHz]v[dB])'])
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
            if freq == 0 or ampl == 0: #off state
                freq, ampl = freq_off, ampl_off
            else:
                self._checkRange('frequency', channel, freq)
                self._checkRange('amplitude', channel, ampl)
            num = self.settings_to_num(channel, freq, ampl, phase, ramp_rate, amp_ramp_rate)
            if not channel.phase_coherent_model:
                num_off = self.settings_to_num(channel, freq_off, ampl_off)
            else:
                #note that keeping the frequency the same when switching off to preserve phase coherence
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

    @setting(46, 'Get DDS Amplitude Range', name = 's', returns = '(vv)')
    def getDDSAmplRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedamplrange

    @setting(47, 'Get DDS Frequency Range', name = 's', returns = '(vv)')
    def getDDSFreqRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedfreqrange

    @setting(48, 'Output', name= 's', state = 'b', returns =' b')
    def output(self, c, name = None, state = None):
        """Turns the dds on and off. Turning off the DDS sets the frequency and amplitude
        to the off_parameters provided in the configuration.
        """
        if self.ddsLock and state is not None:
            raise dds_access_locked()
        channel = self._getChannel(c, name)
        if state is not None:
            yield self._setOutput(channel, state)
            channel.state = state
            self.notifyOtherListeners(c, (name, 'state', channel.state), self.on_dds_param)
        returnValue(channel.state)

    @setting(49, 'Clear DDS Lock')
    def clear_dds_lock(self, c):
        self.ddsLock = False

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

    @inlineCallbacks
    def _setDDSParam(self, channel, ampl = None, freq = None):
        if ampl is None:
            ampl = self.amplitude_to_asf(channel.amplitude)
        if freq is None:
            freq = self.frequency_to_ftw(channel.frequency)
        yield self.inCommunication.run(self.api.setDDSParam, channel.channelnumber, freq, ampl)

    @inlineCallbacks
    def _setOutput(self, channel, state):
        # off to on
        if state and not channel.state:
            yield self.inCommunication.run(self._setDDSParam, channel, channel.frequency, channel.amplitude)
        # on to off
        elif channel.state and not state:
            freq, ampl = channel.off_parameters
            yield self.inCommunication.run(self._setDDSParam, channel, freq, ampl)

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

    def _channel_to_num(self, channel):
        '''
        Returns the current state of the channel in the num representation
        '''
        if channel.state:
            #if on, use current values. else, use off values
            freq, ampl = (channel.frequency, channel.amplitude)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
        else:
            freq, ampl = channel.off_parameters
        num = self.settings_to_num(channel, freq, ampl)
        return num

    def artiq_convert_dds(self, dds_seq):
        #todo: get parameters for the ramp
        return dds_single_seq, dds_ramp_seq

    # needed for backwards compatibility
    def _intToBuf_coherent(self, num):
        '''
        takes the integer representing the setting and returns the buffer string for dds programming
        '''

        freq_num = (num % 2**64)  # change according to the new DDS which supports 64 bit tuning of the frequency. Used to be #freq_num = (num % 2**32)*2**32
        b = bytearray(8)          # initialize the byte array to sent to the pusler later
        for i in range(8):
            b[i]=(freq_num//(2**(i*8)))%256
            #print i, "=", (freq_num//(2**(i*8)))%256

        #phase
        phase_num = (num // 2**80)%(2**16)
        phase = bytearray(2)
        phase[0] = phase_num%256
        phase[1] = (phase_num//256)%256


        ### amplitude
        ampl_num = (num // 2**64)%(2**16)
        amp = bytearray(2)
        amp[0] = ampl_num%256
        amp[1] = (ampl_num//256)%256

        ### ramp rate. 16 bit tunability from roughly 116 Hz/ms to 7.5 MHz/ms
        ramp_rate = (num // 2**96)%(2**16)
        ramp = bytearray(2)
        ramp[0] = ramp_rate%256
        ramp[1] = (ramp_rate//256)%256

        ##  amplitude ramp rate
        amp_ramp_rate = (num // 2**112)%(2**16)
        #print "amp_ramp is" , amp_ramp_rate
        amp_ramp = bytearray(2)
        amp_ramp[0] = amp_ramp_rate%256
        amp_ramp[1] = (amp_ramp_rate//256)%256

        ##a = bytearray.fromhex(u'0000') + amp + bytearray.fromhex(u'0000 0000')
        a = phase + amp + amp_ramp + ramp

        ans = a + b
        return ans

