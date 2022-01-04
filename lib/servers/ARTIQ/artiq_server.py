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

# labrad imports
from labrad.server import LabradServer, setting, Signal
from twisted.internet.threads import deferToThread
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred

# artiq imports
from artiq_api import ARTIQ_api
from artiq.experiment import *
from artiq.master.databases import DeviceDB
from artiq.master.worker_db import DeviceManager
from sipyco.pc_rpc import Client

# device imports
from artiq.coredevice.ad9910 import _AD9910_REG_FTW, _AD9910_REG_ASF, _AD9910_REG_POW
from artiq.coredevice.comm_moninj import CommMonInj, TTLProbe, TTLOverride
from artiq.coredevice.ad53xx import AD53XX_READ_X1A, AD53XX_READ_X1B, AD53XX_READ_OFFSET,\
                                    AD53XX_READ_GAIN, AD53XX_READ_OFS0, AD53XX_READ_OFS1,\
                                    AD53XX_READ_AB0, AD53XX_READ_AB1, AD53XX_READ_AB2, AD53XX_READ_AB3

#     th1.inject(8, TTLOverride.level.value, 1)
#     th1.inject(8, TTLOverride.oe.value, 1)
#     th1.inject(8, TTLOverride.en.value, 1)

#function imports
import numpy as np
import asyncio
import time

TTLSIGNAL_ID = 828176
DACSIGNAL_ID = 828175


