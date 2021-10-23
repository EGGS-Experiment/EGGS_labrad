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

    def __init__(self, api):
        self.api = api
        self.scheduler = self.api.scheduler
        #start
        LabradServer.__init__(self)

    #@inlineCallbacks
    def initServer(self):
        self.ps_filename = 'C:\\Users\\EGGS1\\Documents\\Code\\EGGS_labrad\\lib\\servers\\pulser2\\run_ps.py'

    @setting(1, "Record", returns = '')
    def Record(self, c):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        yield deferToThread(self.api._record)

    @setting(2, "Run Sequence", numruns = 'i', returns='')
    def runSequence(self, c, numruns):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        #get pulser API status
        api_status = None
        for _, exp_status in self.scheduler.get_status().items():
            if exp_status['pipeline'] == 'main':
                api_status = exp_status
        #pulse sequence runs in same pipeline as API
        ps_pipeline = api_status['pipeline']
        #set expid for pulse sequence and set priority greater than API
        ps_expid = api_status['expid']
        ps_expid['file'] = self.ps_filename
        ps_priority = api_status['priority'] + 1
        #run sequence then wait for experiment to submit
        self.scheduler.submit(pipeline_name = ps_pipeline, expid = ps_expid, priority = ps_priority)
        while not self.scheduler.check_pause():
            sleep(0.2)
        yield self.api._disconnect()

    @setting(3, "Stop Sequence", returns='')
    def stopSequence(self, c):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        yield deferToThread(self.api._stopSequence)


