"""
### BEGIN NODE INFO
[info]
name = ARTIQ Server
version = 1.0
description = Pulser using the ARTIQ box. Backwards compatible with old pulse sequences and experiments.
instancename = ARTIQ Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

#labrad imports
from labrad.server import LabradServer, setting, Signal
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred
from twisted.internet.threads import deferToThread

#artiq imports
from .artiq_api import ARTIQ_api
from artiq.experiment import *
from artiq.master.databases import DeviceDB
from artiq.master.worker_db import DeviceManager
from sipyco.pc_rpc import Client
from sipyco.sync_struct import Subscriber

#function imports
import numpy as np

class ARTIQ_Server(LabradServer):
    """ARTIQ box server."""
    name = 'ARTIQ Server'
    regKey = 'ARTIQ_Server'

    def __init__(self):
        self.api = ARTIQ_api()
        self.ddb_filepath = 'C:\\Users\\EGGS1\\Documents\\ARTIQ\\artiq-master\\device_db.py'
        self.devices = DeviceDB(self.ddb_filepath)
        self.device_manager = DeviceManager(self.devices)
        LabradServer.__init__(self)

    @inlineCallbacks
    def initServer(self):
        yield self._setDevices()
        yield self._setClients()
        yield self._setVariables()
        self.listeners = set()

    def _setDevices(self):
        """Sets hardware names"""
        #set hardware
        device_db = self.devices.get_device_db()
        self.ttlin_list = list()
        self.ttlout_list = list()
        self.dds_list = list()
        self.dac_list = list()
        self.adc_list = list()
        #assign names and devices
        for name, params in device_db.items():
            #only get devices with named class
            if 'class' not in params:
                continue
            #set device as attribute
            devicetype = params['class']
            if devicetype == 'TTLInOut':
                self.ttlin_list.append(name)
            elif devicetype == 'TTLOut':
                if 'pmt' in name:
                    self.pmt_list.append(name)
                elif 'linetrigger' in name:
                    self.linetrigger_list.append(name)
                elif 'urukul' not in name:
                    self.ttlout_list.append(name)
            elif devicetype == ('AD9910' or 'AD9912'):
                self.dds_list.append(name)
            elif devicetype == 'CPLD':
                self.urukul_list.append(name)

    def _setClients(self):
        """Sets clients to ARTIQ master."""
        self.scheduler = Client('::1', 3251, 'master_schedule')
        self.datasets = Client('::1', 3251, 'master_dataset_db')

    def _setVariables(self):
        """Sets variables."""
        self.inCommunication = DeferredLock()

        #pulse sequencer variables
        self.ps_filename = 'C:\\Users\\EGGS1\\Documents\\Code\\EGGS_labrad\\lib\\servers\\pulser\\run_ps.py'
        self.ps_rid = None

        #conversions
        from artiq.coredevice.ad9910 impo
        self.seconds_to_mu = self.api.core.seconds_to_mu
        self.amplitude_to_asf = amplitude_to_asf
        self.frequency_to_ftw = self.api.dds_list[0].frequency_to_ftw
        self.turns_to_pow = self.api.dds_list[0].turns_to_pow
        self.dbm_to_fampl = lambda dbm: 10**(float(dbm/10))
        self.voltage_to_mu = self.#todo: finish for zotino

    # Core
    @setting(21, "Get Devices", returns='')
    def getDevices(self):
        return self.devices.get_device_db()

    #Pulse sequencing
    @setting(111, "Run Experiment", path='s', maxruns = 'i', returns='')
    def runExperiment(self, c, path, maxruns = 1):
        """
        Run the experiment a given number of times.
        Argument:
            path    (string): the filepath to the ARTIQ experiment.
            maxruns (int)   : the number of times to run the experiment
        """
        #set pipeline, priority, and expid
        ps_pipeline = 'PS'
        ps_priority = 1
        ps_expid = {'log_level': 30,
                    'file': path,
                    'class_name': None,
                    'arguments': {'maxRuns': maxruns,
                                  'linetrigger_enabled': self.linetrigger_enabled,
                                  'linetrigger_delay_us': self.linetrigger_delay,
                                  'linetrigger_ttl_name': self.linetrigger_ttl}}

        #run sequence then wait for experiment to submit
        yield self.inCommunication.acquire()
        self.ps_rid = yield deferToThread(self.scheduler.submit, pipeline_name = ps_pipeline, expid = ps_expid, priority = ps_priority)
        self.inCommunication.release()

    @setting(112, "Stop Experiment", returns='')
    def stopSequence(self, c):
        """
        Stops any currently running sequence.
        """
        #check that an experiment is currently running
        if self.ps_rid not in self.scheduler.get_status().keys(): raise Exception('No experiment currently running')
        yield self.inCommunication.acquire()
        yield deferToThread(self.scheduler.delete, self.ps_rid)
        self.ps_rid = None
        #todo: make resetting of ps_rid contingent on defertothread completion
        self.inCommunication.release()

    @setting(113, "Runs Completed", returns='i')
    def runsCompleted(self, c):
        """
        Check how many iterations of the experiment have been completed.
        """
        completed_runs = yield self.datasets.get('numRuns')
        returnValue(completed_runs)

    #TTLs
    @setting(211, 'Get TTL', returns = '*s')
    def getTTL(self, c):
        """
        Returns all available TTL channels
        """
        return self.ttlout_list

    @setting(221, "Set TTL", ttl_name = 'i', state = 'b', returns='')
    def setTTL(self, c, ttl_name, state):
        """
        Manually set a TTL to the given state.
        Arguments:
            ttlname (str)   : name of the ttl
            state   (bool)  : ttl power state
        """
        ttl_channel = self.ttlout_list[ttl_name]
        self.inCommunication.acquire()
        yield deferToThread(self.api.setTTL, ttl_channel, state)
        self.inCommunication.release()

    #DDS functions
    @setting(311, "Get DDS", returns = '*s')
    def getDDS(self, c):
        """get the list of available channels"""
        return self.dds_list

    @setting(321, "Initialize DDS", returns = '')
    def initializeDDS(self, c):
        """
        Resets/initializes the DDSs
        """
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.initializeDDS)
        self.inCommunication.release()

    @setting(322, "Toggle DDS", dds_name = 's', state = 'b', returns='')
    def toggleDDS(self, c, dds_name, state):
        """
        Manually toggle a DDS via the RF switch
        Arguments:
            ddsname (str)   : the name of the dds
            state   (bool)  : power state
        """
        dds_channel = self.ddsDict[dds_name].address
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.toggleDDS, dds_channel, state, profile)
        self.inCommunication.release()

    @setting(323, "Set DDS Frequency", dds_name='s', freq='v', profile='i', returns='')
    def setDDSFreq(self, c, dds_name, freq, profile=None):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            ddsname (str)   : the name of the dds
            freq    (float) : frequency (in Hz)
            profile (int)   : the DDS profile to set & change to
        """
        dds_channel = self.ddsDict[dds_name].address
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setDDS, dds_channel, params, profile)
        self.inCommunication.release()

    @setting(324, "Set DDS Amplitude", dds_name='s', ampl='v', profile='i', returns='')
    def setDDSAmpl(self, c, dds_name, ampl, profile=None):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            ddsname (str)   : the name of the dds
            ampl    (float) : amplitude (in V)
            profile (int)   : the DDS profile to set & change to
        """
        dds_channel = self.ddsDict[dds_name].address
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setDDS, dds_channel, params, profile)
        self.inCommunication.release()

    @setting(325, "Set DDS Phase", dds_name='s', freq='v', profile='i', returns='')
    def setDDSPhase(self, c, dds_name, phase, profile = None):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            ddsname (str)   : the name of the dds
            phase   (float) : phase (in radians/2pi)
            profile (int)   : the DDS profile to set & change to
        """
        dds_channel = self.ddsDict[dds_name].address
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setDDS, dds_channel, params, profile)
        self.inCommunication.release()

    @setting(326, "Set DDS Attenuation", dds_name='s', att='v', profile='i', returns='')
    def setDDSAtt(self, c, dds_name, att, profile=None):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            ddsname (str)   : the name of the dds
            att     (float) : attenuation (in dBm)
            profile (int)   : the DDS profile to set & change to
        """
        dds_channel = self.ddsDict[dds_name].address
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setDDS, dds_channel, params, profile)
        self.inCommunication.release()

    @setting(327, "Set DDS Profile", dds_name='s', profile='i', returns='')
    def setDDSProf(self, c, dds_name, profile = None):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            ddsname (str)   : the name of the dds
            profile (int)   : the DDS profile to set & change to
        """
        dds_channel = self.ddsDict[dds_name].address
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setDDS, dds_channel, params, profile)
        self.inCommunication.release()

    #DAC
    @setting(411, "Set DAC", channel='i', voltage='v', returns='')
    def setDAC(self, c, freq = None, ampl = None, phase = None, profile = None):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            channel (int)   : the channel to set
            ddsname (str)   : the desired voltage (in V)
        """
        #todo: get mu
        yield self.inCommunication.acquire()
        yield deferToThread(self.api.setDAC, channel, voltage)
        self.inCommunication.release()

    #Sampler
    @setting(511, "")
    def

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

if __name__ == '__main__':
    from labrad import util
    util.runServer(ARTIQ_Server())