class ARTIQ_Server(LabradServer):
    """ARTIQ server."""
    name = 'ARTIQ Server'
    regKey = 'ARTIQ_Server'


    # SIGNALS
    ttlChanged = Signal(TTLSIGNAL_ID, 'signal: ttl changed', '(sib)')
    dacChanged = Signal(DACSIGNAL_ID, 'signal: dac changed', '(ssv)')


    # STARTUP
    def __init__(self):
        self.api = ARTIQ_api()
        self.ddb_filepath = 'C:\\Users\\EGGS1\\Documents\\ARTIQ\\artiq-master\\device_db.py'
        self.devices = DeviceDB(self.ddb_filepath)
        self.device_manager = DeviceManager(self.devices)
        LabradServer.__init__(self)

    @inlineCallbacks
    def initServer(self):
        self.listeners = set()
        yield self._setClients()
        yield self._setVariables()
        yield self._setDevices()
        self.ttlChanged(('ttl99', 0, True))

    #@inlineCallbacks
    def _setClients(self):
        """
        Create clients to ARTIQ master.
        Used to get datasets, submit experiments, and monitor devices.
        """
        self.scheduler = Client('::1', 3251, 'master_schedule')
        self.datasets = Client('::1', 3251, 'master_dataset_db')

    def _setVariables(self):
        """
        Sets ARTIQ-related variables.
        """
        # used to ensure atomicity
        self.inCommunication = DeferredLock()
        # pulse sequencer variables
        self.ps_filename = 'C:\\Users\\EGGS1\\Documents\\Code\\EGGS_labrad\\lib\\servers\\pulser\\run_ps.py'
        self.ps_rid = None
        # conversions
            # dds
        dds_tmp = list(self.api.dds_list.values())[0]
        self.seconds_to_mu = self.api.core.seconds_to_mu
        self.amplitude_to_asf = dds_tmp.amplitude_to_asf
        self.frequency_to_ftw = dds_tmp.frequency_to_ftw
        self.turns_to_pow = dds_tmp.turns_to_pow
        self.dbm_to_fampl = lambda dbm: 10**(float(dbm/10))
            #dac
        from artiq.coredevice.ad53xx import voltage_to_mu #, ad53xx_cmd_read_ch
        self.voltage_to_mu = voltage_to_mu
        # self.dac_read_code = ad53xx_cmd_read_ch
            # sampler
        from artiq.coredevice.sampler import adc_mu_to_volt
        self.adc_mu_to_volt = adc_mu_to_volt

    #@inlineCallbacks
    def _setDevices(self):
        """
        Get the list of devices in the ARTIQ box.
        """
        self.device_db = self.devices.get_device_db()
        self.ttlout_list = list(self.api.ttlout_list.keys())
        self.ttlin_list = list(self.api.ttlin_list.keys())
        self.dds_list = list(self.api.dds_list.keys())

        # needed for moninj
        ttl_all_list = self.ttlout_list + self.ttlin_list
        self.ttl_channel_to_name = {self.device_db[ttl_name]['arguments']['channel']: ttl_name for ttl_name in ttl_all_list}
        self.dac_channel = self.device_db['spi_zotino0']['arguments']['channel']


    # CORE
    @setting(21, "Get Devices", returns='*s')
    def getDevices(self, c):
        """
        Returns a list of ARTIQ devices.
        """
        self.ttlChanged(('ttl99', 0, True))
        return list(self.device_db.keys())

    # PULSE SEQUENCING
    @setting(111, "Run Experiment", path='s', maxruns='i', returns='')
    def runExperiment(self, c, path, maxruns = 1):
        """
        Run the experiment a given number of times.
        Argument:
            path    (string): the filepath to the ARTIQ experiment.
            maxruns (int)   : the number of times to run the experiment
        """
        # set pipeline, priority, and expid
        ps_pipeline = 'PS'
        ps_priority = 1
        ps_expid = {'log_level': 30,
                    'file': path,
                    'class_name': None,
                    'arguments': {'maxRuns': maxruns,
                                  'linetrigger_enabled': self.linetrigger_enabled,
                                  'linetrigger_delay_us': self.linetrigger_delay,
                                  'linetrigger_ttl_name': self.linetrigger_ttl}}

        # run sequence then wait for experiment to submit
        yield self.inCommunication.acquire()
        self.ps_rid = yield deferToThread(self.scheduler.submit, pipeline_name = ps_pipeline, expid = ps_expid, priority = ps_priority)
        self.inCommunication.release()

    @setting(112, "Stop Experiment", returns='')
    def stopSequence(self, c):
        """
        Stops any currently running sequence.
        """
        # check that an experiment is currently running
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


    # TTL
    @setting(211, 'TTL Get', returns='*s')
    def getTTL(self, c):
        """
        Returns all available TTL channels
        """
        return self.ttlout_list

    @setting(221, "TTL Set", ttl_name='s', state='b', returns='')
    def setTTL(self, c, ttl_name, state):
        """
        Manually set a TTL to the given state.
        Arguments:
            ttl_name (str)  : name of the ttl
            state   (bool)  : ttl power state
        """
        if ttl_name not in self.ttlout_list:
            raise Exception('Error: device does not exist.')
        yield self.api.setTTL(ttl_name, state)


    # DDS
    @setting(311, "DDS Get", returns='*s')
    def getDDS(self, c):
        """get the list of available channels"""
        dds_list = yield self.api.dds_list.keys()
        returnValue(list(dds_list))

    @setting(321, "DDS Initialize", dds_name='s', returns='')
    def initializeDDS(self, c, dds_name):
        """
        Resets/initializes the DDSs.
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        yield self.api.initializeDDS(dds_name)

    @setting(322, "DDS Toggle", dds_name='s', state='b', returns='')
    def toggleDDS(self, c, dds_name, state):
        """
        Manually toggle a DDS via the RF switch
        Arguments:
            dds_name    (str)   : the name of the dds
            state       (bool)  : power state
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        yield self.api.toggleDDS(dds_name, state)

    @setting(323, "DDS Waveform", dds_name='s', param='s', param_val='v', returns='')
    def setDDSWav(self, c, dds_name, param, param_val):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            dds_name     (str)  : the name of the dds
            param       (str)   : the parameter to set
            param_val   (float) : the value of the parameter
        """
        #todo: check input
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        if param.lower() in ('frequency', 'f'):
            ftw = yield self.frequency_to_ftw(param_val)
            yield self.api.setDDS(dds_name, 0, ftw)
        elif param.lower() in ('amplitude', 'a'):
            asf = yield self.amplitude_to_asf(param_val)
            yield self.api.setDDS(dds_name, 1, asf)
        elif param.lower() in ('phase', 'p'):
            if param_val >= 1 or pow < 0:
                raise Exception('Error: phase outside bounds of [0,1]')
            pow = yield self.turns_to_pow(param_val)
            yield self.api.setDDS(dds_name, 2, pow)

    @setting(326, "DDS Attenuation", dds_name='s', att='v', units='s', returns='')
    def setDDSAtt(self, c, dds_name, att, units):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            dds_name (str)  : the name of the dds
            att     (float) : attenuation (in dBm)
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        #todo: check input
        att_mu = att
        yield self.api.setDDSAtt(dds_name, att_mu)

    @setting(331, "DDS Read", dds_name='s', addr='i', length='i', returns='i')
    def readDDS(self, c, dds_name, addr, length):
        """
        Read the value of a DDS register.
        Arguments:
            dds_name (str)  : the name of the dds
            addr     (float): the address to read from
            length (int)    : how many bits to read
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        elif length not in (16, 32, 64):
            raise Exception('Invalid read length. Must be one of [16, 32, 64].')
        reg_val = yield self.api.readDDS(dds_name, addr, length)
        returnValue(reg_val)


    # DAC
    @setting(411, "DAC Initialize", returns='')
    def initializeDAC(self, c):
        """
        Manually initialize the DAC.
        """
        yield self.api.initializeDAC()

    @setting(421, "DAC Set", dac_num='i', value='v', units='s', returns='')
    def setDAC(self, c, dac_num, value, units):
        """
        Manually set the voltage of a DAC channel.
        Arguments:
            dac_num (int)   : the DAC channel number
            value   (float) : the value to write to the DAC register
            units   (str)   : the voltage units, either 'mu' or 'v'
        """
        voltage_mu = None
        # check that dac channel is valid
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        if units == 'v':
            voltage_mu = yield self.voltage_to_mu(value)
        elif units == 'mu':
            if (value < 0) or (value > 0xffff):
                raise Exception('Invalid DAC Voltage!')
            voltage_mu = int(value)
        yield self.api.setDAC(dac_num, voltage_mu)

    @setting(422, "DAC Gain", dac_num='i', gain='v', units='s', returns='')
    def setDACGain(self, c, dac_num, gain, units):
        """
        Manually set the gain of a DAC channel.
        Arguments:
            dac_num (int)   : the DAC channel number
            gain    (float) : the DAC channel gain
            units   (str)   : the gain units, either 'mu' or 'dB'
        """
        gain_mu = None
        # only 32 channels per DAC
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        if units == 'todo':
            gain_mu = int(gain * 0xffff) - 1
        elif units == 'mu':
            gain_mu = int(gain)
        # check that gain is valid
        if gain < 0 or gain > 0xffff:
            raise Exception('Error: gain outside bounds of [0,1]')
        yield self.api.setDACGain(dac_num, gain_mu)

    @setting(423, "DAC Offset", dac_num='i', value='v', units='s', returns='')
    def setDACOffset(self, c, dac_num, value, units):
        """
        Manually set the offset voltage of a DAC channel.
        Arguments:
            dac_num (int)   : the DAC channel number
            value   (float) : the value to write to the DAC offset register
            units   (str)   : the voltage units, either 'mu' or 'v'
        """
        voltage_mu = None
        # check that dac channel is valid
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        if units == 'v':
            voltage_mu = yield self.voltage_to_mu(value)
        elif units == 'mu':
            if (value < 0) or (value > 0xffff):
                raise Exception('Invalid DAC Voltage!')
            voltage_mu = int(value)
        yield self.api.setDACOffset(dac_num, voltage_mu)

    @setting(424, "DAC OFS", value='v', units='s', returns='')
    def setDACglobal(self, c, value, units):
        """
        Write to the OFSx registers of the DAC.
        Arguments:
            value   (float) : the value to write to the DAC OFSx register
            units   (str)   : the voltage units, either 'mu' or 'v'
        """
        voltage_mu = None
        if units == 'v':
            voltage_mu = yield self.voltage_to_mu(value)
        elif units == 'mu':
            if (value < 0) or (value > 0x2fff):
                raise Exception('Invalid DAC Voltage!')
            voltage_mu = int(value)
        yield self.api.setDACOffset(voltage_mu)

    @setting(431, "DAC Read", dac_num='i', reg='s', returns='i')
    def readDAC(self, c, dac_num, reg):
        """
        Read the value of a DAC register.
        Arguments:
            dac_num (str)   : the dac channel number
            param   (float) : the register to read from
        """
        AD53XX_registers = {'X1A': AD53XX_READ_X1A, 'X1B': AD53XX_READ_X1B, 'OFF': AD53XX_READ_OFFSET,
                            'GAIN': AD53XX_READ_GAIN, 'OFS0': AD53XX_READ_OFS1, 'OFS1': AD53XX_READ_OFS1,
                            'AB0': AD53XX_READ_AB0, 'AB1': AD53XX_READ_AB1, 'AB2': AD53XX_READ_AB2,
                            'AB3': AD53XX_READ_AB3}

        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        elif reg.lower() not in AD53XX_registers.keys():
            raise Exception('Error: invalid register. Must be one of ', tuple(AD53XX_registers.keys()))
        reg_val = yield self.api.readDAC(dac_num, reg)
        returnValue(reg_val)


    # SAMPLER
    @setting(511, "Sampler Initialize", returns='')
    def initializeSampler(self, c):
        """
        Initialize the Sampler.
        """
        yield self.api.initializeSampler()

    @setting(512, "Sampler Gain", channel='i', gain='i', returns='')
    def setSamplerGain(self, c, channel, gain):
        """
        Set the gain of a sampler channel.
        Arguments:
            channel (int)   : the dac channel number
            gain   (int) : the channel gain. must be either
        """
        if gain not in (1, 10, 100, 1000):
            raise Exception('Error: invalid gain. Must be one of (1, 10, 100, 1000).')
        yield self.api.setSamplerGain(channel, int(np.log10(gain)))

    @setting(521, "Sampler Read", samples='i', returns='*v')
    def readSampler(self, c, samples=None):
        """
        Acquire samples.
        Arguments:
            samples (int)   : the number of samples to read
        Returns:
                    (*float): the samples
        """
        if samples is None:
            samples = 8
        elif samples % 2 == 1:
            raise Exception('Error: number of samples must be even')
        # get channel gains
        gains = yield self.api.getSamplerGains()
        gains = [(gains >> 2 * i) & 0b11 for i in range(8)]
        # acquire samples
        sampleArr = [0] * samples
        yield self.api.readSampler(sampleArr)
        # convert mu to gain
        for i in range(len(sampleArr)):
            self.adc_mu_to_volt(sampleArr[i], gains[i % 8])
        returnValue(sampleArr)


    # CONTEXT
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

    def stopServer(self):
        self.core_moninj_task.cancel()


if __name__ == '__main__':
    from labrad import util
    util.runServer(ARTIQ_Server())

#todo: check that device exists
#todo: block during exp run