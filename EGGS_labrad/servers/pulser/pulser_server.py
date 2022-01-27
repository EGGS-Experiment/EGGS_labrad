"""
### BEGIN NODE INFO
[info]
name = ARTIQ Pulser
version = 1.0
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

#labrad and artiq imports
from labrad.server import LabradServer, setting, Signal
from labrad.units import WithUnit
from artiq.experiment import *
from sequence import Sequence

#async imports
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread

#function imports
import numpy as np
#todo: make sure all units are right
class Pulser_server(LabradServer):
    """Pulser using the ARTIQ box. Backwards compatible with old pulse sequences and experiments."""
    name = 'ARTIQ Pulser'
    regKey = 'ARTIQ_Pulser'

    onSwitch = Signal(611051, 'signal: switch toggled', '(ss)')
    on_dds_param = Signal(142006, 'signal: new dds parameter', '(ssv)')
    on_line_trigger_param = Signal(142007, 'signal: new line trigger parameter', '(bv)')

    def __init__(self, api):
        self.api = api
        LabradServer.__init__(self)

    @inlineCallbacks
    def initServer(self):
        yield self._setVariables()
        self.listeners = set()

    def _setVariables(self):
        self.scheduler = self.api.scheduler
        self.inCommunication = DeferredLock()

        #pulse sequencer variables
        self.ps_filename = 'C:\\Users\\EGGS1\\Documents\\Code\\EGGS_labrad\\EGGS_labrad\\servers\\pulser\\run_ps.py'
        self.ps_rid = None
        self.ps_is_programmed = False
        self.ps_programmed_sequence = None

        #TTL variables
        self.ttlDict = hardwareConfiguration.channelDict
        #self.timeResolution = float(hardwareConfiguration.timeResolution)
        #self.sequenceTimeRange = hardwareConfiguration.sequenceTimeRange

        #DDS variables
        self.ddsDict = hardwareConfiguration.ddsDict

        #pmt variables
        self.pmt_mode = ''
        #self.pmt_mode = hardwareConfiguration.collectionTime
        self.pmt_interval = 0 * us
        #self.pmt_interval = hardwareConfiguration.collectionMode
        #self.pmt_interval_range = hardwareConfiguration.collectionTimeRange

        #linetrigger variables
        self.linetrigger_enabled = False
        self.linetrigger_delay = 0 * ms
            #todo: change in config
        self.linetrigger_ttl = 'ttl0'
        self.linetrigger_limits = [WithUnit(v, 'us') for v in hardwareConfiguration.lineTriggerLimits]

        #conversions
        self.seconds_to_mu = self.api.core.seconds_to_mu
            #get DDS conversions only if there are DDSs
        if len(self.api.dds_list) > 0:
            self.amplitude_to_asf = self.api.dds_list[0].amplitude_to_asf
            self.frequency_to_ftw = self.api.dds_list[0].frequency_to_ftw
            self.turns_to_pow = self.api.dds_list[0].turns_to_pow
            self.dbm_to_fampl = lambda dbm: 10**(float(dbm/10))
        # todo: get io update alignment

    #Pulse sequencing
    @setting(0, "New Sequence", returns = '')
    def newSequence(self, c):
        """
        Create New Pulse Sequence
        """
        c['sequence'] = Sequence()

    @setting(1, "Record Sequence", sequencename = 's', returns = '')
    def record(self, c, sequencename = None):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        if not sequencename:
            sequencename = 'default'
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.record, sequencename)
        self.inCommunication.release()
        #todo: fix programmed sequence
        self.ps_is_programmed = True

    def _record(self, sequencename = None):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        #set sequencename to default if not specified
        if not sequencename:
            sequencename = 'default'

        #get sequence and check to see we have a sequence
        sequence = c.get('sequence')
        if not sequence: raise Exception("Please create new sequence first")
        self.ps_programmed_sequence = sequence
        ttl_seq, dds_seq = self.sequence.progRepresentation()

        #send to API
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.record, ttl_seq, dds_seq, sequencename)
        self.inCommunication.release()

        #set global variables
        self.ps_is_programmed = True
        self.ps_programmed_sequence = sequence

    @setting(2, "Run Sequence", maxruns = 'i', returns='')
    def runSequence(self, c, maxruns):
        """
        Run the pulse sequence a given number of times.
        Argument:
            numruns (int): number of times to run the pulse sequence
        """
        #check to see if a sequence has been programmed
        if not self.ps_is_programmed: raise Exception("No Programmed Sequence")

        #set pipeline, priority, and expid
        ps_pipeline = 'PS'
        ps_priority = 1
        ps_expid = {'log_level': 30,
                    'file': self.ps_filename,
                    'class_name': None,
                    'arguments': {'maxRuns': maxruns,
                                  'linetrigger_enabled': self.linetrigger_enabled,
                                  'linetrigger_delay_us': self.linetrigger_delay,
                                  'linetrigger_ttl_name': self.linetrigger_ttl}}

        #run sequence then wait for experiment to submit
        yield self.inCommunication.acquire()
        self.ps_rid = yield deferToThread(self.scheduler.submit, pipeline_name = ps_pipeline, expid = ps_expid, priority = ps_priority)
        self.inCommunication.release()

    @setting(3, "Stop Sequence", returns='')
    def stopSequence(self, c):
        """
        Stops any currently running sequence.
        """
        #see if pulse sequence is currently running
        if self.ps_rid not in self.scheduler.get_status().keys(): raise Exception('No pulse sequence currently running')
        yield self.inCommunication.acquire()
        yield deferToThread(self.scheduler.delete, self.ps_rid)
        self.ps_rid = None
        #todo: make resetting of ps_rid contingent on defertothread completion
        self.inCommunication.release()

    @setting(4, "Erase Sequence", sequencename = 's', returns='')
    def eraseSequence(self, c, sequencename = None):
        """
        Erases the given pulse sequence from memory.
        Arguments:
            sequencename (str): the sequence to erase
        """
        #check to see a sequence has been programmed
        if not self.ps_programmed_sequence: raise Exception("No Programmed Sequence")
        #set sequence name to default if not specified
        if not sequencename: sequencename = 'default'
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.eraseSequence, sequencename)
        self.ps_programmed_sequence = None
        self.ps_rid = None
        self.inCommunication.release()

    @setting(5, "Runs Completed", returns='i')
    def runsCompleted(self, c):
        """
        Check how many pulse sequences have been completed.
        """
        completed_runs = yield self.api.runsCompleted()
        returnValue(completed_runs)

    #TTL functions
    @setting(111, 'Add TTL Pulse', ttl_name = 's', start = 'v[s]', duration = 'v[s]')
    def addTTLPulse(self, c, ttl_name, start, duration):
        """
        Add a TTL Pulse to the sequence, times are in seconds
        """
        sequence = c.get('sequence')

        #check to see that a sequence exists
        if not sequence:
            raise Exception("Please create new sequence first")
        #check that channel exists
        if ttl_name not in self.ttlDict.keys():
            raise Exception("Unknown Channel {}".format(ttl_name))

        #convert
        ttl_channel = self.ttlDict[ttl_name].channelnumber
        start = start['s']
        duration = duration['s']

        # check that pulse is within time limit
        if not ((self.sequenceTimeRange[0] <= start <= self.sequenceTimeRange[1]) and
                 (self.sequenceTimeRange[0] <= start + duration <= self.sequenceTimeRange[1])):
            raise Exception("Time boundaries are out of range")
            #check to see that pulse is not too short
        if not duration >= self.timeResolution:
            raise Exception("Incorrect duration")

        sequence.addPulse(ttl_channel, start, duration)

    @setting(112, 'Add TTL Pulses', pulses = '*(sv[s]v[s])')
    def addTTLPulses(self, c, pulses):
        """
        Add multiple TTL Pulses to the sequence, times are in seconds.
        The pulses are a list in the same format as 'add ttl pulse'.
        """
        for pulse in pulses:
            ttl_name = pulse[0]
            start = pulse[1]
            duration = pulse[2]
            yield self.addTTLPulse(c, ttl_name, start, duration)

    @setting(113, "Extend Sequence Length", end_time = 'v[s]')
    def extendSequenceLength(self, c, end_time):
        """
        Extends the TTL pulse sequence to the given time.
        """
        sequence = c.get('sequence')
        if not (self.sequenceTimeRange[0] <= end_time['s'] <= self.sequenceTimeRange[1]):
            raise Exception("Time boundaries are out of range")
        if not sequence:
            raise Exception("Please create new sequence first")
        sequence.extendSequenceLength(end_time['s'])

    @setting(114, "Human Readable TTL", getProgrammed = 'b', returns = '*2s')
    def humanReadableTTL(self, c, getProgrammed = None):
        """
        Gets the TTL sequence in human-readable form.
        Args:
            getProgrammed (bool): False/None(default) to get the sequence added by current context,
                              True to get the last programmed sequence
        Returns:
            a readable form of TTL sequence
        """
        sequence = c.get('sequence')

        #get programmed sequence
        if getProgrammed: sequence = self.ps_programmed_sequence
        #check whether a sequence exists
        if not sequence: raise Exception("Please create new sequence first")
        ttl, _ = sequence.humanRepresentation()
        return ttl.tolist()

    @setting(115, "Human Readable DDS", getProgrammed = 'b', returns = '*(svv)')
    def humanReadableDDS(self, c, getProgrammed = None):
        """
        Gets the DDS sequence in human-readable form.
        Args:
            getProgrammed (bool): False/None(default) to get the sequence added by current context,
                              True to get the last programmed sequence
        Returns:
            a readable form of DDS sequence
        """
        sequence = c.get('sequence')
        #get programmed sequence
        if getProgrammed: sequence = self.ps_programmed_sequence
        #check whether a sequence exists
        _, dds = sequence.humanRepresentation()
        return dds

    @setting(116, 'Get TTLs', returns = '*(sw)')
    def getChannels(self, c):
        """
        Returns all available TTL channels and their corresponding hardware numbers
        """
        keys = self.ttlDict.keys()
        numbers = [self.ttlDict[key].channelnumber for key in keys]
        return zip(keys, numbers)

    @setting(11, "Set TTL", ttl_name = 'i', state = 'b', returns='')
    def setTTL(self, c, ttl_name, state):
        """
        Manually set a TTL to the given state.
        Arguments:
            ttlname (str)   : name of the ttl
            state   (bool)  : ttl power state
        """
        ttl_channel = self.ttlDict[ttl_name].channelnumber
        self.inCommunication.acquire()
        yield deferToThread(self.api.setTTL, ttl_channel, state)
        self.inCommunication.release()

    #DDS functions
    @setting(211, "Get DDS Channels", returns = '*s')
    def getDDSChannels(self, c):
        """get the list of available channels"""
        return self.ddsDict.keys()

    @setting(212, 'Add DDS Pulses', values = ['*(sv[s]v[s]v[MHz]v[dBm]v[deg]v[MHz]v[dB])'])
    def addDDSPulses(self, c, values):
        '''
        Add DDS pulses to sequence.
        Input in the form of a list [(name, start, duration, frequency, amplitude, phase, ramp_rate, amp_ramp_rate)]
        '''
        sequence = c.get('sequence')
        #check whether a sequence exists
        if not sequence: raise Exception("Please create new sequence first")
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

            #strip units
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

            #convert parameters
            _asf = self.dbm_to_fampl(ampl)
            _asf = self.amplitude_to_asf(_asf)
            _ftw = self.frequency_to_ftw(freq * 1e6)
            _pow = self.turns_to_pow(phase / (2*np.pi))
            num_ARTIQ = (_asf, _ftw, _pow)
            num_off_ARTIQ = (0, 0, 0)

            #check time is in range
                #note < sign, because start can not be 0.
                #this would overwrite the 0 position of the ram, and cause the dds to change before pulse sequence is launched
            if not self.sequenceTimeRange[0] < start <= self.sequenceTimeRange[1]:
                raise Exception("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start))
            if not self.sequenceTimeRange[0] < start + dur <= self.sequenceTimeRange[1]:
                raise Exception("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start + dur))

            #ignore zero-length pulses
            if not dur == 0:
                #get the DDS channel number
                dds_channel = channel.address
                sequence.addDDS(dds_channel, start, num_ARTIQ, 'start')
                sequence.addDDS(dds_channel, start + dur, num_off_ARTIQ, 'stop')

    @setting(21, "Initialize DDS", returns = '')
    def initializeDDS(self, c):
        """
        Resets/initializes the DDSs
        """
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.initializeDDS)
        self.inCommunication.release()

    @setting(22, "Toggle DDS", dds_name = 's', state = 'b', returns='')
    def toggleDDS(self, c, dds_name, state, profile = 0):
        """
        Manually toggle a DDS
        Arguments:
            ddsname (str)   : the name of the dds
            state   (bool)  : power state
        """
        dds_channel = self.ddsDict[dds_name].address
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.toggleDDS, dds_channel, state, profile)
        self.inCommunication.release()

    @setting(23, "Set DDS", dds_name = 's', freq = 'v[MHz]', ampl = 'v[dBm]', phase = 'v', profile = 'i', returns='')
    def setDDS(self, c, dds_name, freq = None, ampl = None, phase = None, profile = None):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            ddsname (str)   : the name of the dds
            freq    (float) : frequency (in Hz)
            ampl    (float) : amplitude (in dBm)
            phase   (float) : phase     (in radians)
            profile (int)   : the DDS profile to set & change to
        """
        dds_channel = self.ddsDict[dds_name].address
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setDDS, dds_channel, params, profile)
        self.inCommunication.release()

    #PMT functions
    @setting(31, 'PMT Mode', mode = 's', returns = 's')
    def pmtMode(self, c, mode = None):
        """
        Set the counting mode, either 'Normal' or 'Differential'
        In 'Normal', the FPGA automatically sends the counts with a preset frequency
        In 'Differential', the FPGA uses triggers the pulse sequence
        frequency and to know when the repumping light is switched on or off.
        """
        if mode not in [0, 1]:
            raise Exception('Incorrect Mode')
        self.pmt_mode = mode
        self.pmt_interval = self.collectionTime[mode] * us
        yield self.inCommunication.acquire()
        if mode == 'Normal':
            #set the mode on the device and set update time for normal mode
            yield deferToThread(self.api.setPMTCountInterval, countInterval)
        elif mode == 'Differential':
            yield deferToThread(self.api.setMode, 1)
        self.inCommunication.release()
        return self.pmt_mode

    @setting(32, 'PMT Time', mode = 's', new_time = 'v', returns = '')
    def pmtTime(self, c, mode, new_time = None):
        """
        Set time for each PMT bin in a given mode
        Arguments:
            new_time    (float) : PMT bin time in microseconds
            mode        (str)   : PMT mode
        Returns:
            (float) : PMT bin time in microseconds
        """
        if not self.collectionTimeRange[0] <= new_time <= self.collectionTimeRange[1]:
            raise Exception('Invalid collection time')
        if mode not in self.collectionTime.keys():
            raise Exception("Incorrect mode")

        self.collectionTime[mode] = new_time
        new_time_mu = self.seconds_to_mu(new_time * mu)
        if mode == 'Normal':
            yield self.inCommunication.acquire()
            yield deferToThread(self.api.setPMTCountInterval, new_time_mu)
            self.inCommunication.release()

    @setting(35, 'Get Readout Counts', returns = '*v')
    def getReadoutCounts(self, c):
        yield self.inCommunication.acquire()
        countlist = yield deferToThread(self.api.getReadoutCounts)
        self.inCommunication.release()
        returnValue(countlist)

    #Line Trigger functions
    @setting(41, 'Linetrigger State', enable='b', returns='b')
    def linetrigger_state(self, c, enable=None):
        """Enable or disable the line trigger"""
        if enable is not None:
            self.linetrigger_enabled = enable
            #self.notifyOtherListeners(c, (self.linetrigger_enabled, self.linetrigger_duration), self.on_line_trigger_param)
        return self.linetrigger_enabled

    @setting(42, "Linetrigger Delay", duration='v[us]', returns='v[us]')
    def linetrigger_delay(self, c, duration=None):
        """Get/set the line trigger offset_duration"""
        if duration is not None:
            self.linetrigger_duration = duration['us']
            #self.notifyOtherListeners(c, (self.linetrigger_enabled, self.linetrigger_duration), self.on_line_trigger_param)
        return WithUnit(self.linetrigger_duration, 'us')

    @setting(43, "Get Line Trigger Limits", returns='*v[us]')
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

    #Helper functions
    def _checkRange(self, t, channel, val):
        if t == 'amplitude':
            r = channel.allowedamplrange
        elif t == 'frequency':
            r = channel.allowedfreqrange
        if not r[0] <= val <= r[1]:
            raise Exception("channel {0} : {1} of {2} is outside the allowed range".format(channel.name, t, val))