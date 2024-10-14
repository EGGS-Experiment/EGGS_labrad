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
import numpy as np

from labrad.server import LabradServer, setting, Signal
from twisted.internet.threads import deferToThread
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue

from artiq_api import ARTIQ_API
from artiq_subscriber import ARTIQ_subscriber
from EGGS_labrad.servers import ContextServer
from EGGS_labrad.config import device_db as device_db_module

from artiq.coredevice.ad53xx import AD53XX_READ_X1A, AD53XX_READ_X1B, AD53XX_READ_OFFSET,\
                                    AD53XX_READ_GAIN, AD53XX_READ_OFS0, AD53XX_READ_OFS1,\
                                    AD53XX_READ_AB0, AD53XX_READ_AB1, AD53XX_READ_AB2, AD53XX_READ_AB3

AD53XX_REGISTERS = {
    'X1A': AD53XX_READ_X1A, 'X1B': AD53XX_READ_X1B, 'OFF': AD53XX_READ_OFFSET,
    'GAIN': AD53XX_READ_GAIN, 'OFS0': AD53XX_READ_OFS1, 'OFS1': AD53XX_READ_OFS1,
    'AB0': AD53XX_READ_AB0, 'AB1': AD53XX_READ_AB1, 'AB2': AD53XX_READ_AB2, 'AB3': AD53XX_READ_AB3
}

TTLSIGNAL_ID = 828176
DACSIGNAL_ID = 828175
ADCSIGNAL_ID = 828174
EXPSIGNAL_ID = 828173
DDSSIGNAL_ID = 828172
# todo: move all mu stuff to api since api has better access to conversion stuff than we do and can call it in a nonkernel function
# todo: use dds name helper to allow board number and channel number to be used for settings


