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

from labrad.units import WithUnit
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.artiq_server import ARTIQServer


class PMTServer(LabradServer):
    """
    Controls the Hamamatsu H10892 PMT via ARTIQ.
    """

    name = 'PMT Server'
    regKey = 'PMTServer'

    # SIGNALS
    pressure_update = Signal(999999, 'signal: pressure update', '(ii)')
    temperature_update = Signal(999998, 'signal: temperature update', '(iiii)')

    def __init__(self):
        super(PMTServer, self).__init__()
        self.exp_file = "%LABRAD_ROOT%\\lib\\servers\\pmt\\pmt_server.py"
        self.ttl_number = None
        self.trigger_ttl_number = None
        #todo: get list of ttlinout
        self.available_ttls = {}
        self.bin_time_us = 10
        self.reset_time_us = 10
        self.length_us = 1000
        self.edge_type = 'rising'
        self.dma_handle = None


    # HARDWARE
    @setting(11, 'Status', returns='*s')
    def status(self, c):
        """
        Get system status.
        """
        # create message
        cmd_msg = b'STA'
        #todo

    @setting(21, 'TTL Select', status='i', returns='s')
    def ttlSelect(self, c, chan_num=None):
        """
        Select the TTL channel.
        Arguments:
            chan_num    (bool)  : the TTL channel number for PMT input
        Returns:
                        (bool)  : the TTL channel number for PMT input
        """
        if chan_num in self.available_ttls:
            self.ttl_number = chan_num
        else:
            raise Exception('Error: invalid TTL channel.')
        return 'ttl_' + str(self.ttl_number)


    # GATING
    @setting(211, 'Gating Time', time_us='i', returns='i')
    def gateTime(self, c, time_us=None):
        """
        Set the gate time.
        Arguments:
            time_us (int)   : the gate time in us
        Returns:
                    (int)   : the gate time in us
        """
        if (time_us > 1) and (time_us < 1000):
            self.bin_time_us = time_us
        else:
            raise Exception('Error: invalid delay time. Must be in [1us, 1ms].')
        return self.bin_time_us

    @setting(212, 'Gating Delay', time_us='i', returns='i')
    def gateDelay(self, c, time_us=None):
        """
        Set the delay time between bins.
        Arguments:
            time_us (int)   : the delay time between bins in us
        Returns:
                    (int)   : the delay time between bins in us
        """
        if (time_us > 1) and (time_us < 1000):
            self.reset_time_us = time_us
        else:
            raise Exception('Error: invalid delay time. Must be in [1us, 1ms].')
        return self.reset_time_us

    @setting(221, 'Gating Edge', edge_type='s', returns='s')
    def gateEdge(self, c, edge_type=None):
        """
        Set the edge detection for each count.
        Arguments:
            edge_type   (str)   : the edge detection type. Must be one of ('rising', 'falling', 'both').
        Returns:
                        (str)   : the edge detection type
        """
        if edge_type.lower() in ('rising', 'falling', 'both'):
            self.edge_type = edge_type
        else:
            raise Exception('Error: invalid edge type. Must be one of (rising, falling, both).')
        return self.edge_type


    # ACQUISITION
    # todo: save dataset/return to wherever
    # todo: save to datavault
    # todo: trigger
    # todo: fixed record length
    @setting(311, 'DMA Program', returns='')
    def dmaProgram(self, c):
        """
        Program the PMT sequence onto Kasli.
        """
        # todo
        pass

    @setting(312, 'Linetrigger', status='b', chan_num='i', returns='(bi)')
    def dmaProgram(self, c, status=None, chan_num=None):
        """
        Configure the line trigger.
        Arguments:
            status      (bool)  : whether the linetrigger is active
            chan_num    (int)   : the input TTL channel for the linetrigger
        Return:
                        (bi)    : tuple of (status, chan_num)
        """
        if chan_num in self.available_ttls:
            self.trigger_ttl_number = chan_num
        elif chan_num is not None:
            raise Exception('Error: invalid TTL.')
        if status is not None:
            self.trigger_active = status
        return (self.trigger_active, self.trigger_ttl_number)

    @setting(321, 'Start', record_length_us='i', returns='s')
    def start(self, c, record_length_us=None):
        """
        Start acquisition.
        Arguments:
            record_length_us    (bool)  : the length of time to record in us
        Returns:
                                (*str)  : experiment run parameters.
        """
        # todo: tell artiq to start
        # todo: check if handle exists
        pass

    @setting(322, 'Stop', returns='')
    def stop(self, c, status=None):
        """
        Stop acquisition.
        """
        #todo: look if DMA running
        pass


if __name__ == '__main__':
    from labrad import util
    util.runServer(PMTServer())