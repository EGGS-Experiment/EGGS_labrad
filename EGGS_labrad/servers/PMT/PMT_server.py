"""
### BEGIN NODE INFO
[info]
name = PMT Server
version = 1.0.0
description = Controls the Hamamatsu H10892 PMT via ARTIQ
instancename = PMT Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from numpy import linspace
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.servers import ARTIQServer
from EGGS_labrad.servers.pmt import PMT_exp as DMA_EXP

_TTL_MIN_TIME_US = 0.01
_TTL_MAX_TIME_US = 1000
_RECORD_MIN_TIME_US = 0.01
_RECORD_MAX_TIME_US = 100000


class PMTServer(ARTIQServer):
    """
    Controls the Hamamatsu H10892 PMT via ARTIQ.
    """

    name = 'PMT Server'
    regKey = 'PMTServer'

    dma_name = DMA_EXP._DMA_HANDLE
    dma_exp_filepath = DMA_EXP.__file__
    dataset_name = DMA_EXP._DATASET_NAME

    # SIGNALS
    # pressure_update = Signal(999999, 'signal: pressure update', '(ii)')

    def initServer(self):
        super().initServer()
        # declare PMT variables
        self.signal_ttl = 0
        self.trigger_ttl = 1
        self.overexposed_ttl = 2
        self.power_ttl = 4
        self.trigger_status = False
        self.time_bin_us = 10
        self.time_reset_us = 10
        self.time_total_us = 1000
        self.edge_method = 'rising'
        # get all input TTLs
        artiq_devices = self.get_devices()
        self.available_ttls = []
        for name, params in artiq_devices.items():
            # only get devices with named class
            if ('class' in params) and (params['class'] == 'TTLInOut'):
                # add only the TTL channel number
                self.available_ttls.append(int(name[3:]))


    # STATUS
    @setting(121, 'Overexposed', returns='b')
    def overexposed(self, c):
        """
        Check whether the PMT is overexposed.
        Returns:
            (bool)  :   whether the PMT is overexposed
        """
        ttl_name = 'ttl{:d}'.format(self.overexposed_ttl)
        # todo: set ttl to be input
        overexposed_state = yield self.artiq.ttl_get(ttl_name)
        returnValue(overexposed_state)


    # HARDWARE
    @setting(211, 'TTL PMT', chan_num='i', returns='i')
    def PMTselect(self, c, chan_num=None):
        """
        Select the PMT TTL channel.
        Arguments:
            chan_num    (int)   : the TTL channel number for PMT input.
        Returns:
                        (str)   : PMT input channel number.
        """
        if chan_num is not None:
            if chan_num in self.available_ttls:
                self.signal_ttl = chan_num
            else:
                raise Exception('Error: invalid TTL channel.')
        return self.signal_ttl

    @setting(212, 'TTL Trigger', chan_num='i', returns='i')
    def triggerSelect(self, c, chan_num=None):
        """
        Select the trigger TTL channel.
        Arguments:
            chan_num    (int)   : the TTL channel number for PMT input.
        Returns:
                        (int)   : trigger channel number.
        """
        if chan_num is not None:
            if chan_num in self.available_ttls:
                self.trigger_ttl = chan_num
            else:
                raise Exception('Error: invalid TTL channel.')
        return self.trigger_ttl

    @setting(213, 'TTL Overexposed', chan_num='i', returns='i')
    def overexposedSelect(self, c, chan_num=None):
        """
        Select the overexposed TTL channel.
        Arguments:
            chan_num    (int)   : the TTL channel number for overexposed input.
        Returns:
                        (int)   : overexposed channel number.
        """
        if chan_num is not None:
            if chan_num in self.available_ttls:
                self.overexposed_ttl = chan_num
            else:
                raise Exception('Error: invalid TTL channel.')
        return self.overexposed_ttl

    @setting(214, 'TTL Power', chan_num='i', returns='i')
    def powerSelect(self, c, chan_num=None):
        """
        Select the power TTL channel.
        Arguments:
            chan_num    (int)   : the TTL channel number for PMT power input.
        Returns:
                        (int)   : power input channel number.
        """
        if chan_num is not None:
            if chan_num in self.available_ttls:
                self.power_ttl = chan_num
            else:
                raise Exception('Error: invalid TTL channel.')
        return self.power_ttl

    @setting(221, 'Trigger Status', status=['b', 'i'], returns='b')
    def triggerStatus(self, c, status=None):
        """
        Set the status of triggering.
        Arguments:
            status      (bool)  : whether triggering should be active
        Returns:
                        (bool)  : triggering status
        """
        if type(status) == int:
            if status not in (0, 1):
                raise Exception('Error: invalid input. Value must be a boolean, 0, or 1.')
            else:
                self.trigger_status = status
        return self.trigger_status

    @setting(231, 'TTL Available', returns='*i')
    def ttlAvailable(self, c):
        """
        Get a list of available TTL channels.
        Returns:
            (*i)   : a list of available TTL channels.
        """
        return self.available_ttls


    # GATING
    @setting(311, 'Gating Time', time_us='v', returns='v')
    def gateTime(self, c, time_us=None):
        """
        Set the gate time.
        Arguments:
            time_us (int)   : the gate time in us
        Returns:
                    (int)   : the gate time in us
        """
        if time_us is not None:
            if (time_us >= _TTL_MIN_TIME_US) and (time_us <= _TTL_MAX_TIME_US):
                self.time_bin_us = time_us
            else:
                raise Exception('Error: invalid delay time. Must be in [1us, 10ms].')
        return self.time_bin_us

    @setting(312, 'Gating Delay', time_us='v', returns='v')
    def gateDelay(self, c, time_us=None):
        """
        Set the delay time between bins.
        Arguments:
            time_us (int)   : the delay time between bins in us
        Returns:
                    (int)   : the delay time between bins in us
        """
        if time_us is not None:
            if (time_us >= _TTL_MIN_TIME_US) and (time_us <= _TTL_MAX_TIME_US):
                self.time_reset_us = time_us
            else:
                raise Exception('Error: invalid delay time. Must be in [1us, 10ms].')
        return self.time_reset_us

    @setting(313, 'Gating Edge', edge_method='s', returns='s')
    def gateEdge(self, c, edge_method=None):
        """
        Set the edge detection for each count.
        Arguments:
            edge_method (str)   : the edge detection type. Must be one of ('rising', 'falling', 'both').
        Returns:
                        (str)   : the edge detection type
        """
        if edge_method is not None:
            if edge_method.lower() in ('rising', 'falling', 'both'):
                self.edge_method = edge_method
            else:
                raise Exception('Error: invalid edge type. Must be one of (rising, falling, both).')
        return self.edge_method


    # RECORDING
    @setting(411, 'Length', time_us='v', returns='v')
    def length(self, c, time_us=None):
        """
        Set the total record time (in us).
        This includes the delay between bins.
        Arguments:
            time_us (int)   : the length of time to record for
        Returns:
                    (int)   : the length of time to record for
        """
        if time_us is not None:
            if (time_us >= _RECORD_MIN_TIME_US) and (time_us <= _RECORD_MAX_TIME_US):
                self.time_total_us = time_us
            else:
                raise Exception('Error: invalid ***todo')
        return self.time_total_us


    # RUN
    @setting(511, 'Program', returns='v')
    def program(self, c):
        """
        Program the PMT sequence onto core DMA.
        Returns:
            (int)   : the programming experiment RID
        """
        kwargs = {
            'signal_ttl': self.signal_ttl, 'trigger_ttl': self.trigger_ttl, 'power_ttl': self.power_ttl,
            'trigger_status': self.trigger_status, 'time_bin_us': self.time_bin_us, 'time_reset_us': self.time_reset_us,
            'time_total_us': self.time_total_us, 'edge_method': self.edge_method
        }
        ps_rid = self.runExperiment(self.dma_exp_filepath, kwargs)
        return ps_rid

    @setting(521, 'Start', returns='*2v')
    def start(self, c):
        """
        Start acquisition by running the core DMA experiment.
        Returns:
                                (*v, *i): (time array, count array)
        """
        # run core DMA experiment
        yield self.DMArun(self.dma_name)
        # get dataset
        res = self.getDataset(self.dataset_name)
        # create time array
        num_bins = int(self.time_total_us / (self.time_bin_us + self.time_reset_us))
        t_arr = linspace(0, self.time_total_us, num_bins)
        returnValue([t_arr, res])


if __name__ == '__main__':
    from labrad import util
    util.runServer(PMTServer())