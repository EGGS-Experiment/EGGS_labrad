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
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue

# artiq imports
import numpy as np
from artiq_api import ARTIQ_api
DDB_FILEPATH = 'C:\\Users\\EGGS1\\Documents\\Code\\EGGS_labrad\\EGGS_labrad\\config\\device_db.py'

# device imports
from artiq.coredevice.ad53xx import AD53XX_READ_X1A, AD53XX_READ_X1B, AD53XX_READ_OFFSET,\
                                    AD53XX_READ_GAIN, AD53XX_READ_OFS0, AD53XX_READ_OFS1,\
                                    AD53XX_READ_AB0, AD53XX_READ_AB1, AD53XX_READ_AB2, AD53XX_READ_AB3
AD53XX_REGISTERS = {'X1A': AD53XX_READ_X1A, 'X1B': AD53XX_READ_X1B, 'OFF': AD53XX_READ_OFFSET,
                    'GAIN': AD53XX_READ_GAIN, 'OFS0': AD53XX_READ_OFS1, 'OFS1': AD53XX_READ_OFS1,
                    'AB0': AD53XX_READ_AB0, 'AB1': AD53XX_READ_AB1, 'AB2': AD53XX_READ_AB2,
                    'AB3': AD53XX_READ_AB3}


TTLSIGNAL_ID = 828176
DACSIGNAL_ID = 828175
ADCSIGNAL_ID = 828174
EXPSIGNAL_ID = 828173
DDSSIGNAL_ID = 828172


