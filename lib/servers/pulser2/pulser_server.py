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
#from pulser_legacy import Pulser_legacy
from artiq.experiment import *

#async imports
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread

#function imports
import numpy as np
from artiq.coredevice.ad9910 import AD9910

class Pulser_server(LabradServer):

    name = 'ARTIQ Pulser'
    regKey = 'ARTIQ_Pulser'

    onSwitch = Signal(611051, 'signal: switch toggled', '(ss)')

    def __init__(self, api):
        self.api = api
        LabradServer.__init__(self)

    @inlineCallbacks
    def initServer(self):
        yield self._setVariables()

    def _setVariables(self):
        self.scheduler = self.api.scheduler
        self.inCommunication = DeferredLock()

        #pulse sequencer variables
        self.ps_filename = 'C:\\Users\\EGGS1\\Documents\\Code\\EGGS_labrad\\lib\\servers\\pulser2\\run_ps.py'
        self.ps_rid = None
        self.ps_programmed = False

        #pmt variables
        self.pmt_mode = 0
        self.pmt_interval = 0 * us

        #linetrigger variables
        self.linetrigger_enabled = False
        self.linetrigger_delay = 0 * ms
            #todo: change in config
        self.linetrigger_ttl = 'ttl0'

        #conversions
        self.seconds_to_mu = self.api.core.seconds_to_mu
        # self.amplitude_to_asf = self.api.dds_list[0].amplitude_to_asf
        # self.frequency_to_ftw = self.api.dds_list[0].frequency_to_ftw
        # self.turns_to_pow = self.api.dds_list[0].turns_to_pow
        # self.dbm_to_fampl = lambda dbm: 10**(float(dbm/10))

    #Pulse sequencing
    @setting(0, "New Sequence", returns = '')
    def newSequence(self, c):
        """
        Create New Pulse Sequence
        """
        c['sequence'] = Sequence(self)

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
        self.ps_programmed = True

        # sequence = c.get('sequence')
        # if not sequence:
        #     raise Exception("Please create new sequence first")
        # self.programmed_sequence = sequence
        # #todo: calculate number of PMT recordings need
        # #todo: ensure num doesn't exceed pmt array length
        # _, ttl = sequence.progRepresentation()
        # if dds is None:
        #     dds = {}
        # #use ddsSettinglist since that is more ARTIQ-friendly
        # dds_single, dds_ramp = self._artiqParseDDS(sequence.ddsSettingList)
        # yield self.inCommunication.acquire()
        # yield deferToThread(self.api.programBoard, ttl, dds_single, dds_ramp)
        # self.inCommunication.release()
        # self.isProgrammed = True

    @setting(2, "Run Sequence", numruns = 'i', returns='')
    def runSequence(self, c, numruns):
        """
        Run the pulse sequence a given number of times.
        Argument:
            numruns (int): number of times to run the pulse sequence
        """
        if not self.ps_programmed:
            raise Exception("No Programmed Sequence")
        #set pipeline, priority, and expid
        ps_pipeline = 'PS'
        ps_priority = 1
        ps_expid = {'log_level': 30,
                    'file': self.ps_filename,
                    'class_name': None,
                    'arguments': {'maxRuns': numruns,
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
        if self.ps_rid not in self.scheduler.get_status().keys():
            raise Exception('No pulse sequence currently running')
        yield self.inCommunication.acquire()
        yield deferToThread(self.scheduler.delete, self.ps_rid)
        self.ps_rid = None
        self.inCommunication.release()

    @setting(4, "Erase Sequence", sequencename = 's', returns='')
    def eraseSequence(self, c, sequencename = None):
        """
        Erases the given pulse sequence from memory.
        Arguments:
            sequencename (str): the sequence to erase
        """
        if not self.ps_programmed:
            raise Exception("No Programmed Sequence")
        if not sequencename:
            sequencename = 'default'
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.eraseSequence, sequencename)
        self.ps_programmed = False
        self.ps_rid = None
        self.inCommunication.release()

    @setting(5, "Runs Completed", returns='i')
    def runsCompleted(self, c):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        completed_runs = yield self.api.runsCompleted()
        returnValue(completed_runs)

    #TTL functions
    @setting(11, "Set TTL", ttlname = 'i', state = 'b', returns='')
    def setTTL(self, c, ttlname, state):
        """
        Switches a TTL to the given state.
        Arguments:
            ttlname (str)   : name of the ttl
            state   (bool)  : ttl power state
        """
        self.inCommunication.acquire()
        yield deferToThread(self.api.setTTL, ttlname, state)
        self.inCommunication.release()

    #DDS functions
    @setting(21, "Initialize DDS", returns = '')
    def initializeDDS(self, c):
        """
        Reprograms the DDS chip to its initial state
        """
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.initializeDDS)
        self.inCommunication.release()

    @setting(22, "Set DDS", ddsname = 's', freq = 'v[MHz]', ampl = 'v[dBm]', phase = 'v', profile = 'i', returns='')
    def setDDS(self, c, ddsname, freq = None, ampl = None, phase = None, profile = None):
        """
        Sets a DDS to the given parameters.
        Arguments:
            ddsname (str)   : the name of the dds
            state   (bool)  : power state
            freq    (float) : frequency (in Hz)
            ampl    (float) : amplitude (in dBm)
            phase   (float) : phase     (in radians)
            profile (int)   : the DDS profile to set & change to
        """
        #todo:
        #tdodo: convert
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setDDS, ddsnum, params, profile)
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
        if mode == 'Normal':
            yield self.inCommunication.acquire()
            yield deferToThread(self.api.setPMTCountInterval, mu_time)
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