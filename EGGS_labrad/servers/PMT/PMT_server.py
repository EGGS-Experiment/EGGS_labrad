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
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.servers import ARTIQServer

from EGGS_labrad.servers.pmt import PMT_exp as DMA_EXP

_TTL_MAX_TIME_US = 10000
_TTL_MIN_TIME_US = 1
_RECORD_MAX_TIME_US = 100000
_RECORD_MIN_TIME_US = 10


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
        self.ttl_number = 0
        self.trigger_ttl_number = 1
        self.overexposed_ttl_number = 2
        self.trigger_status = False
        self.bin_time_us = 10
        self.reset_time_us = 10
        self.length_us = 1000
        self.edge_method = 'rising'
        # get all input TTLs
        artiq_devices = self.get_devices()
        self.available_ttls = []
        for name, params in artiq_devices.items():
            # only get devices with named class
            if ('class' in params) and (params['class'] == 'TTLInOut'):
                self.available_ttls.append(int(name[3:]))

    # STATUS
    @setting(121, 'Overexposed', returns='b')
    def overexposed(self, c):
        """
        Check whether PMT is overexposed.
        Returns:
            (bool)  :   whether the PMT is overexposed
        """
        ttl_name = 'ttl{:d}'.format(self.overexposed_ttl_number)
        overexposed_state = yield self.artiq.ttl_get(ttl_name)
        returnValue(overexposed_state)


    # HARDWARE
    @setting(211, 'TTL PMT', chan_num='i', returns='i')
    def PMTselect(self, c, chan_num=None):
        """
        Select the PMT TTL channel.
        Arguments:
            chan_num    (int)   : the TTL channel number for PMT input
        Returns:
                        (str)   : the input TTL device name
        """
        if chan_num is not None:
            if chan_num in self.available_ttls:
                self.ttl_number = chan_num
            else:
                raise Exception('Error: invalid TTL channel.')
        return self.ttl_number

    @setting(212, 'TTL Trigger', chan_num='i', returns='i')
    def triggerSelect(self, c, chan_num=None):
        """
        Select the trigger TTL channel.
        Arguments:
            chan_num    (int)   : the TTL channel number for PMT input
        Returns:
                        (int)   : trigger device name
        """
        if chan_num is not None:
            if chan_num in self.available_ttls:
                self.trigger_ttl_number = chan_num
            else:
                raise Exception('Error: invalid TTL channel.')
        return self.trigger_ttl_number

    @setting(213, 'Trigger Active', status='b', returns='b')
    def triggerActive(self, c, status=None):
        """
        Select the trigger TTL channel.
        Arguments:
            status      (bool)  : whether triggering should be active
        Returns:
                        (bool)  : triggering status
        """
        if status is not None:
            self.status = status
        return self.trigger_status

    @setting(221, 'TTL Available', returns='*i')
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
                self.bin_time_us = time_us
            else:
                raise Exception('Error: invalid delay time. Must be in [1us, 10ms].')
        return self.bin_time_us

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
                self.reset_time_us = time_us
            else:
                raise Exception('Error: invalid delay time. Must be in [1us, 10ms].')
        return self.reset_time_us

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
        Set the record time (in us).
        Arguments:
            time_us (int)   : the length of time to record for
        Returns:
                    (int)   : the length of time to record for
        """
        if time_us is not None:
            if (time_us > _RECORD_MIN_TIME_US) and (time_us < _RECORD_MAX_TIME_US):
                self.length_us = time_us
            else:
                raise Exception('Error: invalid ***todo')
        return self.length_us


    # RUN
    @setting(511, 'Program', returns='v')
    def program(self, c):
        """
        Program the PMT sequence onto core DMA.
        Returns:
            (int)   : the programming experiment RID
        """
        kwargs = {'ttl_number': self.ttl_number, 'trigger_ttl_number': self.trigger_ttl_number,
                  'trigger_status': self.trigger_status, 'bin_time_us': self.bin_time_us,
                  'reset_time_us': self.reset_time_us, 'length_us': self.length_us, 'edge_method': self.edge_method}
        ps_rid = self.runExperiment(self.dma_exp_filepath, kwargs)
        return ps_rid

    @setting(521, 'Start', returns='*v')
    def start(self, c):
        """
        Start acquisition by running the core DMA experiment.
        Returns:
                    (*v, *i)    : (time array, count array)
        """
        yield self.DMArun(self.dma_name)
        res = self.getDataset(self.dataset_name)
        returnValue(res)


if __name__ == '__main__':
    from labrad import util
    util.runServer(PMTServer())