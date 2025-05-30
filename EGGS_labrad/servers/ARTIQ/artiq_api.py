import numpy as np

from artiq.language import *
from artiq.coredevice import *
from artiq.master.databases import DeviceDB
from artiq.master.worker_db import DeviceManager
from artiq.coredevice.urukul import urukul_sta_rf_sw, CFG_PROFILE, CFG_RF_SW, DEFAULT_PROFILE
from artiq.coredevice.ad9910 import (_AD9910_REG_PROFILE0, _AD9910_REG_PROFILE1, _AD9910_REG_PROFILE2,
                                     _AD9910_REG_PROFILE3, _AD9910_REG_PROFILE4, _AD9910_REG_PROFILE5,
                                     _AD9910_REG_PROFILE6, _AD9910_REG_PROFILE7)

from builtins import ConnectionAbortedError, ConnectionResetError


class ARTIQ_API(object):
    """
    An API for ARTIQ hardware.
    Directly accesses the hardware on the box without having to use artiq_master.
    # todo: set version so we know what we're compatible with
    # todo: experiment with kernel invariants, fast-math, host_only, rpc, portable
    """
    kernel_invariants = set()

    '''
    AUTORELOAD DECORATOR
    '''
    def autoreload(func):
        """
        A decorator for non-kernel functions that attempts to reset
        the connection to artiq_master if we lost it.
        """
        def inner(self, *args, **kwargs):

            # run decorated function
            try:
                res = func(self, *args, **kwargs)
                return res

            # handle connection errors
            except (ConnectionAbortedError, ConnectionResetError) as e:

                # attempt to reconnect to master and reset client objects
                try:
                    # reset connection
                    print('Connection aborted, resetting connection to artiq_master...')
                    self.reset_connection()

                    # retry decorated function
                    res = func(self, *args, **kwargs)
                    return res
                except Exception as e:
                    print(repr(e))
                    raise e

            # handle RTIOUnderflows
            except RTIOUnderflow as e:
                # add slack
                self.core.break_realtime()

                # retry decorated function
                res = func(self, *args, **kwargs)
                return res

            # handle RTIOOverflows
            except RTIOOverflow as e:
                # reset core & add more slack
                self.core.reset()
                self.core.break_realtime()

                # retry decorated function
                res = func(self, *args, **kwargs)
                return res

            # handle all other errors
            except Exception as e:
                print("Unknown Error: {}".format(repr(e)))

        return inner


    '''
    INITIALIZATION
    '''
    def __init__(self, ddb_filepath):
        # get devices and device manager
        devices =               DeviceDB(ddb_filepath)
        self.ddb_filepath =     ddb_filepath
        self.device_manager =   DeviceManager(devices)
        self.device_db =        devices.get_device_db()
        self._getDevices()

        # get precompiled functions
        self._getPrecompiledFunctions()

    def close_connection(self):
        """
        Close core connection to hardware to allow others to
        take control.
        """
        try:
            self.core.close()
        except Exception as e:
            print(repr(e))


    '''new faster functions meant to be used with precompile'''
    def _getPrecompiledFunctions(self) -> TNone:
        """
        todo: document
        """
        '''
        DDS PRECOMPILE
        '''
        # set holder variables for DDS data getter
        self._dds_freq_get_ftw =    np.int32(0)
        self._dds_ampl_get_asf =    np.int32(0)
        self._dds_att_get_mu =      np.int32(0)
        self._dds_sw_get_status =   False

        # set holder variables for DDS data setter
        self._dds_num =             np.int32(0)
        self._dds_freq_set_ftw =    np.int32(0)
        self._dds_ampl_set_asf =    np.int32(0)
        self._dds_att_set_mu =      np.int32(0)
        self._dds_sw_set_status =   False

        ## precompile hardware functions
        # getters
        self._precompile_func_get_wave =    self.core.precompile(self._getDDSFastWave)
        self._precompile_func_get_att =     self.core.precompile(self._getDDSFastATT)
        self._precompile_func_get_sw =      self.core.precompile(self._getDDSFastSW)
        # setters
        self._precompile_func_set_freq =    self.core.precompile(self._setDDSFastFTW)
        self._precompile_func_set_ampl =    self.core.precompile(self._setDDSFastASF)
        self._precompile_func_set_att =     self.core.precompile(self._setDDSFastATT)
        self._precompile_func_set_sw =      self.core.precompile(self._setDDSFastSW)

        '''
        TTL PRECOMPILE
        '''
        # set holder variables for TTLCounter data getter
        self._ttlcount_get_counts =     np.zeros(0, dtype=np.int32)

        # set holder variables for TTLCounter data setter
        self._ttlcount_num =            np.int32(0)
        self._ttlcount_time_set_mu =    np.int32(0)
        self._ttlcount_samples_set_mu = np.int32(0)

        ## precompile hardware functions
        # getters
        self._precompile_func_get_ttlcounts =   self.core.precompile(self._getTTLCountFastCounts)

    @autoreload
    def getDDSFastWave(self, device_name: TStr) -> TTuple([TInt32, TInt32]):
        """
        todo:document
        """
        # get index of the desired dds within _dds_channels
        try:
            self._dds_num = self.dds_dict_search_num[device_name]
        except Exception as e:
            raise Exception("Error: desired device not found.")

        # call precompiled DDS waveform getter
        self._precompile_func_get_wave()

        # return waveform values
        return self._dds_freq_get_ftw, self._dds_ampl_get_asf

    @autoreload
    def getDDSFastATT(self, device_name: TStr) -> TInt32:
        """
        todo:document
        """
        # get index of the desired dds within _dds_channels
        try:
            self._dds_num = self.dds_dict_search_num[device_name]
        except Exception as e:
            raise Exception("Error: desired device not found.")

        # call precompiled DDS waveform getter
        self._precompile_func_get_att()

        # return waveform values
        return self._dds_att_get_mu

    @autoreload
    def getDDSFastSW(self, device_name: TStr) -> TInt32:
        """
        todo:document
        """
        # get index of the desired dds within _dds_channels
        try:
            self._dds_num = self.dds_dict_search_num[device_name]
        except Exception as e:
            raise Exception("Error: desired device not found.")

        # call precompiled DDS waveform getter
        self._precompile_func_get_sw()

        # return waveform values
        return self._dds_sw_get_status

    @autoreload
    def setDDSFastFTW(self, device_name: TStr, freq_ftw: TInt32) -> TNone:
        """
        todo:document
        """
        # get index of the desired dds within _dds_channels
        try:
            self._dds_num = self.dds_dict_search_num[device_name]
        except Exception as e:
            raise Exception("Error: desired device not found.")

        # set ftw as class variable for RPC retrieval
        self._dds_freq_set_ftw = np.int32(freq_ftw)

        # call precompiled DDS frequency setter
        self._precompile_func_set_freq()

    @autoreload
    def setDDSFastASF(self, device_name: TStr, ampl_asf: TInt32) -> TNone:
        """
        todo:document
        """
        # get index of the desired dds within _dds_channels
        try:
            self._dds_num = self.dds_dict_search_num[device_name]
        except Exception as e:
            raise Exception("Error: desired device not found.")

        # set ftw as class variable for RPC retrieval
        self._dds_ampl_set_asf = np.int32(ampl_asf)

        # call precompiled DDS frequency setter
        self._precompile_func_set_ampl()

    @autoreload
    def setDDSFastATT(self, device_name: TStr, att_mu: TInt32) -> TNone:
        """
        todo:document
        """
        # get index of the desired dds within _dds_channels
        try:
            self._dds_num = self.dds_dict_search_num[device_name]
        except Exception as e:
            raise Exception("Error: desired device not found.")

        # set att as class variable for RPC retrieval
        self._dds_att_set_mu = np.int32(att_mu)

        # call precompiled DDS attenuation setter
        self._precompile_func_set_att()

    @autoreload
    def setDDSFastSW(self, device_name: TStr, sw_state: TBool) -> TNone:
        """
        todo: document
        """
        # get index of the desired dds within _dds_channels
        try:
            self._dds_num = self.dds_dict_search_num[device_name]
        except Exception as e:
            raise Exception("Error: desired device not found.")

        # set att as class variable for RPC retrieval
        self._dds_sw_set_status = bool(sw_state)

        # call precompiled DDS attenuation setter
        self._precompile_func_set_sw()


    """
    FAST - KERNEL FUNCTIONS
    """
    @kernel(flags={"fast-math"})
    def _getDDSFastWave(self) -> TNone:
        self.core.break_realtime()

        # get device
        index_dds = self._return_dds_num()
        self.core.break_realtime()
        dds_dev = self._dds_channels[index_dds]
        self.core.break_realtime()

        # get existing waveform from device
        profile_data_mu = dds_dev.read64(_AD9910_REG_PROFILE7)
        self._store_getter_dds_data(profile_data_mu)

    @kernel(flags={"fast-math"})
    def _getDDSFastATT(self) -> TNone:
        self.core.break_realtime()

        # get device
        index_dds = self._return_dds_num()
        self.core.break_realtime()
        dds_dev = self._dds_channels[index_dds]
        self.core.break_realtime()

        # get existing waveform from device
        dds_att_mu = dds_dev.get_att_mu()
        self._store_getter_dds_att(dds_att_mu)

    @kernel(flags={"fast-math"})
    def _getDDSFastSW(self) -> TNone:
        self.core.break_realtime()

        # get device
        index_dds = self._return_dds_num()
        self.core.break_realtime()
        dds_dev = self._dds_channels[index_dds]
        self.core.break_realtime()
        channel_num = dds_dev.chip_select - 4

        # read CPLD status register
        urukul_cfg = dds_dev.cpld.sta_read()
        self.core.break_realtime()
        # extract switch status
        sw_reg = urukul_sta_rf_sw(urukul_cfg)
        sw_status = (sw_reg >> channel_num) & 0x1
        self._store_getter_dds_sw(sw_status)

    @kernel(flags={"fast-math"})
    def _setDDSFastFTW(self) -> TNone:
        self.core.break_realtime()

        ## get device
        index_dds = self._return_dds_num()
        self.core.break_realtime()
        dds_dev = self._dds_channels[index_dds]
        dds_cpld = dds_dev.cpld
        self.core.break_realtime()

        ## set default profile
        # extract current switch register status from urukul status register
        # note: necessary to prevent overwriting of existing switch configuration
        reg_sw = urukul_sta_rf_sw(dds_cpld.sta_read())
        reg_cfg_current = (dds_cpld.cfg_reg & ~0xF) | reg_sw
        # note: the following core.break_realtime is CRITICAL to ensuring
        # that we actually read the switch register correctly
        self.core.break_realtime()

        # update current configuration register with desired profile
        reg_cfg_update = reg_cfg_current & ~(7 << CFG_PROFILE)
        reg_cfg_update |= (DEFAULT_PROFILE & 7) << CFG_PROFILE
        dds_cpld.cfg_write(reg_cfg_update)
        dds_cpld.io_update.pulse_mu(64)
        self.core.break_realtime()

        ## update waveform
        # read ASF of current profile
        profile_data_mu = dds_dev.read64(_AD9910_REG_PROFILE7)
        ampl_curr_asf = np.int32((profile_data_mu >> 48) & 0x3FFF)
        self.core.break_realtime()

        # get new ftw via rpc
        ftw_update = self._return_setter_dds_ftw()
        self.core.break_realtime()

        # update device profile
        dds_dev.set_mu(ftw_update, asf=ampl_curr_asf, profile=DEFAULT_PROFILE)

    @kernel(flags={"fast-math"})
    def _setDDSFastASF(self) -> TNone:
        self.core.break_realtime()

        # get device
        index_dds = self._return_dds_num()
        self.core.break_realtime()
        dds_dev = self._dds_channels[index_dds]
        dds_cpld = dds_dev.cpld
        self.core.break_realtime()

        ## set default profile
        # extract current switch register status from urukul status register
        # note: necessary to prevent overwriting of existing switch configuration
        reg_sw = urukul_sta_rf_sw(dds_cpld.sta_read())
        reg_cfg_current = (dds_cpld.cfg_reg & ~0xF) | reg_sw
        # note: the following core.break_realtime is CRITICAL to ensuring
        # that we actually read the switch register correctly
        self.core.break_realtime()

        # update current configuration register with desired profile
        reg_cfg_update = reg_cfg_current & ~(7 << CFG_PROFILE)
        reg_cfg_update |= (DEFAULT_PROFILE & 7) << CFG_PROFILE
        dds_cpld.cfg_write(reg_cfg_update)
        dds_cpld.io_update.pulse_mu(64)
        self.core.break_realtime()

        ## update waveform
        # read FTW of current profile
        profile_data_mu = dds_dev.read64(_AD9910_REG_PROFILE7)
        freq_curr_ftw = np.int32(profile_data_mu & 0xFFFFFFFF)
        self.core.break_realtime()

        # get new asf via rpc
        asf_update = self._return_setter_dds_asf()
        self.core.break_realtime()

        # update device profile
        dds_dev.set_mu(freq_curr_ftw, asf=asf_update, profile=DEFAULT_PROFILE)

    @kernel(flags={"fast-math"})
    def _setDDSFastATT(self) -> TNone:
        self.core.break_realtime()

        # get device
        index_dds = self._return_dds_num()
        self.core.break_realtime()
        dds_dev = self._dds_channels[index_dds]
        self.core.break_realtime()

        # read CPLD attenuation register
        # note: necessary to ensure existing attenuations are stored
        att_curr = dds_dev.get_att_mu()
        self.core.break_realtime()

        # get new att via rpc
        att_update = self._return_setter_dds_att()
        self.core.break_realtime()

        # update device attenuation
        dds_dev.set_att_mu(att_update)

    @kernel(flags={"fast-math"})
    def _setDDSFastSW(self) -> TNone:
        self.core.break_realtime()

        # get device
        index_dds = self._return_dds_num()
        self.core.break_realtime()
        dds_dev = self._dds_channels[index_dds]
        self.core.break_realtime()
        channel_num = dds_dev.chip_select - 4

        # get switch status via rpc
        sw_state = self._return_setter_dds_sw()
        self.core.break_realtime()

        # read CPLD status register
        # note: necessary to ensure existing switch states are not overridden
        urukul_cfg = dds_dev.cpld.sta_read()
        self.core.break_realtime()

        # insert new switch status & update device
        sw_reg = urukul_sta_rf_sw(urukul_cfg)
        sw_reg &= ~(0x1 << channel_num)
        if sw_state:
            sw_reg |= (0x1 << channel_num)
        dds_dev.cpld.cfg_switches(sw_reg)
        self.core.break_realtime()

        # also set the TTL DDS switches
        if sw_state:
            dds_dev.sw.on()
        else:
            dds_dev.sw.off()
        self.core.break_realtime()


    """
    FAST - HOST-KERNEL COMMUNICATION RPCs
    """
    @rpc(flags={"async"})
    def _store_getter_dds_data(self, profile_data_mu: TInt64) -> TNone:
        self._dds_freq_get_ftw =    np.int32(profile_data_mu & 0xFFFFFFFF)
        # self._dds_phase_get_pow =   np.int32((profile_data_mu >> 32) & 0xFFFF)
        self._dds_ampl_get_asf =    np.int32((profile_data_mu >> 48) & 0x3FFF)

    @rpc(flags={"async"})
    def _store_getter_dds_att(self, att_mu: TInt32) -> TNone:
        self._dds_att_get_mu = att_mu

    @rpc(flags={"async"})
    def _store_getter_dds_sw(self, sw_status: TBool) -> TNone:
        self._dds_sw_get_status = sw_status

    @rpc
    def _return_dds_num(self) -> TInt32:
        return self._dds_num

    @rpc
    def _return_setter_dds_ftw(self) -> TInt32:
        return self._dds_freq_set_ftw

    @rpc
    def _return_setter_dds_asf(self) -> TInt32:
        return self._dds_ampl_set_asf

    @rpc
    def _return_setter_dds_att(self) -> TInt32:
        return self._dds_att_set_mu

    @rpc
    def _return_setter_dds_sw(self) -> TBool:
        return self._dds_sw_set_status

    @rpc(flags={"async"})
    def _debug_print(self, data) -> TNone:
        print('\n\t\tdebug: {}'.format(data))
    '''new faster functions meant to be used with precompile'''

    '''ttl precompile functions'''
    @autoreload
    def getTTLCountFastCounts(self, ttlcount_name: TStr, time_count_us: TFloat, num_samples: TInt32) -> TArray(TInt32, 1):
        """
        Get the number of TTL input events for a given time, averaged over a number of trials.
        """
        # get index of the desired TTL EdgeCounter within _ttlcount_channels
        try:
            self._ttlcount_num = self.ttlcount_dict_search_num[ttlcount_name]
        except Exception as e:
            raise Exception('Error: Invalid device name.')

        # set counting variables as class variables for RPC retrieval
        self._ttlcount_samples_set_mu = num_samples
        self._ttlcount_time_set_mu = self.core.seconds_to_mu(time_count_us * us)

        # call precompiled ttl counting function
        self._precompile_func_get_ttlcounts()

        # return count list
        return self._ttlcount_get_counts

    @kernel(flags={"fast-math"})
    def _getTTLCountFastCounts(self) -> TNone:
        self.core.break_realtime()

        # get device
        index_ttlcount = self._return_ttlcount_num()
        self.core.break_realtime()
        ttlcount_dev = self._ttlcount_channels[index_ttlcount]
        self.core.break_realtime()

        # get counting parameters via rpc
        num_samples, time_count_mu = self._return_setter_ttlcount_params()
        self.core.break_realtime()

        # create count storage array
        _count_store = [0] * num_samples

        # count!
        for i in range(num_samples):
            ttlcount_dev.gate_rising_mu(time_count_mu)
            _count_store[i] = ttlcount_dev.fetch_count()
            self.core.break_realtime()

        # get existing waveform from device
        self._store_getter_ttlcount_counts(_count_store)

    @rpc(flags={"async"})
    def _store_getter_ttlcount_counts(self, count_list: TList(TInt32)) -> TNone:
        self._ttlcount_get_counts = np.array(count_list)

    @rpc
    def _return_ttlcount_num(self) -> TInt32:
        return self._ttlcount_num

    @rpc
    def _return_setter_ttlcount_params(self) -> TTuple([TInt32, TInt64]):
        return self._ttlcount_samples_set_mu, self._ttlcount_time_set_mu
    '''ttl precompile functions'''

    def stopAPI(self):
        """
        Closes any opened devices.
        """
        self.device_manager.close_devices()

    def reset_connection(self):
        """
        Reestablishes a connection to artiq_master.
        """
        devices = DeviceDB(self.ddb_filepath)
        self.device_manager = DeviceManager(devices)
        self.device_db = devices.get_device_db()
        self._getDevices()

        # # note: only the core needs to be re-acquired
        # # since the kernel decorator looks for only it inside the class object
        self.core = self.device_manager.get("core")

        # re-precompile relevant functions
        self._getPrecompiledFunctions()


    '''
    SETUP
    '''
    def _getDevices(self):
        """
        Gets necessary device objects.
        """
        # get core
        self.core = self.device_manager.get("core")

        # store devices in dictionary where device
        # name is key and device itself is value
        self.ttlout_dict =          dict()
        self.ttlin_dict =           dict()
        self.ttlcounter_dict =      dict()
        self.dds_dict =             dict()
        self.urukul_dict =          dict()
        self.zotino =               None
        self.fastino =              None
        self.dacType =              None
        self.sampler =              None
        self.phaser =               None

        # tmp remove
        _dds_dict_search_counter =      0
        self.dds_dict_search_num =      dict()

        _ttlcount_dict_search_counter = 0
        self.ttlcount_dict_search_num = dict()
        # tmp remove

        # assign names and devices
        for name, params in self.device_db.items():

            # only get devices with named class
            if 'class' not in params:
                continue

            # set device as attribute
            devicetype = params['class']
            device = self.device_manager.get(name)
            if devicetype == 'TTLInOut':
                self.ttlin_dict[name] =     device
            elif devicetype == 'TTLOut':
                self.ttlout_dict[name] =    device
            elif devicetype == 'EdgeCounter':
                self.ttlcounter_dict[name] = device

                # tmp remove
                self.ttlcount_dict_search_num[name] = _ttlcount_dict_search_counter
                _ttlcount_dict_search_counter += 1
                # tmp remove

            elif devicetype == 'AD9910':
                self.dds_dict[name] = device

                # tmp remove
                self.dds_dict_search_num[name] = _dds_dict_search_counter
                _dds_dict_search_counter += 1
                # tmp remove

            elif devicetype == 'CPLD':
                self.urukul_dict[name] = device
            elif devicetype == 'Zotino':
                # need to specify both device types since
                # all kernel functions need to be valid
                self.zotino =   device
                self.fastino =  device
                self.dacType =  devicetype
            elif devicetype == 'Fastino':
                self.fastino =  device
                self.zotino =   device
                self.dacType =  devicetype
            elif devicetype == 'Sampler':
                self.sampler =  device
            elif devicetype == 'Phaser':
                self.phaser =   device

        # holder objects for dds channels
        # these are needed so we can iterate devices in kernel functions
        # todo: ensure somehow that values still correspond to their index
        self._dds_channels =    list(self.dds_dict.values())
        self._dds_boards =      list(self.urukul_dict.values())
        self._ttlcount_channels =   list(self.ttlcounter_dict.values())

        # set all DDSs and Urukuls as class attributes
        for dev_name in (list(self.dds_dict.keys()) + list(self.urukul_dict.keys())):
            setattr(self, dev_name, self.device_manager.get(dev_name))


    '''
    TTL FUNCTIONS
    '''
    @autoreload
    def setTTL(self, ttlname: TStr, state: TBool) -> TNone:
        """
        Manually set the state of a TTL.
        """
        try:
            dev = self.ttlout_dict[ttlname]
        except Exception as e:
            raise Exception('Invalid device name.')

        self._setTTL(dev, state)

    # @kernel(flags={"fast-math"})
    @kernel
    def _setTTL(self, dev, state: TInt32) -> TNone:
        self.core.break_realtime()
        if state:
            dev.on()
        else:
            dev.off()

    def getTTL(self, ttlname):
        """
        Manually set the state of a TTL.
        """
        try:
            dev = self.ttlin_dict[ttlname]
        except Exception as e:
            raise Exception('Invalid device name.')
        self._getTTL(dev)

    @kernel(flags={"fast-math"})
    def _getTTL(self, dev) -> TNone:
        self.core.break_realtime()
        return dev.sample_get_nonrt()

    @autoreload
    def counterTTL(self, ttlname: TStr, time_us: TFloat, trials: TInt32) -> TArray(TInt64, 1):
        """
        Get the number of TTL input events for a given time, averaged over a number of trials.
        """
        try:
            dev = self.ttlcounter_dict[ttlname]
        except Exception as e:
            raise Exception('Error: Invalid device name.')

        # convert us to mu
        time_mu = self.core.seconds_to_mu(time_us * us)
        # create holding structures for counts
        setattr(self, "ttl_counts_array", np.zeros(trials))
        # get counts
        self._counterTTL(dev, time_mu, trials)
        # delete holding structure
        tmp_arr = self.ttl_counts_array
        delattr(self, "ttl_counts_array")
        return tmp_arr

    @kernel(flags={"fast-math"})
    def _counterTTL(self, dev, time_mu: TInt64, trials: TInt32) -> TNone:
        self.core.break_realtime()

        for i in range(trials):
            self.core.break_realtime()
            dev.gate_rising_mu(time_mu)
            self._recordTTLCounts(dev.fetch_count(), i)

    @rpc(flags={"async"})
    def _recordTTLCounts(self, time_value_mu: TInt64, index: TInt32) -> TNone:
        """
        Records values via rpc to minimize kernel overhead.
        """
        self.ttl_counts_array[index] = time_value_mu


    '''
    DDS FUNCTIONS
    '''
    @autoreload
    def initializeDDSAll(self) -> TNone:
        # initialize urukul cplds as well as dds channels
        device_list = list(self.urukul_dict.values())
        for device in device_list:
            self._initializeDDS(device)

    @autoreload
    def initializeDDS(self, dds_name: TStr) -> TNone:
        dev = self.dds_dict[dds_name]
        self._initializeDDS(dev)

    @kernel(flags={"fast-math"})
    def _initializeDDS(self, dev) -> TNone:
        self.core.break_realtime()
        dev.init()

    @autoreload
    def getDDSsw(self, dds_name: TStr) -> TInt32:
        """
        Get the RF switch status of a DDS channel.
        """
        dev = self.dds_dict[dds_name]
        # get channel number of dds
        channel_num = dev.chip_select - 4
        # get board status register
        urukul_cfg = self._getUrukulStatus(dev.cpld)
        # extract switch register from status register
        sw_reg = urukul_sta_rf_sw(urukul_cfg)
        return (sw_reg >> channel_num) & 0x1

    @autoreload
    def setDDSsw(self, dds_name: TStr, state: TBool) -> TNone:
        """
        Set the RF switch of a DDS channel.
        """
        # get channel number of dds on urukul
        dev = self.dds_dict[dds_name]
        channel_num = dev.chip_select - 4

        # extract switch register from urukul status register
        urukul_cfg = self._getUrukulStatus(dev.cpld)
        sw_reg = urukul_sta_rf_sw(urukul_cfg)

        # insert new switch status
        sw_reg &= ~(0x1 << channel_num)
        sw_reg |= (state << channel_num)

        # set switch status for whole board
        self._setDDSsw(dev, state, sw_reg)

    @kernel(flags={"fast-math"})
    def _setDDSsw(self, dds_dev, state, sw_reg) -> TNone:
        self.core.break_realtime()
        # set switches via configuration register
        dds_dev.cpld.cfg_switches(sw_reg)
        # set switches via DDS TTL
        if state is True:
            dds_dev.sw.on()
        elif state is False:
            dds_dev.sw.off()

    @autoreload
    def getDDS(self, dds_name: TStr) -> TTuple([TInt32, TInt32, TInt32]):
        """
        Get the frequency, amplitude, and phase values (in machine units) of a DDS channel.
        """
        dev = self.dds_dict[dds_name]
        # read in waveform values
        profiledata = self._readDDS64(dev, _AD9910_REG_PROFILE0)
        # separate register values into ftw, asf, and pow
        ftw = profiledata & 0xFFFFFFFF
        pow = (profiledata >> 32) & 0xFFFF
        asf = (profiledata >> 48)
        # ftw = 0XFFFFFFFF means not initialized
        ftw = 0 if (ftw == 0xFFFFFFFF) else ftw
        # asf = -1 or 0x8b5 means amplitude has not been set
        asf = 0 if (asf < 0) or ((asf == 0x8b5) & (ftw == 0x0)) else asf & 0x3FFF
        return np.int32(ftw), np.int32(asf), np.int32(pow)

    @autoreload
    def setDDS(self, dds_name, param: TStr, val: TInt32) -> TNone:
        """
        Manually set the frequency, amplitude, or phase values
        (in machine units) of a DDS channel.
        """
        dev = self.dds_dict[dds_name]
        # read in current parameters
        profiledata = self._readDDS64(dev, _AD9910_REG_PROFILE0)
        ftw = val if param == 'ftw' else (profiledata & 0xFFFFFFFF)
        asf = val if param == 'asf' else ((profiledata >> 48) & 0x3FFF)
        pow = val if param == 'pow' else ((profiledata >> 32) & 0xFFFF)
        # set DDS
        self._setDDS(dev, np.int32(ftw), np.int32(asf), np.int32(pow))

    @kernel(flags={"fast-math"})
    def _setDDS(self, dev, ftw: TInt32, asf: TInt32, pow: TInt32) -> TNone:
        self.core.break_realtime()
        dev.set_mu(ftw, pow_=pow, asf=asf)

    @autoreload
    def getDDSatt(self, dds_name: TStr) -> TInt32:
        """
        Set the DDS attenuation.
        """
        dev = self.dds_dict[dds_name]
        # get channel number of dds
        channel_num = dev.chip_select - 4
        att_reg = np.int32(self._getUrukulAtt(dev.cpld))
        # get only attenuation of channel
        return np.int32((att_reg >> (8 * channel_num)) & 0xFF)

    @autoreload
    def setDDSatt(self, dds_name: TStr, att_mu: TInt32) -> TNone:
        """
        Set the DDS attenuation.
        """
        dev = self.dds_dict[dds_name]
        # get channel number of dds
        channel_num = dev.chip_select - 4
        att_reg = self._setDDSatt(dev.cpld, channel_num, att_mu)

    @kernel(flags={"fast-math"})
    def _setDDSatt(self, cpld, channel_num, att_mu) -> TNone:
        self.core.break_realtime()
        cpld.bus.set_config_mu(0x0C, 32, 16, 2)

        # shift in zeros, shift out current value
        cpld.bus.write(0)
        cpld.bus.set_config_mu(0x0A, 32, 6, 2)
        delay_mu(10000)
        cpld.att_reg = cpld.bus.read()

        # remove old attenuator value for desired channel
        cpld.att_reg &= ~(0xff << (8 * channel_num))

        # add in new attenuator value
        cpld.att_reg |= (att_mu << (8 * channel_num))

        # shift in adjusted value and latch
        cpld.bus.write(cpld.att_reg)

    @autoreload
    def readDDS(self, dds_name, reg, length):
        """
        Read the value of a DDS register.
        """
        dev = self.dds_dict[dds_name]
        if length == 16:
            return self._readDDS16(dev, reg)
        elif length == 32:
            return self._readDDS32(dev, reg)
        elif length == 64:
            return self._readDDS64(dev, reg)

    @kernel(flags={"fast-math"})
    def _readDDS16(self, dev, reg):
        self.core.break_realtime()
        return dev.read16(reg)

    @kernel(flags={"fast-math"})
    def _readDDS32(self, dev, reg):
        self.core.break_realtime()
        return dev.read32(reg)

    @kernel(flags={"fast-math"})
    def _readDDS64(self, dev, reg):
        self.core.break_realtime()
        return dev.read64(reg)


    # DDS QUICK GET
    @autoreload
    def getDDSAll(self):
        """
        Quickly get frequency, amplitude, attenuation, and switch values
        (in machine units) for all DDS channels.
        """
        # create structures to hold params
        dds_params_processed = np.zeros([len(self.dds_dict), 4], dtype=np.int32)
        setattr(self, "channel_profiledata", [])
        setattr(self, "board_sw", [])
        setattr(self, "board_att", [])

        # get params!
        self._getDDSAll()

        # process channel params
        for i, profiledata in enumerate(self.channel_profiledata):
            ftw = profiledata & 0xFFFFFFFF
            ftw = 0 if (ftw == 0xFFFFFFFF) else np.int32(ftw)
            asf = profiledata >> 48
            asf = 0 if ((asf < 0) or ((asf == 0x8b5) & (ftw == 0x0))) else np.int32(asf & 0x3FFF)
            dds_params_processed[i][:2] = [ftw, asf]

        # process attenuation state
        board_att_tmp = []
        for i, att_state in enumerate(self.board_att):
            att_state = '{:08x}'.format(att_state)
            board_att_tmp += [int(att_state[i: i+2], base=16) for i in range(0, len(att_state), 2)][::-1]
        dds_params_processed[:, 2] = board_att_tmp

        # process switch state
        board_sw_tmp = []
        for i, sw_state in enumerate(self.board_sw):
            sw_state_processed = reversed('{:04b}'.format(sw_state))
            board_sw_tmp += list(map(int, sw_state_processed))
        dds_params_processed[:, 3] = board_sw_tmp

        # delete holding structures
        delattr(self, "channel_profiledata")
        delattr(self, "board_sw")
        delattr(self, "board_att")

        return dds_params_processed

    @kernel(flags={"fast-math"})
    def _getDDSAll(self) -> TNone:
        self.core.break_realtime()

        # read channel parameters
        for dev_ad9910 in self._dds_channels:
            self._recordParamsChannel(dev_ad9910.read64(_AD9910_REG_PROFILE0))
            self.core.break_realtime()

        # read board parameters
        for dev_cpld in self._dds_boards:
            cpld_sta_reg = dev_cpld.sta_read()
            self.core.break_realtime()
            cpld_att_reg = dev_cpld.get_att_mu()
            self._recordParamsBoard(cpld_sta_reg, cpld_att_reg)
            self.core.break_realtime()

    @rpc(flags={"async"})
    def _recordParamsChannel(self, profiledata) -> TNone:
        self.channel_profiledata.append(profiledata)

    @rpc(flags={"async"})
    def _recordParamsBoard(self, sw_state, att_state) -> TNone:
        self.board_sw.append(urukul_sta_rf_sw(sw_state))
        self.board_att.append(np.uintc(att_state))


    '''
    URUKUL FUNCTIONS
    '''
    @autoreload
    def initializeUrukul(self, urukul_name: TStr) -> TNone:
        """
        Initialize an Urukul board.
        """
        dev = self.urukul_dict[urukul_name]
        self._initializeUrukul(dev)

    @kernel(flags={"fast-math"})
    def _initializeUrukul(self, dev) -> TNone:
        self.core.break_realtime()
        dev.init()

    @kernel(flags={"fast-math"})
    def _getUrukulStatus(self, cpld):
        """
        Get the status register of an Urukul board.
        """
        self.core.break_realtime()
        return cpld.sta_read()

    @kernel(flags={"fast-math"})
    def _getUrukulAtt(self, cpld):
        """
        Get the attenuation register of an Urukul board.
        """
        self.core.break_realtime()
        return cpld.get_att_mu()

    # @kernel
    # def _getUrukulProfile(self, cpld):
    #     """
    #     Get the profile register of an Urukul board.
    #     """
    #     self.core.break_realtime()
    #     return (cpld.cfg_reg >> CFG_PROFILE) & 0x8


    '''
    DAC/ZOTINO FUNCTIONS
    '''
    @autoreload
    def initializeDAC(self) -> TNone:
        self._initializeDAC()

    @kernel(flags={"fast-math"})
    def _initializeDAC(self) -> TNone:
        """
        Initialize the DAC.
        """
        self.core.break_realtime()
        self.zotino.init()

    @autoreload
    def setZotino(self, channel_num, volt_mu):
        self._setZotino(channel_num, volt_mu)

    @kernel(flags={"fast-math"})
    def _setZotino(self, channel_num: TInt32, volt_mu: TInt32) -> TNone:
        """
        Set the voltage of a DAC register.
        """
        self.core.break_realtime()
        self.zotino.write_dac_mu(channel_num, volt_mu)
        self.zotino.load()

    @autoreload
    def setZotinoGain(self, channel_num: TInt32, gain_mu: TInt32) -> TNone:
        self._setZotinoGain(channel_num, gain_mu)

    @kernel(flags={"fast-math"})
    def _setZotinoGain(self, channel_num: TInt32, gain_mu: TInt32) -> TNone:
        """
        Set the gain of a DAC channel.
        """
        self.core.break_realtime()
        self.zotino.write_gain_mu(channel_num, gain_mu)
        self.zotino.load()

    @autoreload
    def setZotinoOffset(self, channel_num: TInt32, volt_mu: TInt32) -> TNone:
        self._setZotinoOffset(channel_num, volt_mu)

    @kernel(flags={"fast-math"})
    def _setZotinoOffset(self, channel_num: TInt32, volt_mu: TInt32) -> TNone:
        """
        Set the voltage of a DAC offset register.
        """
        self.core.break_realtime()
        self.zotino.write_offset_mu(channel_num, volt_mu)
        self.zotino.load()

    @autoreload
    def setZotinoGlobal(self, word):
        self._setZotinoGlobal(word)

    @kernel(flags={"fast-math"})
    def _setZotinoGlobal(self, word):
        """
        Set the OFSx registers on the AD5372.
        """
        self.core.break_realtime()
        self.zotino.write_offset_dacs_mu(word)

    @autoreload
    def readZotino(self, channel_num, address):
        return self._setZotinoGlobal(channel_num, address)

    @kernel(flags={"fast-math"})
    def _readZotino(self, channel_num, address):
        """
        Read the value of one of the DAC registers.
        :param channel_num: Channel to read from
        :param address: Register to read from
        :return: the value of the register
        """
        self.core.break_realtime()
        reg_val = self.zotino.read_reg(channel_num, address)
        return reg_val


    '''
    FASTINO FUNCTIONS
    '''
    @autoreload
    def initializeFastino(self) -> TNone:
        self._initializeFastino()

    @kernel(flags={"fast-math"})
    def _initializeFastino(self) -> TNone:
        """
        Initialize the Fastino.
        """
        self.core.break_realtime()
        self.fastino.init()

    @autoreload
    def setFastino(self, channel_num: TInt32, volt_mu: TInt32) -> TNone:
        self._setFastino(channel_num, volt_mu)

    @kernel(flags={"fast-math"})
    def _setFastino(self, channel_num: TInt32, volt_mu: TInt32) -> TNone:
        """
        Set the voltage of a Fastino register.
        """
        self.core.break_realtime()
        self.fastino.set_dac_mu(channel_num, volt_mu)
        self.fastino.update(1 << channel_num)
        self.core.break_realtime()

    @autoreload
    def readFastino(self, addr):
        return self._readFastino(addr)

    @kernel(flags={"fast-math"})
    def _readFastino(self, addr):
        self.core.break_realtime()
        return self.fastino.read(addr)

    @autoreload
    def continuousFastino(self, channel_num: TInt32) -> TNone:
        self._continuousFastino(channel_num)

    @kernel(flags={"fast-math"})
    def _continuousFastino(self, channel_num: TInt32) -> TNone:
        """
        Allows a Fastino channel to be updated continuously regardless of incoming data.
        """
        self.core.break_realtime()
        self.fastino.set_continuous(1 << channel_num)


    '''
    SAMPLER
    '''
    @autoreload
    def initializeSampler(self) -> TNone:
        """
        Initialize the Sampler.
        """
        self._initializeSampler()

    @kernel(flags={"fast-math"})
    def _initializeSampler(self) -> TNone:
        """
        Initialize the Sampler.
        """
        self.core.break_realtime()
        self.sampler.init()

    @autoreload
    def setSamplerGain(self, channel_num: TInt32, gain_mu: TInt32) -> TNone:
        """
        Set the gain for a sampler channel.
        :param channel_num: Channel to set
        :param gain_mu: Register to read from
        :return: the value of the register
        """
        self._setSamplerGain(channel_num, gain_mu)

    @kernel(flags={"fast-math"})
    def _setSamplerGain(self, channel_num: TInt32, gain_mu: TInt32) -> TNone:
        self.core.break_realtime()
        self.sampler.set_gain_mu(channel_num, gain_mu)

    @autoreload
    def getSamplerGains(self):
        # get raw gain register
        gains = self._getSamplerGains()
        gains = ('{:016b}'.format(gains))
        # convert to machine units
        gain_status_tmp = []
        gain_status_tmp += [int(gains[i: i+2], base=2) for i in range(0, len(gains), 2)]
        # reverse only at end since gains are ordered the other way
        gain_status_tmp = gain_status_tmp[::-1]
        return gain_status_tmp

    @kernel(flags={"fast-math"})
    def _getSamplerGains(self):
        """
        Get the gain of all sampler channels.
        :return: the sample channel gains.
        """
        self.core.break_realtime()
        return self.sampler.gains

    @autoreload
    def readSampler(self, rate_hz: TFloat, samples: TInt32) -> TArray(TInt32, 1):
        # create structures to hold results
        setattr(self, "sampler_dataset", np.zeros((samples, 8), dtype=np.int32))
        setattr(self, "sampler_holder", np.zeros(8, dtype=np.int32))
        # convert rate to mu
        time_delay_mu = self.core.seconds_to_mu(1 / rate_hz)
        # read samples!
        self._readSampler(time_delay_mu, samples)
        # delete holding structure
        tmp_arr = self.sampler_dataset
        delattr(self, "sampler_dataset")
        delattr(self, "sampler_holder")
        return tmp_arr

    @kernel(flags={"fast-math"})
    def _readSampler(self, time_delay_mu: TInt64, samples: TInt32) -> TNone:
        self.core.break_realtime()

        for i in range(samples):
            with parallel:
                with sequential:
                    self.sampler.sample_mu(self.sampler_holder)
                    self._recordSamplerValues(i, self.sampler_holder)
                delay_mu(time_delay_mu)

    @rpc(flags={"async"})
    def _recordSamplerValues(self, i: TInt32, value_arr: TArray(TInt32, 1)) -> TNone:
        """
        Records values via rpc to minimize kernel overhead.
        """
        self.sampler_dataset[i] = value_arr

