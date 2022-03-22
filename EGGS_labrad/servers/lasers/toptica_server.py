"""
### BEGIN NODE INFO
[info]
name = Toptica Server
version = 1.0
description = Talks to Toptica devices.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.server import LabradServer, setting
from twisted.internet.defer import returnValue, inlineCallbacks, DeferredLock

from toptica.lasersdk.client import Client, NetworkConnection


class TopticaServer(LabradServer):
    """
    Talks to Toptica devices.
    """

    name = 'Toptica Server'
    regKey = 'Toptica Server'
    device = None

    def initServer(self):
        # get DLC pro addresses from registry
        reg = self.client.registry
        pass
        # try:
        #     tmp = yield reg.cd()
        #     yield reg.cd(['', 'Servers', regKey])
        #     # todo: iteratively get all ip addresses
        #     node = yield reg.get('default_node')
        #     yield reg.cd(tmp)
        # except Exception as e:
        #     yield reg.cd(tmp)


    # DIRECT COMMUNICATION
    @setting(21, 'Direct Read', key='s', returns='s')
    def directRead(self, c, key):
        """
        Directly read the given parameter (verbatim).
        Arguments:
            key     (str)   : the parameter key to read from.
        """
        pass

    @setting(22, 'Direct Write', key='s', returns='s')
    def directWrite(self, c, key):
        """
        Directly write a value to a given parameter (verbatim).
        Arguments:
            key     (str)   : the parameter key to read from.
            value   (?)     : the value to set the parameter to
        """
        pass
#todo: errors

    # STATUS
    @setting(111, 'Device Info', chan='i', returns='(ss)')
    def deviceInfo(self, c, chan):
        """
        Returns key information about the specified laser channel.
        Returns:
            (str)   : the node
            (str)   : the port
        """
        if self.ser:
            return (self.serNode, self.port)
        else:
            raise Exception('No device selected.')


    # EMISSION
    @setting(211, 'Emission Interlock', chan='i', status='b', returns='v')
    def emissionInterlock(self, c, chan, status=None):
        """
        Get/set the status of the emission interlock.
        Arguments:
            chan        (int)   : the desired laser channel.
            status      (bool)  : the emission status of the laser head.
        Returns:
                        (bool)  : the emission status of the laser head.
        """
        pass


    # CURRENT
    @setting(311, 'Current Actual', chan='i', returns='v')
    def currentActual(self, c, chan):
        """
        Returns the actual current of the selected laser head.
        Arguments:
            chan        (int)   : the desired laser channel.
        Returns:
                        (float) : the current (in mA).
        """
        curr = yield self.device.get('laser1:dll:cc:current-act')
        returnValue(float(curr))

    @setting(312, 'Current Target', chan='i', curr='v', returns='v')
    def currentSet(self, c, chan, curr=None):
        """
        Get/set the target current of the selected laser channel.
        Arguments:
            curr    (float) : the target current (in mA).
        Returns:
                    (float) : the target current (in mA).
        """
        pass

    @setting(313, 'Current Max', curr='v', returns='v')
    def currentMax(self, c, curr=None):
        """
        Get/set the maximum current of the selected laser head.
        Arguments:
            curr    (float) : the maximum current (in mA).
        Returns:
                    (float) : the maximum current (in mA).
        """
        pass


    # TEMPERATURE
    @setting(321, 'Temperature Actual', returns='v')
    def tempActual(self, c):
        """
        Returns the actual temperature of the selected laser head.
        Returns:
            (float) : the temperature (in K).
        """
        pass

    @setting(322, 'Temperature Target', temp='v', returns='v')
    def tempSet(self, c, temp=None):
        """
        Get/set the target temperature of the selected laser head.
        Arguments:
            temp    (float) : the target temperature (in K).
        Returns:
                    (float) : the target temperature (in K).
        """
        pass

    @setting(323, 'Temperature Max', temp='v', returns='v')
    def tempMax(self, c, temp=None):
        """
        Get/set the maximum temperature of the selected laser head.
        Arguments:
            temp    (float) : the maximum temperature (in K).
        Returns:
                    (float) : the maximum temperature (in K).
        """
        pass


    # PIEZO
    @setting(411, 'th1', temp='v', returns='v')
    def th1(self, c, temp=None):
        """
        Get/set the maximum temperature of the selected laser head.
        Arguments:
            temp    (float) : the maximum temperature (in K).
        Returns:
                    (float) : the maximum temperature (in K).
        """
        pass



if __name__ == '__main__':
    from labrad import util
    util.runServer(TopticaServer())
