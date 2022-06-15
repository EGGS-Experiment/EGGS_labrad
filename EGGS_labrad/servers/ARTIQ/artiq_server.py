"""
### BEGIN NODE INFO
[info]
name = ARTIQ Server
version = 1.1.0
description = A bridge to use LabRAD for ARTIQ.
instancename = ARTIQ Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import logging

from labrad.server import LabradServer, setting, Signal
from twisted.internet.threads import deferToThread
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue

import numpy as np
from artiq_api import ARTIQ_api
from EGGS_labrad.config import device_db as device_db_module

from artiq.coredevice.ad53xx import AD53XX_READ_X1A, AD53XX_READ_X1B, AD53XX_READ_OFFSET,\
                                    AD53XX_READ_GAIN, AD53XX_READ_OFS0, AD53XX_READ_OFS1,\
                                    AD53XX_READ_AB0, AD53XX_READ_AB1, AD53XX_READ_AB2, AD53XX_READ_AB3

AD53XX_REGISTERS = {'X1A': AD53XX_READ_X1A, 'X1B': AD53XX_READ_X1B, 'OFF': AD53XX_READ_OFFSET,
                    'GAIN': AD53XX_READ_GAIN, 'OFS0': AD53XX_READ_OFS1, 'OFS1': AD53XX_READ_OFS1,
                    'AB0': AD53XX_READ_AB0, 'AB1': AD53XX_READ_AB1, 'AB2': AD53XX_READ_AB2, 'AB3': AD53XX_READ_AB3}

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
    regKey = 'ARTIQ Server'


    # SIGNALS
    ttlChanged = Signal(TTLSIGNAL_ID, 'signal: ttl changed', '(sb)')
    ddsChanged = Signal(DDSSIGNAL_ID, 'signal: dds changed', '(ssv)')
    dacChanged = Signal(DACSIGNAL_ID, 'signal: dac changed', '(isv)')
    adcUpdated = Signal(ADCSIGNAL_ID, 'signal: adc updated', '(*v)')
    expRunning = Signal(EXPSIGNAL_ID, 'signal: exp running', '(bi)')


    # STARTUP
    @inlineCallbacks
    def initServer(self):
        # remove logger objects from artiq/sipyco
        # todo: fix
        logger_dict = {}
        for logger_name, logger_object in self.logger.manager.loggerDict.items():
            if ('artiq' not in logger_name) and ('sipyco' not in logger_name):
                logger_dict[logger_name] = logger_object

        self.logger.manager.loggerDict = logger_dict

        self.api = ARTIQ_api(device_db_module.__file__)
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

    def _setVariables(self):
        """
        Sets ARTIQ-related variables.
        """
        # used to ensure atomicity
        self.inCommunication = DeferredLock()
        # pulse sequencer variables
        self.ps_rid = None
        # conversions
        # DDS - val to mu
        self.dds_frequency_to_ftw = lambda freq: np.int32(freq * 4.2949673) # 32 bits / 1GHz
        self.dds_amplitude_to_asf = lambda ampl: np.int32(ampl * 0x3fff)
        self.dds_turns_to_pow = lambda phase: np.int32(phase * 0xffff)
        self.dds_att_to_mu = lambda dbm: np.int32(0xff) - np.int32(round(dbm * 8))
        # DDS - mu to val
        self.dds_ftw_to_frequency = lambda freq: freq / 4.2949673
        self.dds_asf_to_amplitude = lambda ampl: ampl / 0x3fff
        self.dds_pow_to_turns = lambda phase: phase / 0xffff
        self.dds_mu_to_att = lambda mu: (255 - (mu & 0xff)) / 8
        # DAC
        from artiq.coredevice.ad53xx import voltage_to_mu
        self.dac_voltage_to_mu = voltage_to_mu
        # ADC
        from artiq.coredevice.sampler import adc_mu_to_volt
        self.adc_mu_to_volt = adc_mu_to_volt

    def _setDevices(self):
        """
        Get the list of devices in the ARTIQ box.
        """
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

    # @setting(32, 'Dataset Set', dataset_name='s', values='?')
    # def setDataset(self, c, dataset_name):
    #     """
    #     Sets the values of a dataset.
    #     Arguments:
    #         dataset_name    (str)   : the name of the dataset
    #         values                  : the values for the dataset
    #     """
    #     #return self.datasets.get(dataset_name, archive=False)
    #     pass


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
        ps_expid = {
            'log_level': 30,
            'file': path,
            'class_name': None,
            'arguments': {
                'maxRuns': maxruns,
                'linetrigger_enabled': self.linetrigger_enabled,
                'linetrigger_delay_us': self.linetrigger_delay,
                'linetrigger_ttl_name': self.linetrigger_ttl}
        }

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
        return self.api.ttlout_list + self.api.ttlin_list

    @setting(221, "TTL Set", ttl_name='s', state=['b', 'i'], returns='')
    def setTTL(self, c, ttl_name, state):
        """
        Manually set a TTL to the given state. TTL can be of classes TTLOut or TTLInOut.
        Arguments:
            ttl_name    (str)           : name of the ttl
            state       [bool, int]     : ttl power state
        """
        if ttl_name not in self.api.ttlout_list:
            raise Exception('Error: device does not exist.')
        if (type(state) == int) and (state not in (0, 1)):
            raise Exception('Error: invalid state.')
        yield self.api.setTTL(ttl_name, state)
        self.notifyOtherListeners(c, (ttl_name, state), self.ttlChanged)

    @setting(222, "TTL Get", ttl_name='s', returns='b')
    def getTTL(self, c, ttl_name):
        """
        Read the power state of a TTL. TTL must be of class TTLInOut.
        Arguments:
            ttl_name    (str)   : name of the ttl
        Returns:
                        (bool)  : ttl power state
        """
        if ttl_name not in self.api.ttlin_list:
            raise Exception('Error: device does not exist.')
        state = yield self.api.getTTL(ttl_name)
        returnValue(bool(state))


    # DDS
    @setting(311, "DDS List", returns='*s')
    def DDSlist(self, c):
        """
        Get the list of available DDS (AD9910 or AD9912) channels.
        Returns:
            (*str)  : the list of DDS names.
        """
        dds_list = yield self.api.dds_list.keys()
        returnValue(list(dds_list))

    @setting(321, "DDS Initialize", dds_name='s', returns='')
    def DDSinitialize(self, c, dds_name):
        """
        Resets/initializes the DDSs.
        Arguments:
            dds_name    (str)   : the name of the DDS.
        """
        if dds_name not in self.api.dds_list:
            raise Exception('Error: device does not exist.')
        yield self.api.initializeDDS(dds_name)

    @setting(322, "DDS Toggle", dds_name='s', state=['b', 'i'], returns='b')
    def DDStoggle(self, c, dds_name, state=None):
        """
        Manually toggle a DDS via the RF switch.
        Arguments:
            dds_name    (str)           : the name of the DDS.
            state       [bool, int]     : the DDS rf switch state.
        Returns:
                        (bool)          :
        """
        if dds_name not in self.api.dds_list:
            raise Exception('Error: device does not exist.')
        # setter
        if state is not None:
            if (type(state) == int) and (state not in (0, 1)):
                raise Exception('Error: invalid input. Value must be a boolean, 0, or 1.')
            yield self.api.setDDSsw(dds_name, state)
        # getter
        state = yield self.api.getDDSsw(dds_name)
        self.notifyOtherListeners(c, (dds_name, 'onoff', state), self.ddsChanged)
        returnValue(bool(state))

    @setting(323, "DDS Frequency", dds_name='s', freq='v', returns='i')
    def DDSfreq(self, c, dds_name, freq=None):
        """
        Manually set the frequency of a DDS.
        Arguments:
            dds_name    (str)   : the name of the DDS.
            freq        (float) : the frequency (in Hz).
        Returns:
                        (int)   : the 32-bit frequency tuning word.
        """
        if dds_name not in self.api.dds_list:
            raise Exception('Error: device does not exist.')
        # setter
        if freq is not None:
            if (freq > 4e8) or (freq < 0):
                raise Exception('Error: frequency must be within [0 Hz, 400 MHz].')
            ftw = self.dds_frequency_to_ftw(freq)
            yield self.api.setDDS(dds_name, 'ftw', ftw)
        # getter
        ftw, _, _ = yield self.api.getDDS(dds_name)
        self.notifyOtherListeners(c, (dds_name, 'ftw', ftw), self.ddsChanged)
        returnValue(np.int32(ftw))

    @setting(324, "DDS Amplitude", dds_name='s', ampl='v', returns='i')
    def DDSampl(self, c, dds_name, ampl=None):
        """
        Manually set the amplitude of a DDS.
        Arguments:
            dds_name    (str)   : the name of the DDS.
            ampl        (float) : the fractional amplitude.
        Returns:
                        (int)   : the 14-bit amplitude scaling factor.
        """
        if dds_name not in self.api.dds_list:
            raise Exception('Error: device does not exist.')
        # setter
        if ampl is not None:
            if (ampl > 1) or (ampl < 0):
                raise Exception('Error: amplitude must be within [0, 1].')
            asf = self.dds_amplitude_to_asf(ampl)
            yield self.api.setDDS(dds_name, 'asf', asf)
        # getter
        _, asf, _ = yield self.api.getDDS(dds_name)
        self.notifyOtherListeners(c, (dds_name, 'asf', asf), self.ddsChanged)
        returnValue(np.int32(asf))

    @setting(325, "DDS Phase", dds_name='s', phase='v', returns='i')
    def DDSphase(self, c, dds_name, phase=None):
        """
        Manually set the phase of a DDS.
        Arguments:
            dds_name    (str)   : the name of the dds
            phase       (float) : the phase in rotations (1 is a full rotation, value must be between [0, 1)).
        Returns:
                        (int)   : the 16-bit phase offset word.
        """
        if dds_name not in self.api.dds_list:
            raise Exception('Error: device does not exist.')
        if phase is not None:
            if (phase >= 1) or (phase < 0):
                raise Exception('Error: phase must be within [0, 1).')
            pow = self.dds_turns_to_pow(phase)
            yield self.api.setDDS(dds_name, 'pow', pow)
        # getter
        _, _, pow = yield self.api.getDDS(dds_name)
        self.notifyOtherListeners(c, (dds_name, 'pow', pow), self.ddsChanged)
        returnValue(np.int32(pow))

    @setting(326, "DDS Attenuation", dds_name='s', att='v', returns='i')
    def DDSatt(self, c, dds_name, att=None):
        """
        Manually set a DDS to the given parameters.
        Arguments:
            dds_name    (str)   : the name of the DDS.
            att         (float) : the channel attenuation (in dBm).
        Returns:
                        (int)   : the channel attenuation (in machine units).
        """
        if dds_name not in self.api.dds_list:
            raise Exception('Error: device does not exist.')
        # setter
        if att is not None:
            if (att < 0) or (att > 31.5):
                raise Exception('Error: attenuation must be within [0, 31.5].')
            att_mu = self.dds_att_to_mu(att)
            yield self.api.setDDSatt(dds_name, int(att_mu))
        # getter
        att_mu = yield self.api.getDDSatt(dds_name)
        self.notifyOtherListeners(c, (dds_name, 'att', att_mu), self.ddsChanged)
        returnValue(att_mu)

    @setting(331, "DDS Read", dds_name='s', addr='i', length='i', returns=['i', '(ii)'])
    def DDSread(self, c, dds_name, addr, length):
        """
        Read the value of a DDS register.
        Arguments:
            dds_name    (str)   : the name of the dds
            addr        (int)   : the address to read from
            length      (int)   : how many bits to read. Must be one of (16, 32, 64).
        Returns:
            (word)  : the register value
        """
        if dds_name not in self.api.dds_list:
            raise Exception('Error: device does not exist.')
        elif length not in (16, 32, 64):
            raise Exception('Error: invalid read length. Must be one of (16, 32, 64).')
        reg_val = yield self.api.readDDS(dds_name, addr, length)
        if length != 64:
            returnValue(reg_val)
        else:
            # have to break it into two 32-bit words, since
            # labrad can only send 32-bit data at most
            reg_val1 = np.int32(reg_val)
            reg_val2 = np.int32((reg_val >> 32) & 0xffffffff)
            resp = (reg_val1, reg_val2)
            returnValue(resp)


    # URUKUL
    @setting(341, "Urukul List", returns='*s')
    def UrukulList(self, c):
        """
        Get the list of available Urukul CPLDs.
        Returns:
            (*str)  : the list of urukul CPLD names.
        """
        urukul_list = yield self.api.urukul_list.keys()
        returnValue(list(urukul_list))

    @setting(342, "Urukul Initialize", urukul_name='s', returns='')
    def UrukulInitialize(self, c, urukul_name):
        """
        Resets/initializes an Urukul CPLD.
        Arguments:
            urukul_name (str)   : the name of the urukul CPLD.
        """
        if urukul_name not in self.api.urukul_list:
            raise Exception('Error: device does not exist.')
        yield self.api.initializeUrukul(urukul_name)


    # DAC
    @setting(411, "DAC Initialize", returns='')
    def DACinitialize(self, c):
        """
        Manually initialize the DAC.
        """
        yield self.api.initializeDAC()

    @setting(421, "DAC Set", dac_num='i', value='v', units='s', returns='')
    def DACset(self, c, dac_num, value, units='mu'):
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
            voltage_mu = yield self.dac_voltage_to_mu(value)
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
        self.notifyOtherListeners(c, (dac_num, 'dac', voltage_mu), self.dacChanged)

    @setting(422, "DAC Gain", dac_num='i', gain='v', units='s', returns='')
    def DACgain(self, c, dac_num, gain, units='mu'):
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
        if (gain < 0) or (gain > 0xffff):
            raise Exception('Error: gain outside bounds of [0,1]')
        yield self.api.setZotinoGain(dac_num, gain_mu)
        self.notifyOtherListeners(c, (dac_num, 'gain', gain_mu), self.dacChanged)

    @setting(423, "DAC Offset", dac_num='i', value='v', units='s', returns='')
    def DACoffset(self, c, dac_num, value, units='mu'):
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
            voltage_mu = yield self.dac_voltage_to_mu(value)
        elif units == 'mu':
            if (value < 0) or (value > 0xffff):
                raise Exception('Error: invalid DAC voltage.')
            voltage_mu = int(value)
        else:
            raise Exception('Error: invalid units.')
        yield self.api.setZotinoOffset(dac_num, voltage_mu)
        self.notifyOtherListeners(c, (dac_num, 'off', voltage_mu), self.dacChanged)

    @setting(424, "DAC OFS", value='v', units='s', returns='')
    def DACofs(self, c, value, units='mu'):
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
            voltage_mu = yield self.dac_voltage_to_mu(value)
        elif units == 'mu':
            if (value < 0) or (value > 0x2fff):
                raise Exception('Error: invalid DAC voltage.')
            voltage_mu = int(value)
        else:
            raise Exception('Error: invalid units.')
        yield self.api.setZotinoGlobal(voltage_mu)
        self.notifyOtherListeners(c, (-1, 'ofs', voltage_mu), self.dacChanged)

    @setting(431, "DAC Read", dac_num='i', reg='s', returns='i')
    def DACread(self, c, dac_num, reg):
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
    def samplerInitialize(self, c):
        """
        Initialize the Sampler.
        """
        yield self.api.initializeSampler()

    @setting(512, "Sampler Gain", channel='i', gain='i', returns='')
    def samplerGain(self, c, channel, gain):
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
    def samplerRead(self, c, samples=None):
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
        Notifies all listeners except the one in the given context, executing function f.
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        f(message, notified)

    def getOtherListeners(self, c):
        """
        Get all listeners except for the context owner.
        """
        notified = self.listeners.copy()
        notified.remove(c.ID)
        return notified

    def initContext(self, c):
        """
        Initialize a new context object.
        """
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)


if __name__ == '__main__':
    from labrad import util

    util.runServer(ARTIQ_Server())
