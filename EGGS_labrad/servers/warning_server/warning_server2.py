"""
### BEGIN NODE INFO
[info]
name = Warning Server 2
version = 1.0.0
description = Tracks serious errors/issues in LabRAD and forwards them to ARTIQ.
instancename = Warning Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.wrappers import connectAsync
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.servers import PollingServer
from EGGS_labrad.config.multiplexerclient_config import multiplexer_config

from os import environ
from socket import gethostname

import numpy as np
import scipy.ndimage as ndi




# todo: check voltage/error signal and look at RMS to predict errors
# todo: overnight safety - if no exp is running, stop everything and switch off relevant lasers; then send email
# todo: make connection to artiq so we can set warnings automatically via dataset
# todo: make it respond automatically by cancelling experiments
# todo: make it respond to a problem ONLY ONCE before needing to be reset


from enum import Enum
class WarningStatus(Enum):
    warning_disabled =  0
    warning_enabled =   1
    warning_triggered = 2
    unknown_error =     3


class WarningServer2(PollingServer):
    """
    Warning Server 2
    todo: document
    """
    name = 'Warning Server 2'
    regKey = 'Warning Server 2'

    # configure server polling
    POLL_ON_STARTUP =           True
    POLL_INTERVAL_ON_STARTUP =  5.
    POLL_INTERVAL_MIN =         2.
    POLL_INTERVAL_MAX =         60.

    # SIGNALS
    wm_warning = Signal(782346, 'signal: wavemeter warning', '(iss)')

    # STARTUP
    @inlineCallbacks
    def initServer(self):
        super().initServer()

        # store error status
        self.warning_status = WarningStatus.warning_enabled

        # create client connections
        yield self._setup_wavemeter()
        yield self._setup_artiq()

    @inlineCallbacks
    def _setup_wavemeter(self):
        """
        Establish LabRAD connection to the wavemeter computer.
        """
        # get wavemeter channel config
        self.wm_config = multiplexer_config
        self.wm_channels = {
            ch_config[0]: (ch_name, float(ch_config[1]))    # ch_num: (ch_name, lock_freq_thz)
            for ch_name, ch_config in self.wm_config.channels.items()
        }

        # set up wavemeter values
        self.wm_tol_thz = 0.000100  # 100 MHz unlock tolerance

        # create connection to wavemeter labrad
        self.cxn_wm = yield connectAsync(
            self.wm_config.ip, port=7682, name="{:s} ({:s})".format("WARNING_SERVER", gethostname()),
            username="", password=environ['LABRADPASSWORD']
        )

        # subscribe to wavemeter's frequency updats
        self.wm = self.cxn_wm.multiplexerserver
        self.wm.signal__frequency_changed(456983)
        self.wm.addListener(listener=self.process_wavemeter_frequency, source=None, ID=456983)

        # self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        # yield self.cxn.manager.addListener(listener=self._serverConnect, source=None, ID=9898989)
        # self.cxn.manager.send_named_message('node.' + signal, tuple(kw.items()))

    @inlineCallbacks
    def _setup_artiq(self):
        """
        Establish connection to ARTIQ master.
        """
        self.scheduler = Client('192.168.1.48', 3251, 'schedule')
        self.datasets = Client('192.168.1.48', 3251, 'dataset_db')

    @inlineCallbacks
    def _poll(self):
        """
        Poll function for this PollingServer's LoopingCall.
        """
        # check mode hopping via wavemeter trace
        self.process_wavemeter_trace()
        # todo: get wavemeter traces for all channels
        # todo: call process_wavemeter_trace
        pass


    '''
    SIGNALS/SLOTS
    '''
    @inlineCallbacks
    def process_wavemeter_trace(self):
        """
        Check wavemeter traces to ensure.
        """
        for chan in self.wm_channels:
            trace = yield self.wavemeter.get_wavemeter_pattern(chan)
            trace = trace[0]

            # apply minimum filter and extract "floor"
            tr_filt = ndi.minimum_filter1d(trace, 20)
            tr_floor = np.median(tr_filt)

            tr_filt2 = ndi.maximum_filter1d(trace, 20)
            tr_ceil = np.median(tr_filt2)

            # check trace for mode-hopping
            if tr_floor > 0.15 * np.max(trace):
                self.emergency_response((chan, self.wm_channels[chan][0],
                                         "Error: {:} mode hop".format(self.wm_channels[chan][0])))

    def process_wavemeter_frequency(self, c, signal):
        """
        Check wavemeter frequency updates to ensure all lasers are locked.
        """
        chan, freq = signal
        # todo: make it check against setpoint instead

        # respond only to channels we care about
        if chan in self.wm_channels:

            # check if channel has unlocked
            if abs(freq - self.wm_channels[chan][1]) >= self.wm_tol_thz:

                # initiate emergency response
                self.emergency_response((chan, self.wm_channels[chan][0],
                                         "Error: {:} unlocked".format(self.wm_channels[chan][0])))

    def process_wavemeter_DAC(self):
        """
        Check wavemeter servo DAC updates to ensure all lasers are locked.
        """
        pass

    def emergency_response(self, error_details, exp_shutdown=False):
        """
        Process emergency responses from different error conditions.
        Arguments:
            error_details: tuple of (channel_num, channel_name, error_message); emitted to listeners
            exp_shutdown: whether to shut down all ARTIQ experiments and place the system in an ion-safe state.
        """
        # send warning message to all interested listeneres
        self.wm_warning(error_details)
        # todo: send artiq dataset message

        # todo: initiate experiment shutdown?
        if exp_shutdown and :
            pass

    '''
    USER SETTINGS
    '''
    @setting(1, "Warning Status", returns='s')
    def warningStatus(self, c, status=None):
        """
        Reset the error alarm to allow server to respond to errors again.
        Arguments:
            status
        Returns:
            (str): the warning status.
        """
        if status in [stat.name for stat in (WarningStatus.enabled, WarningStatus.disabled)]:
            self.warning_status = WarningStatus[status]

        return self.warning_status.value


if __name__ == '__main__':
    from labrad import util
    util.runServer(WarningServer())
