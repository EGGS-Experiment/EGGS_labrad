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

#labrad and artiq imports
from labrad.server import LabradServer, setting, Signal

#async imports
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread

#function imports
import numpy as np
from time import sleep

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

    @setting(1, "Record Sequence", returns = '')
    def record(self, c):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        self.inCommunication.acquire()
        yield deferToThread(self.api.record)
        self.inCommunication.release()

    @setting(2, "Run Sequence", numruns = 'i', returns='')
    def runSequence(self, c, numruns):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        #set pipeline, priority, and expid
        ps_pipeline = 'PS'
        ps_expid = {'log_level': 30, 'file': self.ps_filename, 'class_name': None, 'arguments': {}}
        ps_priority = 1
        #get current RID
        self.ps_rid = self.scheduler.rid + 1
        #run sequence then wait for experiment to submit
        self.inCommunication.acquire()
        yield deferToThread(self.scheduler.submit, pipeline_name = ps_pipeline, expid = ps_expid, priority = ps_priority)
        self.inCommunication.release()

    @setting(3, "Stop Sequence", returns='')
    def stopSequence(self, c):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        if not self.ps_rid:
            raise Exception('No pulse sequence currently running')
        self.inCommunication.acquire()
        yield deferToThread(self.scheduler.delete, self.ps_rid)
        self.inCommunication.release()
        self.ps_rid = None


