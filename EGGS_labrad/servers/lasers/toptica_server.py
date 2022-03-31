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
from labrad.server import setting
from twisted.internet.defer import returnValue, inlineCallbacks

from toptica.lasersdk.client import Client, NetworkConnection


class TopticaServer(PollingServer):
    """
    Talks to Toptica devices.
    """

    name = 'Toptica Server'
    regKey = 'Toptica Server'
    devices = {}
    device_params = {}
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
                dev_params = yield reg.get(channel_num)
                self.channels[channel_num] = {'dev_params': dev_params}
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
        # get laser parameters
        for chan_num in self.channels.keys():
            try:
                fac_params = yield self._read(chan_num, 'dl:factory-settings')
                self.channels[chan_num]['name'] = yield self._read(chan_num, 'product-name')
                self.channels[chan_num]['wavelength'] = fac_params[0]
                self.channels[chan_num]['current_threshold'] = fac_params[1]
                self.channels[chan_num]['current_max'] = fac_params[3][2]
                self.channels[chan_num]['temp_min'] = fac_params[4][0]
                self.channels[chan_num]['temp_max'] = fac_params[4][1]
            except Exception as e:
                print(e)

    def stopServer(self):
        # close all devices on completion
        for device in self.devices.values():
            device.close()


    # DIRECT COMMUNICATION
    @setting(11, 'Device Read', chan='i', key='s', returns='s')
    def directRead(self, c, chan, key):
        """
        Directly read the given parameter (verbatim).
        Arguments:
            chan        (int)   : the desired laser channel.
            key         (str)   : the parameter key to read from.
        Returns:
                        (str)   : the device response.
        """
        resp = yield self._read(chan, key)
        returnValue(str(resp))

    @setting(12, 'Device Write', chan='i', key='s', value='?', returns='')
    def directWrite(self, c, chan, key, value):
        """
        Directly write a value to a given parameter (verbatim).
        Arguments:
            chan    (int)    : the desired laser channel.
            key     (str)   : the parameter key to read from.
            value   (?)     : the value to set the parameter to
        """
        yield self._write(chan, key, value)


    # STATUS
    # todo: errors
    # todo: param updates
    @setting(111, 'Device List', returns='?')
    def deviceList(self, c, chan):
        """
        Returns all connected laser heads.
        Returns:
                (int, str, int): (channel number, device name, center wavelength)
        """
        device_list = [(int(chan_num), chan_params['name'], chan_params['wavelength']) for chan_num, chan_params in self.channels.items()]
        return device_list

    @setting(112, 'Device Info', chan='i', returns='*(s?)')
    def deviceInfo(self, c, chan):
        """
        Returns key information about the specified laser channel.
        Returns: todo finish
        """
        chan = str(chan)
        if chan in self.channels.keys():
            param_dict = self.channels[chan]
            return list(zip(param_dict.keys(), str(param_dict.values())))
        else:
            raise Exception('Error: channel does not exist.')

    @setting(121, 'Emission', chan='i', returns='b')
    def emission(self, c, chan):
        """
        Get the emission status of a laser channel.
        Arguments:
            chan        (int)   : the desired laser channel.
        Returns:
                        (bool)  : the emission status of the laser head.
        """
        resp = yield self._read(chan, 'emission')
        returnValue(float(resp))


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
        resp = yield self._read(chan, 'dl:cc:current-act')
        returnValue(float(resp))

    @setting(312, 'Current Set', chan='i', curr='v', returns='v')
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
                raise Exception('Error: target current is set too high. Must be less than 200mA.')
            else:
                yield self._write(chan, 'dl:cc:current-set', curr)
        resp = yield self._read(chan, 'dl:cc:current-set')
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
                raise Exception('Error: target current is set too high. Must be less than 200mA.')
            else:
                yield self._write(chan, 'dl:cc:current-clip', curr)
        resp = yield self._read(chan, 'dl:cc:current-clip')
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
        resp = yield self._read(chan, 'dl:tc:temp-act')
        returnValue(float(resp))

    @setting(322, 'Temperature Set', chan='i', temp='v', returns='v')
    def tempSet(self, c, chan, temp=None):
        """
        Get/set the target temperature of the selected laser head.
        Arguments:
            chan    (int)   : the desired laser channel.
            temp    (float) : the target temperature (in K).
        Returns:
                    (float) : the target temperature (in K).
        """
        if temp is not None:
            if (temp <= 15) or (temp >= 50):
                raise Exception('Error: target temperature is set too high. Must be less than 200mA.')
            else:
                yield self._write(chan, 'dl:tc:temp-set', temp)
        resp = yield self._read(chan, 'dl:tc:temp-set')
        returnValue(float(resp))

    @setting(323, 'Temperature Max', chan='i', temp='(vv)', returns='(vv)')
    def tempMax(self, c, chan, temp=None):
        """
        Get/set the minimum and maximum temperatures of the selected laser head.
        Arguments:
            chan    (int)           : the desired laser channel.
            temp    (float, float)  : the temperatures bounds (minimum, maximum) in K.
        Returns:
                    (float)         : the temperatures bounds (minimum, maximum) in K.
        """
        if temp is not None:
            if temp[0] >= temp[1]:
                raise Exception('Error: target temperature is set too high. Must be less than 200mA.')
            elif (temp[0] <= 15) or (temp[1] >= 50):
                raise Exception('Error: minimum temperature must be lower than maximum temperature.')
            else:
                yield self._write(chan, 'dl:tc:limits:temp-min', temp[0])
                yield self._write(chan, 'dl:tc:limits:temp-max', temp[1])
        respMin = yield self._read(chan, 'dl:tc:limits:temp-min')
        respMax = yield self._read(chan, 'dl:tc:limits:temp-max')
        returnValue((float(respMin), float(respMax)))


    # PIEZO
    @setting(411, 'Piezo Toggle', chan='i', status='b', returns='b')
    def piezoToggle(self, c, chan, status=None):
        """
        Toggle piezo control.
        Arguments:
            chan        (int)   : the desired laser channel.
            status      (bool)  : whether piezo control is on or off.
        Returns:
                        (bool)  : whether piezo control is on or off.
        """
        if status is not None:
            yield self._write(chan, 'dl:pc:enabled', status)
        resp = yield self._read(chan, 'dl:pc:enabled')
        returnValue(resp)

    @setting(412, 'Piezo Channel', chan='i', input_chan='i', returns='i')
    def piezoChannel(self, c, chan, input_chan=None):
        """
        Assign an input channel for piezo control.
        Arguments:
            chan        (int)   : the desired laser channel.
            input_chan  (int)   : the input channel for the error signal.
        Returns:
                        (int)   : the input channel for the error signal.
        """
        conv_dict = {1: 0, 2: 1, 3: 2, 4: 4}
        if input_chan is not None:
            if input_chan not in (1, 2, 3, 4):
                raise Exception('Error: input channel must be one of (1, 2, 3, 4).')
            else:
                # convert channel to device value
                input_chan = conv_dict[input_chan]
                yield self._write(chan, 'dl:pc:external-input', input_chan)
        resp = yield self._read(chan, 'dl:pc:external-input')
        returnValue(resp)

    @setting(413, 'Piezo Factor', chan='i', factor='v', returns='v')
    def piezoFactor(self, c, chan, factor=None):
        """
        Get/set the piezo input factor.
        Arguments:
            chan        (int)   : the desired laser channel.
            factor      (float) : the piezo input factor
        Returns:
                        (float) : the piezo input factor
        """
        if factor is not None:
            if (factor < 0.01) or (factor > 10):
                raise Exception('Error: ARC factor must be within [0.01, 10].')
            else:
                yield self._write(chan, 'dl:pc:external-input:factor', factor)
        resp = yield self._read(chan, 'dl:pc:external-input:factor')
        returnValue(resp)

    @setting(414, 'Piezo Actual', chan='i', returns='v')
    def piezoActual(self, c, chan):
        """
        Returns the actual piezo voltage of the selected laser head.
        Arguments:
            chan    (int)   : the desired laser channel.
                    (float) : the piezo voltage (in V).
        """
        resp = yield self._read(chan, 'dl:pc:voltage-act')
        returnValue(float(resp))


    # SCAN
    @setting(511, 'Scan Toggle', chan='i', status='b', returns='b')
    def scanToggle(self, c, chan, status=None):
        """
        Toggle scan control.
        Arguments:
            chan        (int)   : the desired laser channel.
            status      (bool)  : whether scan control is on or off.
        Returns:
                        (bool)  : whether scan control is on or off.
        """
        if status is not None:
            yield self._write(chan, 'scan:enabled', status)
        resp = yield self._read(chan, 'scan:enabled')
        returnValue(resp)

    @setting(512, 'Scan Mode', chan='i', mode='b', returns='i')
    def scanMode(self, c, chan, mode=None):
        """
        Get/set the scan output.
        Arguments:
            chan        (int)   : the desired laser channel.
            mode        (int)   : the scan mode (1 = current, 2 = temperature, 3 = piezo).
        Returns:
                        (int)   : the scan mode (1 = current, 2 = temperature, 3 = piezo).
        """
        #todo: convert mode to actual mode number
        if mode is not None:
            if mode not in (0, 1, 2):
                raise Exception("Error: invalid scan mode. Must be one of (0, 1, 2).")
            yield self._write(chan, 'scan:output-channel', mode)
        resp = yield self._read(chan, 'scan:output-channel')
        returnValue(resp)

    @setting(513, 'Scan Shape', chan='i', shape='i', returns='i')
    def scanShape(self, c, chan, shape=None):
        """
        Get/set the scan amplitude.
        Arguments:
            chan        (int)   : the desired laser channel.
            shape       (int)   : the desired scan shape (0 = sine, 1 = triangle, 2 = triangle rounded).
        Returns:
                        (int)   : the desired scan shape (0 = sine, 1 = triangle, 2 = triangle rounded).
        """
        if shape is not None:
            if shape not in (0, 1, 2):
                raise Exception("Error: invalid scan shape. Must be one of (0, 1, 2).")
            yield self._write(chan, 'scan:signal-type', shape)
        resp = yield self._read(chan, 'scan:signal-type')
        returnValue(resp)

    @setting(521, 'Scan Amplitude', chan='i', amp='v', returns='v')
    def scanAmplitude(self, c, chan, amp=None):
        """
        Get/set the scan amplitude.
        Arguments:
            chan        (int)   : the desired laser channel.
            amp         (float) : the scan amplitude.
        Returns:
                        (float) : the scan amplitude.
        """
        if amp is not None:
            yield self._write(chan, 'scan:amplitude', amp)
        resp = yield self._read(chan, 'scan:amplitude')
        returnValue(resp)

    @setting(522, 'Scan Offset', chan='i', offset='v', returns='v')
    def scanOffset(self, c, chan, offset=None):
        """
        Get/set the scan offset.
        Arguments:
            chan        (int)   : the desired laser channel.
            offset      (float) : the scan offset value.
        Returns:
                        (float) : the scan offset value.
        """
        if offset is not None:
            yield self._write(chan, 'scan:offset', offset)
        resp = yield self._read(chan, 'scan:offset')
        returnValue(resp)

    @setting(523, 'Scan Frequency', chan='i', freq='v', returns='v')
    def scanFrequency(self, c, chan, freq=None):
        """
        Get/set the scan frequency.
        Arguments:
            chan        (int)   : the desired laser channel.
            freq        (float) : the scan frequency (in Hz).
        Returns:
                        (float) : the scan frequency (in Hz).
        """
        if freq is not None:
            yield self._write(chan, 'scan:frequency', freq)
        resp = yield self._read(chan, 'scan:enabled')
        returnValue(resp)


    # HELPER
    @inlineCallbacks
    def _read(self, chan, param):
        chan = str(chan)
        if chan not in self.channels.keys():
            raise Exception('Error: invalid channel.')
        dev_name, laser_num = self.channels[chan]['dev_params']
        dev = self.devices[dev_name]
        #print('laser{:d}:{}'.format(laser_num, param))
        resp = yield dev.get('laser{:d}:{}'.format(laser_num, param))
        returnValue(resp)

    @inlineCallbacks
    def _write(self, chan, param, value):
        chan = str(chan)
        if chan not in self.channels.keys():
            raise Exception('Error: invalid channel.')
        dev_name, laser_num = self.channels[chan]
        dev = self.devices[dev_name]
        #print('write: ', 'laser{:d}:{}'.format(laser_num, param), ', value: ', value)
        yield dev.set('laser{:d}:{}'.format(laser_num, param), value)


    # POLLING
    @inlineCallbacks
    def _poll(self):
        """
        Polls #todo finish.
        """
        pass
        # yield self.temperature_read(None, None)


if __name__ == '__main__':
    from labrad import util
    util.runServer(TopticaServer())