class ARTIQ_Server(LabradServer):
    """
    A bridge between LabRAD and ARTIQ.
    Allows us to easily incorporate ARTIQ into LabRAD for most things.
    Can run without the existence of an ARTIQ Master.
    """

    name = 'ARTIQ Server'
    regKey = 'ARTIQServer'


    # SIGNALS
    ttlChanged = Signal(TTLSIGNAL_ID, 'signal: ttl changed', '(sb)')
    ddsChanged = Signal(DDSSIGNAL_ID, 'signal: dds changed', '(ssv)')
    dacChanged = Signal(DACSIGNAL_ID, 'signal: dac changed', '(ssv)')
    adcUpdated = Signal(ADCSIGNAL_ID, 'signal: adc updated', '(*v)')
    expRunning = Signal(EXPSIGNAL_ID, 'signal: exp running', '(bi)')


    # STARTUP
    @inlineCallbacks
    def initServer(self):
        # initialize ARTIQ API
        self.api = ARTIQ_api(DDB_FILEPATH)
        # set up ARTIQ stuff
        yield self._setClients()
        yield self._setVariables()
        yield self._setDevices()
        # set up context stuff
        self.listeners = set()

    def _setClients(self):
        """
        Create clients to ARTIQ master.
        Used to get datasets, submit experiments, and monitor devices.
        """
        from sipyco.pc_rpc import Client
        try:
            self.scheduler = Client('::1', 3251, 'master_schedule')
            self.datasets = Client('::1', 3251, 'master_dataset_db')
        except Exception as e:
            print('ARTIQ Master not running. Scheduler and datasets disabled.')
        pass

    def _setVariables(self):
        """
        Sets ARTIQ-related variables.
        """
        # used to ensure atomicity
        self.inCommunication = DeferredLock()
        # pulse sequencer variables
        self.ps_rid = None
        # conversions
            # dds
        dds_tmp = list(self.api.dds_list.values())[0]
        self.dds_amplitude_to_asf = dds_tmp.amplitude_to_asf
        self.dds_frequency_to_ftw = dds_tmp.frequency_to_ftw
        self.dds_turns_to_pow = dds_tmp.turns_to_pow
        self.dds_att_to_mu = lambda dbm: 10**(float(dbm/10))
            # dac
        from artiq.coredevice.ad53xx import voltage_to_mu
        self.voltage_to_mu = voltage_to_mu
            # sampler
        from artiq.coredevice.sampler import adc_mu_to_volt
        self.adc_mu_to_volt = adc_mu_to_volt

    def _setDevices(self):
        """
        Get the list of devices in the ARTIQ box.
        """
        self.ttlout_list = list(self.api.ttlout_list.keys())
        self.ttlin_list = list(self.api.ttlin_list.keys())
        self.dds_list = list(self.api.dds_list.keys())
        self.dacType = self.api.dacType


    # CORE
    @setting(21, "Get Devices", returns='*s')
    def getDevices(self, c):
        """
        Returns a list of ARTIQ devices.
        """
        return list(self.api.device_db.keys())

    @setting(31, 'Dataset Get', dataset_name='s', returns='?')
    def getDataset(self, c, dataset_name):
        """
        Returns a dataset.
        Arguments:
            dataset_name    (str)   : the name of the dataset
        Returns:
            the dataset
        """
        return self.datasets.get(dataset_name, archive=False)

    @setting(32, 'Dataset Set', dataset_name='s', values='?')
    def setDataset(self, c, dataset_name):
        """
        Sets the values of a dataset.
        Arguments:
            dataset_name    (str)   : the name of the dataset
            values                  : the values for the dataset
        """
        #return self.datasets.get(dataset_name, archive=False)
        pass


    # PULSE SEQUENCING
    @setting(111, "Run Experiment", path='s', maxruns='i', returns='')
    def runExperiment(self, c, path, maxruns=1):
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
        self.ps_rid = yield deferToThread(self.scheduler.submit, pipeline_name=ps_pipeline, expid=ps_expid, priority=ps_priority)
        self.inCommunication.release()

    @setting(112, "Stop Experiment", returns='')
    def stopSequence(self, c):
        """
        Stops any currently running sequence.
        """
        # check that an experiment is currently running
        if self.ps_rid not in self.scheduler.get_status().keys():
            raise Exception('Error: no experiment currently running')
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

    @setting(121, "DMA Run", handle_name='s', returns='')
    def runDMA(self, c, handle_name):
        """
        Run an experiment from core DMA.
        Arguments:
            handle_name     (str)   : the name of the DMA sequence
        """
        yield self.api.runDMA(handle_name)
        #todo: fix problem when we separately run experiment?


    # TTL
    @setting(211, 'TTL List', returns='*s')
    def listTTL(self, c):
        """
        Lists all available TTL channels.
        Returns:
                (*str)  : a list of all TTL channels.
        """
        return self.ttlout_list + self.ttlin_list

    @setting(221, "TTL Set", ttl_name='s', state=['b', 'i'], returns='')
    def setTTL(self, c, ttl_name, state):
        """
        Manually set a TTL to the given state. TTL can be of classes TTLOut or TTLInOut.
        Arguments:
            ttl_name    (str)           : name of the ttl
            state       [bool, int]     : ttl power state
        """
        if ttl_name not in self.ttlout_list:
            raise Exception('Error: device does not exist.')
        if (type(state) == int) and (state not in (0, 1)):
            raise Exception('Error: invalid state.')
        yield self.api.setTTL(ttl_name, state)
        self.ttlChanged((ttl_name, state))

    @setting(222, "TTL Get", ttl_name='s', returns='b')
    def getTTL(self, c, ttl_name):
        """
        Read the power state of a TTL. TTL must be of class TTLInOut.
        Arguments:
            ttl_name    (str)   : name of the ttl
        Returns:
                        (bool)  : ttl power state
        """
        if ttl_name not in self.ttlin_list:
            raise Exception('Error: device does not exist.')
        state = yield self.api.getTTL(ttl_name)
        returnValue(bool(state))


    # DDS
    @setting(311, "DDS List", returns='*s')
    def listDDS(self, c):
        """
        Get the list of available DDS (AD5372) channels.
        Returns:
            (*str)  : the list of dds names
        """
        dds_list = yield self.api.dds_list.keys()
        returnValue(list(dds_list))

    @setting(321, "DDS Initialize", dds_name='s', returns='')
    def initializeDDS(self, c, dds_name):
        """
        Resets/initializes the DDSs.
        Arguments:
            dds_name    (str)   : the name of the dds
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        yield self.api.initializeDDS(dds_name)

    @setting(322, "DDS Toggle", dds_name='s', state=['b', 'i'], returns='')
    def toggleDDS(self, c, dds_name, state):
        """
        Manually toggle a DDS via the RF switch
        Arguments:
            dds_name    (str)           : the name of the dds
            state       [bool, int]     : power state
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        if (type(state) == int) and (state not in (0, 1)):
            raise Exception('Error: device does not exist.')
        yield self.api.toggleDDS(dds_name, state)

    @setting(323, "DDS Frequency", dds_name='s', freq='v', returns='')
    def setDDSFreq(self, c, dds_name, freq):
        """
        Manually set the frequency of a DDS.
        Arguments:
            dds_name    (str)   : the name of the dds
            freq        (float) : the frequency in Hz
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        if freq > 400 or freq < 0:
            raise Exception('Error: frequency must be within [0 Hz, 400 MHz].')
        ftw = self.dds_frequency_to_ftw(freq)
        yield self.api.setDDS(dds_name, 0, ftw)
        self.ddsChanged((dds_name, 'freq', freq))

    @setting(324, "DDS Amplitude", dds_name='s', ampl='v', returns='')
    def setDDSAmpl(self, c, dds_name, ampl):
        """
        Manually set the amplitude of a DDS.
        Arguments:
            dds_name    (str)   : the name of the dds
            ampl        (float) : the fractional amplitude
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        if ampl > 1 or ampl < 0:
            raise Exception('Error: amplitude must be within [0, 1].')
        asf = self.dds_amplitude_to_asf(ampl)
        yield self.api.setDDS(dds_name, 1, asf)
        self.ddsChanged((dds_name, 'ampl', ampl))

    @setting(325, "DDS Phase", dds_name='s', phase='v', returns='')
    def setDDSPhase(self, c, dds_name, phase):
        """
        Manually set the phase of a DDS.
        Arguments:
            dds_name    (str)   : the name of the dds
            phase       (float) : the phase in rotations (i.e. x2pi)
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        if phase >= 1 or pow < 0:
            raise Exception('Error: phase must be within [0, 1).')
        pow_dds = self.dds_turns_to_pow(phase)
        yield self.api.setDDS(dds_name, 2, pow_dds)
        self.ddsChanged((dds_name, 'phase', phase))

    @setting(326, "DDS Attenuation", dds_name='s', att='v', units='s', returns='')
    def setDDSAtt(self, c, dds_name, att, units='mu'):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            dds_name (str)  : the name of the dds
            att     (float) : attenuation (in dBm)
            units   (str)   : the voltage units, either 'mu' or 'v'
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        att_mu = att
        if units.lower() == 'dbm':
            att_mu = self.dds_att_to_mu(att)
        elif units.lower() != 'mu':
            raise Exception('Error: invalid units.')
        yield self.api.setDDSAtt(dds_name, att_mu)
        self.ddsChanged((dds_name, 'att', att))

    @setting(331, "DDS Read", dds_name='s', addr='i', length='i', returns='w')
    def readDDS(self, c, dds_name, addr, length):
        """
        Read the value of a DDS register.
        Arguments:
            dds_name    (str)   : the name of the dds
            addr        (int)   : the address to read from
            length      (int)   : how many bits to read
        Returns:
            (word)  : the register value
        """
        if dds_name not in self.dds_list:
            raise Exception('Error: device does not exist.')
        elif length not in (16, 32):
            raise Exception('Error: invalid read length. Must be one of (16, 32).')
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
    def setDAC(self, c, dac_num, value, units='mu'):
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
        # check that units and voltage are valid
        if units.lower() in ('v', 'volt', 'voltage'):
            voltage_mu = yield self.dac_volt_to_mu(value)
        elif units.lower() == 'mu':
            if (value < 0) or (value > 0xffff):
                raise Exception('Error: invalid DAC voltage.')
            voltage_mu = int(value)
        else:
            raise Exception('Error: invalid units.')
        # send to correct device
        if self.dacType == 'Zotino':
            yield self.api.setZotino(dac_num, voltage_mu)
        elif self.dacType == 'Fastino':
            yield self.api.setFastino(dac_num, voltage_mu)
        self.dacChanged((dac_num, 'chan', voltage_mu))

    @setting(422, "DAC Gain", dac_num='i', gain='v', units='s', returns='')
    def setDACGain(self, c, dac_num, gain, units='mu'):
        """
        Manually set the gain of a DAC channel.
        Arguments:
            dac_num (int)   : the DAC channel number
            gain    (float) : the DAC channel gain
            units   (str)   : the gain units, either 'mu' or 'dB'
        """
        if self.dacType != 'Zotino':
            raise Exception('Error: DAC does not support this function.')
        gain_mu = None
        # only 32 channels per DAC
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        if units in ('pct', 'frac', 'p', 'f'):
            gain_mu = int(gain * 0xffff) - 1
        elif units == 'mu':
            gain_mu = int(gain)
        else:
            raise Exception('Error: invalid units.')
        # check that gain is valid
        if gain < 0 or gain > 0xffff:
            raise Exception('Error: gain outside bounds of [0,1]')
        yield self.api.setZotinoGain(dac_num, gain_mu)
        self.dacChanged((dac_num, 'gain', voltage_mu))

    @setting(423, "DAC Offset", dac_num='i', value='v', units='s', returns='')
    def setDACOffset(self, c, dac_num, value, units='mu'):
        """
        Manually set the offset voltage of a DAC channel.
        Arguments:
            dac_num (int)   : the DAC channel number
            value   (float) : the value to write to the DAC offset register
            units   (str)   : the voltage units, either 'mu' or 'v'
        """
        if self.dacType != 'Zotino':
            raise Exception('Error: DAC does not support this function.')
        voltage_mu = None
        # check that dac channel is valid
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        if units == 'v':
            voltage_mu = yield self.dac_volt_to_mu(value)
        elif units == 'mu':
            if (value < 0) or (value > 0xffff):
                raise Exception('Error: invalid DAC voltage.')
            voltage_mu = int(value)
        else:
            raise Exception('Error: invalid units.')
        yield self.api.setZotinoOffset(dac_num, voltage_mu)
        self.dacChanged((dac_num, 'offset', voltage_mu))

    @setting(424, "DAC OFS", value='v', units='s', returns='')
    def setDACGlobal(self, c, value, units='mu'):
        """
        Write to the global OFSx registers of the DAC.
        Arguments:
            value   (float) : the value to write to the DAC OFSx register
            units   (str)   : the voltage units, either 'mu' or 'v'
            units   (str)   : the voltage units, either 'mu' or 'v'
        """
        if self.dacType != 'Zotino':
            raise Exception('Error: DAC does not support this function.')
        voltage_mu = None
        if units == 'v':
            voltage_mu = yield self.dac_volt_to_mu(value)
        elif units == 'mu':
            if (value < 0) or (value > 0x2fff):
                raise Exception('Error: invalid DAC voltage.')
            voltage_mu = int(value)
        else:
            raise Exception('Error: invalid units.')
        yield self.api.setZotinoGlobal(voltage_mu)
        self.dacChanged((0, 'ofs', voltage_mu))

    @setting(431, "DAC Read", dac_num='i', reg='s', returns='i')
    def readDAC(self, c, dac_num, reg):
        """
        Read the value of a DAC register.
        Arguments:
            dac_num (int)   : the dac channel number
            param   (float) : the register to read from
        """
        if (dac_num > 31) or (dac_num < 0):
            raise Exception('Error: device does not exist.')
        elif reg.upper() not in AD53XX_REGISTERS.keys():
            raise Exception('Error: invalid register. Must be one of ' + str(tuple(AD53XX_REGISTERS.keys())))
        # send to correct device
        if self.dacType == 'Zotino':
            reg_val = yield self.api.readZotino(dac_num, AD53XX_REGISTERS[reg])
        elif self.dacType == 'Fastino':
            reg_val = yield self.api.readFastino(dac_num, AD53XX_REGISTERS[reg])
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
            gain   (int)    : the channel gain
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
        self.adcUpdated(sampleArr)
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


if __name__ == '__main__':
    from labrad import util
    util.runServer(ARTIQ_Server())