class ARTIQ_Server(ContextServer):
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
        super().initServer()

        # remove logger objects from artiq/sipyco
        logging.getLogger('artiq.coredevice.comm').disabled = True
        logging.getLogger('artiq.coredevice.comm_kernel').disabled = True
        # for logger_name, logger_object in self.logger.manager.loggerDict.items():
        #     print('logger_name: {}\t\tlogger_obj: {}'.format(logger_name, logger_object))

        # set up ARTIQ stuff
        self.api = ARTIQ_API(device_db_module.__file__)
        yield self._setClients()
        yield self._setVariables()
        yield self._setDevices()

    def _setClients(self):
        """
        Create clients to ARTIQ master.
        Used to get datasets, submit experiments, and monitor devices.
        """
        # connect to master clients
        from sipyco.pc_rpc import Client
        try:
            self.scheduler = Client('192.168.1.48', 3251, 'master_schedule')
            self.datasets = Client('192.168.1.48', 3251, 'master_dataset_db')
        except Exception as e:
            print("Unable to connect to ARTIQ Master. Scheduler and datasets disabled.")

        # connect to master notifications
        try:
            # set up ARTIQ subscriber
            from asyncio import get_event_loop, set_event_loop, Event
            self._exp_running = False
            self.subscriber_exp = ARTIQ_subscriber('schedule', self._process_subscriber_update, self)
            self.subscriber_exp.connect('::1', 3250)

            # set up event loop for ARTIQ_subscriber
            loop = get_event_loop()
            stop_event = Event()

            # set up thread to run subscriber event loop in background
            from threading import Thread
            def run_in_background(loop):
                # set event loop for thread to be the passed-in loop
                set_event_loop(loop)
                # run loop indefinitely
                loop.run_until_complete(stop_event.wait())
                loop.close()

            t = Thread(target=run_in_background, args=(loop,))
            t.start()

        except Exception as e:
            print(e)
            print("Unable to connect to ARTIQ Master. Experiment notifications disabled.")

    def _process_subscriber_update(self, mod):
        """
        Checks if any experiments are running and sends a Signal
        to clients accordingly.
        """
        # todo: do we actually need this?
        running_exp = None

        # check if any experiments are running
        for rid, exp_params in self.struct_holder_schedule.backing_store.items():
            run_status = exp_params['status']

            # send experiment details to clients if experiment is running
            if run_status == 'running':
                self.expRunning((True, rid))
                # tmp remove
                self.api.core.close()
                # tmp remove
                return

        # otherwise, no experiment running, so inform clients
        self.expRunning((False, -1))

    def _setVariables(self):
        """
        Sets ARTIQ-related variables.
        """
        # used to ensure atomicity
        self.inCommunication = DeferredLock()

        # conversions
        # DDS - val to mu
        self.dds_frequency_to_ftw = lambda freq: np.int32(freq * 4.294967295) # 0xFFFFFFFF / 1GHz
        self.dds_amplitude_to_asf = lambda ampl: np.int32(ampl * 0x3FFF)
        self.dds_turns_to_pow =     lambda phase: np.int32(phase * 0xFFFF)
        self.dds_att_to_mu =        lambda dbm: np.int32(0xFF) - np.int32(round(dbm * 8))

        # DDS - mu to val
        self.dds_ftw_to_frequency = lambda freq: freq / 4.2949673
        self.dds_asf_to_amplitude = lambda ampl: ampl / 0x3FFF
        self.dds_pow_to_turns =     lambda phase: phase / 0xFFFF
        self.dds_mu_to_att =        lambda mu: (255 - (mu & 0xFF)) / 8

        # DAC
        from artiq.coredevice.ad53xx import voltage_to_mu
        self.dac_voltage_to_mu =    voltage_to_mu

        # ADC
        from artiq.coredevice.sampler import adc_mu_to_volt
        self.adc_mu_to_volt =       adc_mu_to_volt

    def _setDevices(self):
        """
        Get the list of devices in the ARTIQ box.
        """
        self.dacType = self.api.dacType


    # CORE
    # CORE
    @setting(888888, "tmp close", returns='')
    def tmp_close(self, c):
        """
        Returns a list of ARTIQ devices.
        """
        self.api.core.close()

    @setting(21, "Get Devices", returns='*s')
    def getDevices(self, c):
        """
        Returns a list of ARTIQ devices.
        """
        return list(self.api.device_db.keys())

    @setting(31, 'Dataset Get', dataset_key='s', returns='?')
    def datasetGet(self, c, dataset_key):
        """
        Returns a dataset.
        Arguments:
            dataset_key (str)   : the name of the dataset.
        Returns:
            the dataset values
        """
        return self.datasets.get(dataset_key)

    @setting(32, 'Dataset Set', dataset_key='s', dataset_value='?', persist='b', returns='')
    def datasetSet(self, c, dataset_key, dataset_value, persist=True):
        """
        Sets the values of a dataset.
            If the dataset does not exist, a new one will be created.
            If the dataset already exists, the old value will completely overwritten.
        Arguments:
            dataset_key (str)   : the name of the dataset.
            dataset_value       : the values for the dataset.
            persist     (bool)  : whether the data should persist between master reboots.
        """
        print('\tds set: {}\n'.format(dataset_value))
        self.datasets.set(dataset_key, dataset_value, persist)

    @setting(33, 'Dataset Delete', dataset_key='s', returns='')
    def datasetDelete(self, c, dataset_key):
        """
        De;ete a dataset/
        Arguments:
            dataset_key (str)   : the name of the dataset.
        """
        self.datasets.delete(dataset_key)


    # TTL
    @setting(211, 'TTL List', returns='*s')
    def ttlList(self, c):
        """
        Lists all available TTL channels.
        Returns:
                (*str)  : a list of all TTL channels.
        """
        ttlin_list = list(self.api.ttlin_dict.keys())
        ttlout_list = list(self.api.ttlout_dict.keys())
        return ttlin_list + ttlout_list

    @setting(221, "TTL Set", ttl_name='s', state=['b', 'i'], returns='')
    def ttlSet(self, c, ttl_name, state):
        """
        Manually set a TTL to the given state. TTL can be of classes TTLOut or TTLInOut.
        Arguments:
            ttl_name    (str)           : name of the ttl
            state       [bool, int]     : ttl power state
        """
        if ttl_name not in self.api.ttlout_dict:
            raise Exception('Error: device does not exist.')
        if (type(state) == int) and (state not in (0, 1)):
            raise Exception('Error: invalid state.')
        yield self.api.setTTL(ttl_name, state)
        self.notifyOtherListeners(c, (ttl_name, state), self.ttlChanged)

    @setting(222, "TTL Get", ttl_name='s', returns='b')
    def ttlGet(self, c, ttl_name):
        """
        Read the power state of a TTL. TTL must be of class TTLInOut.
        Arguments:
            ttl_name    (str)   : name of the ttl
        Returns:
                        (bool)  : ttl power state
        """
        if ttl_name not in self.api.ttlin_dict:
            raise Exception('Error: device does not exist.')
        state = yield self.api.getTTL(ttl_name)
        returnValue(bool(state))

    @setting(231, "TTL Counts", ttl_name='s', time_us='i', trials='i', returns='(vv)')
    def ttlCounts(self, c, ttl_name, time_us=3000, trials=10):
        """
        Read the number of counts from a TTL in a given time and
            averages it over a number of trials.
            TTL must be of class EdgeCounter.
        Arguments:
            ttl_name    (str)   : name of the ttl
            time_us     (int)   : number of seconds to count for
            trials      (int)   : number of trials to average counts over
        Returns:
                        (float, float) : the mean and stdev of the TTL counts.
        """
        # check device is valid
        if ttl_name not in self.api.ttlcounter_dict:
            raise Exception('Error: device does not exist.')

        # ensure we don't count for too long or too short
        if (time_us * 1e-6 * trials > 20) or (time_us < 10):
            raise Exception('Error: invalid total counting time.')

        counts_list = self.api.getTTLCountFastCounts(ttl_name, time_us, trials)
        return (np.mean(counts_list), np.std(counts_list))

    @setting(232, "TTL Count List", ttl_name='s', time_us='i', trials='i', returns='*v')
    def ttlCountList(self, c, ttl_name, time_us=3000, trials=10):
        """
        Read the number of counts from a TTL in a given time
            for a number of trials and returns the raw data.
            TTL must be of class EdgeCounter.
        Arguments:
            ttl_name    (str)   : name of the ttl
            time_us     (int)   : number of seconds to count for
            trials      (int)   : number of trials to average counts over
        Returns:
                        (list(float)) : raw ttl counts for each trial
        """
        # check device is valid
        if ttl_name not in self.api.ttlcounter_dict:
            raise Exception('Error: device does not exist.')

        # ensure we don't count for too long or too short
        if (time_us * 1e-6 * trials > 20) or (time_us < 10):
            raise Exception('Error: invalid total counting time.')

        counts_list = self.api.getTTLCountFastCounts(ttl_name, time_us, trials)
        return counts_list


    # DDS
    @setting(311, "DDS List", returns='*s')
    def DDSlist(self, c):
        """
        Get the list of available DDS (AD9910 or AD9912) channels.
        Returns:
            (*str)  : the list of DDS names.
        """
        return list(self.api.dds_dict.keys())

    @setting(321, "DDS Initialize", dds_name='s', returns='')
    def DDSinitialize(self, c, dds_name):
        """
        Resets/initializes the DDSs.
        Arguments:
            dds_name    (str)   : the name of the DDS.
        """
        if dds_name not in self.api.dds_dict:
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
        if dds_name not in self.api.dds_dict:
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

    '''
    PRECOMPILE TESTING
    '''
    # @setting(88888, "DDS Frequency Fast", dds_name='s', freq='v', returns='i')
    @setting(323, "DDS Frequency", dds_name='s', freq='v', returns='i')
    def DDSfrequency(self, c, dds_name, freq=None):
        """
        Manually set the frequency of a DDS.
        Arguments:
            dds_name    (str)   : the name of the DDS.
            freq        (float) : the frequency (in Hz).
        Returns:
                        (int)   : the 32-bit frequency tuning word.
        """
        # check device is valid
        if dds_name not in self.api.dds_dict:
            raise Exception('Error: device does not exist.')

        # setter
        if freq is not None:
            if (freq > 4e8) or (freq < 0):
                raise Exception('Error: frequency must be within [0 Hz, 400 MHz].')
            ftw = self.dds_frequency_to_ftw(freq)
            self.api.setDDSFastFTW(dds_name, ftw)

        # getter
        ftw, asf = self.api.getDDSFastWave(dds_name)
        self.notifyOtherListeners(c, (dds_name, 'ftw', ftw), self.ddsChanged)
        return np.int32(ftw)

    # @setting(88889, "DDS Amplitude Fast", dds_name='s', ampl='v', returns='i')
    @setting(324, "DDS Amplitude", dds_name='s', ampl='v', returns='i')
    def DDSamplitude(self, c, dds_name, ampl=None):
        """
        Manually set the amplitude of a DDS.
        Arguments:
            dds_name    (str)   : the name of the DDS.
            ampl        (float) : the fractional amplitude.
        Returns:
                        (int)   : the 14-bit amplitude scaling factor.
        """
        # check device is valid
        if dds_name not in self.api.dds_dict:
            raise Exception('Error: device does not exist.')

        # setter
        if ampl is not None:
            if (ampl > 1.) or (ampl < 0.):
                raise Exception('Error: amplitude must be within [0, 1].')
            asf = self.dds_amplitude_to_asf(ampl)
            self.api.setDDSFastASF(dds_name, asf)

        # getter
        ftw, asf = self.api.getDDSFastWave(dds_name)
        self.notifyOtherListeners(c, (dds_name, 'asf', asf), self.ddsChanged)
        return np.int32(asf)
    '''
    PRECOMPILE TESTING
    '''

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
        if dds_name not in self.api.dds_dict:
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
        if dds_name not in self.api.dds_dict:
            raise Exception('Error: device does not exist.')

        # setter
        if att is not None:
            if (att < 0) or (att > 31.5):
                raise Exception('Error: attenuation must be within [0, 31.5].')
            att_mu = self.dds_att_to_mu(att)
            self.api.setDDSFastATT(dds_name, int(att_mu))
            # self.api.setDDSatt(dds_name, int(att_mu))

        # getter
        att_mu = self.api.getDDSFastATT(dds_name)
        # att_mu = self.api.getDDSatt(dds_name)
        self.notifyOtherListeners(c, (dds_name, 'att', att_mu), self.ddsChanged)
        return att_mu

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
        if dds_name not in self.api.dds_dict:
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

    @setting(332, "DDS Get All", returns='*2i')
    def DDSGetAll(self, c):
        """
        Quickly get frequency, amplitude, attenuation, and switch values
            (in SI units) for all DDS channels.
            Doesn't return pow (phase offset word).
            Should only be used by DDS Client.
        Returns:
            list(tuple(int, int, int, bool)) : a list of dds parameters for all DDSs in the format (asf, ftw, att, sw)
        """
        dds_data = yield self.api.getDDSAll()
        returnValue(dds_data)

    def _ddsNameHelper(self, dds_name):
        """
        Ensure DDS channel exists.
        """
        # accept dds_name as tuple of (board_num, channel_num)
        if (type(dds_name) is tuple) and (len(dds_name) == 2):
            dds_name = "urukul{:d}_ch{:d}".format(dds_name[0], dds_name[1])
        # check dds exists
        if dds_name not in self.api.dds_dict:
            raise Exception('Error: device does not exist.')
        return dds_name


    # URUKUL
    @setting(351, "Urukul List", returns='*s')
    def UrukulList(self, c):
        """
        Get the list of available Urukul CPLDs.
        Returns:
            (*str)  : the list of urukul CPLD names.
        """
        urukul_list = yield self.api.urukul_list.keys()
        returnValue(list(urukul_list))

    @setting(352, "Urukul Initialize", urukul_name='s', returns='')
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

    @setting(512, "Sampler Gain", channel='i', gain='i', returns='i')
    def samplerGain(self, c, channel, gain=None):
        """
        Set the gain of a sampler channel.
        Arguments:
            channel (int)   : the ADC channel number. Must be in [0, 7]).
            gain    (int)   : the channel gain. Must be one of (1, 10, 100, 1000).
        Returns:
                    (int)   : the channel gain of the  (in mu).
        """
        # setter
        if gain is not None:
            if gain not in (1, 10, 100, 1000):
                raise Exception('Error: invalid gain. Must be one of (1, 10, 100, 1000).')
            gain_mu = int(np.log10(gain))
            yield self.api.setSamplerGain(channel, gain_mu)
        # getter
        sampler_gains = yield self.api.getSamplerGains()
        gain = int(10 ** sampler_gains[channel])
        returnValue(gain)

    @setting(521, "Sampler Read", channels='*i', rate='v', samples='i', returns='*v')
    def samplerRead(self, c, channels, rate, samples):
        """
        Read samples from given channels on the Sampler in a given time and
            averages it over a number of trials.
        Arguments:
            channels    list(int): a list of channels to read. Channels must be in [0, 7].
            rate        (float): the sample rate to read at (in Hz). Must be in [10, 1e4].
            samples     (int): the number of samples to read.
        Returns:
                        list(float): the average values for each channel (in volts).
        """
        if samples % 2 == 1:
            raise Exception('Error: number of samples must be even')
        elif (rate < 10) or (rate > 1e4):
            raise Exception('Error: number of samples must be even')
        # get channel gains
        sampler_gains = yield self.api.getSamplerGains()
        gain_arr_mu = np.array([sampler_gains[channel_num] for channel_num in channels])
        # acquire samples
        samples = yield self.api.readSampler(rate, samples)
        # keep values only for channels of interest
        samples = np.array([samples[:, channel_num] for channel_num in channels])
        # average values
        sample_mean = np.mean(samples, axis=1)
        # convert mu to volts
        sample_mean_volts = [self.adc_mu_to_volt(sample_mean[i], gain_arr_mu[i]) for i in range(len(channels))]
        returnValue(sample_mean_volts)

    @setting(522, "Sampler Read List", channels='*i', rate='v', samples='i', returns='*2v')
    def samplerReadList(self, c, channels, rate, samples):
        """
        Read samples from given channels on the Sampler in a given time and
            returns all values.
        Arguments:
            channels    list(int): a list of channels to read. Channels must be in [0, 7].
            rate        (float): the sample rate to read at (in Hz). Must be in [10, 1e4].
            samples     (int): the number of samples to read.
        Returns:
                        list(float): the sampler values for each channel (in volts).
        """
        if samples % 2 == 1:
            raise Exception('Error: number of samples must be even')
        elif (rate < 10) or (rate > 1e4):
            raise Exception('Error: number of samples must be even')
        # get channel gains
        sampler_gains = yield self.api.getSamplerGains()
        gain_arr_mu = np.array([sampler_gains[channel_num] for channel_num in channels])
        # acquire samples
        samples_mu = yield self.api.readSampler(rate, samples)
        # keep values only for channels of interest
        samples_mu = np.array([samples_mu[:, channel_num] for channel_num in channels])
        # convert mu to volts
        samples_volts = np.array([self.adc_mu_to_volt(samples_mu[i], gain_arr_mu[i]) for i in range(len(channels))])
        returnValue(samples_volts)


if __name__ == '__main__':
    from labrad import util
    util.runServer(ARTIQ_Server())
