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

class Pulser_server(LabradServer):

    name = 'ARTIQ Pulser'
    regKey = 'ARTIQ_Pulser'

    def __init__(self, api):
        self.api = api
        self.scheduler = self.api.scheduler
        #start
        LabradServer.__init__(self)

    @inlineCallbacks
    def initServer(self):
        yield deferToThread(self.api._initializeDevices)
        print('ok')

        self.maxRuns = 0


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
        yield deferToThread(self.api._runSequence, numruns)

    @setting(3, "Stop Sequence", returns='')
    def stopSequence(self, c):
        """
        Programs Pulser with the current sequence.
        Saves the current sequence to self.programmed_sequence.
        """
        yield deferToThread(self.api._stopSequence)


