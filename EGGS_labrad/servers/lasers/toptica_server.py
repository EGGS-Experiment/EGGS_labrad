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
from EGGS_labrad.servers import PollingServer
from labrad.server import LabradServer, setting
from twisted.internet.defer import returnValue, inlineCallbacks, DeferredLock

from toptica.lasersdk.client import Client, NetworkConnection


class TopticaServer(LabradServer):
    """
    Talks to Toptica devices.
    """

    name = 'Toptica Server'
    regKey = 'Toptica Server'
    devices = {}
    channels = {}

    @inlineCallbacks
    def initServer(self):
        super().initServer()
        # get DLC pro addresses from registry
        reg = self.client.registry
        ip_addresses = {}
        try:
            tmp = yield reg.cd()
            yield reg.cd(['', 'Servers', self.regKey])
            _, ip_address_list = yield reg.dir()
            # get DLC Pro ip addresses
            for key in ip_address_list:
                ip_addresses[key] = yield reg.get(key)
            # get channel parameters
            yield reg.cd(['Channels'])
            _, channel_list = yield reg.dir()
            for channel_num in channel_list:
                self.channels[channel_num] = yield reg.get(channel_num)
            yield reg.cd(tmp)
        except Exception as e:
            yield reg.cd(tmp)
        # create DLC Pro device objects
        for name, ip_address in ip_addresses.items():
            try:
                dev = Client(NetworkConnection(ip_address))
                dev.open()
                self.devices[name] = dev
            except Exception as e:
                print(e)

    def stopServer(self):
        # close all devices on completion
        for device in self.devices.values():
            device.close()


    # DIRECT COMMUNICATION
    @setting(11, 'Direct Read', key='s', returns='s')
    def directRead(self, c, key):
        """
        Directly read the given parameter (verbatim).
        Arguments:
            key     (str)   : the parameter key to read from.
        """
        pass

    @setting(12, 'Direct Write', key='s', returns='s')
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
        resp = yield self._read(str(chan), 'dl:cc:current-act')
        returnValue(float(resp))

    @setting(312, 'Current Target', chan='i', curr='v', returns='v')
    def currentSet(self, c, chan, curr=None):
        """
        Get/set the target current of the selected laser channel.
        Arguments:
            chan    (int)   : the desired laser channel.
            curr    (float) : the target current (in mA).
        Returns:
                    (float) : the target current (in mA).
        """
        if curr is not None:
            if (curr <= 0) or (curr >= 200):
                yield self._write(str(chan), 'dl:cc:current-set')
            else:
                raise Exception('Error: maximum current is set too high. Must be less than 200mA.')
        resp = yield self._read(str(chan), 'dl:cc:current-set')
        returnValue(float(resp))

    @setting(313, 'Current Max', chan='i', curr='v', returns='v')
    def currentMax(self, c, chan, curr=None):
        """
        Get/set the maximum current of the selected laser head.
        Arguments:
            chan    (int)   : the desired laser channel.
            curr    (float) : the maximum current (in mA).
        Returns:
                    (float) : the maximum current (in mA).
        """
        if curr is not None:
            if (curr <= 0) or (curr >= 200):
                yield self._write(str(chan), 'dl:cc:current-clip')
            else:
                raise Exception('Error: maximum current is set too high. Must be less than 200mA.')
        resp = yield self._read(str(chan), 'dl:cc:current-clip')
        returnValue(float(resp))


    # TEMPERATURE
    @setting(321, 'Temperature Actual', chan='i', returns='v')
    def tempActual(self, c, chan):
        """
        Returns the actual temperature of the selected laser head.
        Arguments:
            chan    (int)   : the desired laser channel.
                    (float) : the temperature (in K).
        """
        pass

    @setting(322, 'Temperature Target', chan='i', temp='v', returns='v')
    def tempSet(self, c, chan, temp=None):
        """
        Get/set the target temperature of the selected laser head.
        Arguments:
            chan    (int)   : the desired laser channel.
            temp    (float) : the target temperature (in K).
        Returns:
                    (float) : the target temperature (in K).
        """
        pass

    @setting(323, 'Temperature Max', chan='i', temp='v', returns='v')
    def tempMax(self, c, chan, temp=None):
        """
        Get/set the maximum temperature of the selected laser head.
        Arguments:
            chan    (int)   : the desired laser channel.
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


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls #.
        """
        pass
        # yield self.temperature_read(None, None)

    @inlineCallbacks
    def _read(self, chan, param):
        dev_name, laser_num = self.channels[chan]
        print(dev_name, laser_num)
        dev = self.devices[dev_name]
        print('laser{:d}:{}'.format(laser_num, param))
        resp = yield dev.get('laser{:d}:{}'.format(laser_num, param))
        returnValue(resp)

    @inlineCallbacks
    def _write(self, chan, param, value):
        dev_name, laser_num = self.channels[chan]
        dev = self.devices[dev_name]
        yield dev.set('laser{:d}:{}'.format(laser_num, param), value)


if __name__ == '__main__':
    from labrad import util
    util.runServer(TopticaServer())
