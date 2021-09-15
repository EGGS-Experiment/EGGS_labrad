"""
### BEGIN NODE INFO
[info]
name = Math Server
version = 0.1
description = Provides math functions for data processing

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from __future__ import absolute_import
from twisted.internet.defer import inlineCallbacks, returnValue
from labrad.server import LabradServer, setting

import numpy as np

class MathServer(LabradServer):
    """Provides math functions for data processing (e.g. FFT)"""

    name = 'Math Server'

    #FFT
    @setting(100, dataset='i', returns='(vvvvsvss)')
    def fft(self, c, channel):
        """
        FFT a dataset

        Args:
            dataset (int): dataset to be fft'd

        Returns:
            Tuple of (probeAtten, termination, scale, position, coupling, bwLimit, invert, units)
        """
        return np.fft.fft(dataset)


if __name__ == '__main__':
    from labrad import util
    util.runServer(MathServer())