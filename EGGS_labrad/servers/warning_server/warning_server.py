"""
### BEGIN NODE INFO
[info]
name = Warning Server
version = 1.1.0
description = Tracks serious errors/issues in LabRAD.
instancename = Warning Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
import numpy as np
from labrad.server import LabradServer, setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue
from EGGS_labrad.servers import ContextServer

from os import environ
from socket import gethostname
from labrad.wrappers import connectAsync
from EGGS_labrad.config.multiplexerclient_config import multiplexer_config
TMP_ID = 456983

# todo: make polling server and grab traces periodically
# todo: make connection to artiq so we can set warnings automatically


class WarningServer(ContextServer):
    """
    Warning Server
    todo: document
    """
    name = 'Warning Server'
    regKey = 'Warning Server'

    # SIGNALS
    wm_unlock = Signal(782346, 'signal: wavemeter unlock', '(is)')

    # STARTUP
    @inlineCallbacks
    def initServer(self):
        super().initServer()

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
        self.wm.signal__frequency_changed(TMP_ID)
        self.wm.addListener(listener=self.process_wavemeter_frequency, source=None, ID=TMP_ID)

        # self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        # yield self.cxn.manager.addListener(listener=self._serverConnect, source=None, ID=9898989)
        # self.cxn.manager.send_named_message('node.' + signal, tuple(kw.items()))

    def process_wavemeter_frequency(self, c, signal):
        chan, freq = signal
        if chan in self.wm_channels:
            if abs(freq - self.wm_channels[chan][1]) >= self.wm_tol_thz:
                # print("\n\t\tUNLOCK: {}".format(self.wm_channels[chan][0]))
                self.wm_unlock((chan, self.wm_channels[chan][0]))
                # todo: emit named message via labrad


if __name__ == '__main__':
    from labrad import util
    util.runServer(WarningServer())
