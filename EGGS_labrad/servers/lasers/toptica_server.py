"""
### BEGIN NODE INFO
[info]
name = Toptica Server
version = 1.0.1
description = Talks to Toptica devices.

[startup]
cmdline = %PYTHON% %FILE%
timeout = 40

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.server import setting, Signal
from twisted.internet.defer import returnValue, inlineCallbacks
from toptica.lasersdk.client import Client, NetworkConnection

import logging
from EGGS_labrad.servers import PollingServer

CURRENTSIGNAL =         913548
TEMPERATURESIGNAL =     913549
PIEZOSIGNAL =           913550
# todo: send signal when values change
# todo: subscribe to when values change

DEVICE_TYPE_PREFIX = {
    'DLpro':        'dl',
    'BoosTApro':    'amp',
}


class TopticaServer(PollingServer):
    """
    Talks to Toptica devices.
    """
    name =      'Toptica Server'
    regKey =    'Toptica Server'

    devices =       {}  # stores DLC PRO device objects
    device_params = {}  # stores parameters for the DLC pro channels
    channels =      {}  # stores the in-use channels on each DLC PRO


    '''
    SIGNALS
    '''
    current_update =        Signal(CURRENTSIGNAL, 'signal: current updated', '(iv)')
    temperature_update =    Signal(TEMPERATURESIGNAL, 'signal: temperature updated', '(iv)')
    piezo_update =          Signal(PIEZOSIGNAL, 'signal: piezo updated', '(iv)')


    '''
    STARTUP/SHUTDOWN
    '''
    @inlineCallbacks
    def initServer(self):
        """
        Gets device information from LabRAD registry, then attempts to connect to them.
        """
        super().initServer()

        '''GET AVAILABLE DLC PRO DEVICE INFORMATION FROM REGISTRY'''
        # get DLC pro addresses from registry
        reg = self.client.registry
        ip_addresses = {}

        try:
            # attempt to access registry files for the toptica server
            conf_dir = yield reg.cd()
            yield reg.cd(['', 'Servers', self.regKey])
            _, ip_address_list = yield reg.dir()

            # get DLC PRO IP addresses
            for key in ip_address_list:
                # note: do error handling in case someone wrote the entries incorrectly
                try:
                    ip_addresses[key] = yield reg.get(key)
                except:
                    pass

            # get channel parameters
            yield reg.cd(['Channels'])
            _, channel_list = yield reg.dir()
            for channel_num in channel_list:
                # note: do error handling in case someone wrote the entries incorrectly
                try:
                    dev_params = yield reg.get(channel_num)
                    self.channels[int(channel_num)] = {'dev_params': dev_params}
                except:
                    pass

        finally:
            # return to the root directory
            yield reg.cd(conf_dir)


        '''CONNECT TO DLC PRO DEVICES'''
        # # tmp remove - for debugging
        # logging.getLogger('toptica.lasersdk.asyncio.connection').disabled = True
        # # tmp remove - for debugging

        # attempt connection to DLC PRO devices
        invalid_devices = []
        for name, ip_address in ip_addresses.items():
            try:
                dev = Client(NetworkConnection(ip_address, timeout=2.))
                dev.open()
                self.devices[name] = dev
            except Exception as e:
                # store invalid device name for later deletion from self.channels
                invalid_devices.append(name)
                print("Device unavailable ({:}, {:}): {:}".format(name, ip_address, e))

        # remove all channels corresponding to invalid devices in self.channels
        for channel in tuple(self.channels.items()):
            chan_key, chan_info = channel
            if chan_info['dev_params'][0] in invalid_devices:
                del self.channels[chan_key]

        # attempt to get parameters for all lasers
        for chan_num in tuple(self.channels.keys()):
            try:
                # retrieve and store basic channel information
                chan_num = int(chan_num)
                self.channels[chan_num]['name'] = yield self._read(chan_num, 'product-name', prefix=None)
                dev_type = yield self._read(chan_num, 'type', prefix=None)
                self.channels[chan_num]['type'] = dev_type

                # prorgammatically retrieve and store other factory settings
                dev_info_dict = {
                    'wavelength': '{:s}:factory-settings:wavelength',
                    'current_threshold': '{:s}:factory-settings:threshold-current',
                    'current_max': '{:s}:factory-settings:cc:current-clip',
                    'temp_min': '{:s}:factory-settings:tc:temp-min',
                    'temp_max': '{:s}:factory-settings:tc:temp-max',
                }
                for k, v in dev_info_dict.items():
                    # note: do error handling in case device doesn't have parameter
                    try:
                        dev_param = yield self._read(chan_num, v.format(DEVICE_TYPE_PREFIX[dev_type]), prefix=None)
                    except Exception as e:
                        dev_param = None
                    self.channels[chan_num][k] = dev_param

            except Exception as e:
                # remove channel from list to prevent later errors
                del self.channels[chan_num]
                print('Error getting params (Channel {:}): {:}'.format(chan_num, e))
                print('Removing channel {:} from channel list.'.format(chan_num))

        # stop logging everything
        logging.getLogger('toptica.lasersdk.asyncio.connection').disabled = True

    def stopServer(self):
        """
        Close all devices on completion.
        """
        for device in self.devices.values():
            try:
                device.close()
            except:
                pass


    '''
    DIRECT COMMUNICATION
    '''
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
        resp = yield self._read(chan, key, prefix=None)
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
        yield self._write(chan, key, value, prefix=None)


    '''
    STATUS
    '''
    @setting(111, 'Device List', returns='?')
    def deviceList(self, c, chan):
        """
        Returns information of all connected devices.
        Returns:
                (int, str, int): (channel number, device name, center wavelength (-1 if N/A))
        """
        device_list = [(chan_num, chan_params['name'], str(chan_params.get('wavelength', -1)))
                       for chan_num, chan_params in self.channels.items()]
        return device_list

    @setting(112, 'Device Info', chan='i', returns='*(ss)')
    def deviceInfo(self, c, chan):
        """
        Returns key information about the specified laser channel.
        Returns:
                    *(str, str): a list of tuples (param_name, param_value).
        """
        if chan in self.channels.keys():
            param_dict = self.channels[chan]
            param_dict_values = map(str, param_dict.values())
            return list(zip(param_dict.keys(), param_dict_values))
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
        resp = yield self._read(chan, 'emission', prefix=None)
        returnValue(bool(resp))


    '''
    CURRENT FUNCTIONS
    '''
    @setting(311, 'Current Actual', chan='i', returns='v')
    def currentActual(self, c, chan):
        """
        Returns the actual current of the selected laser head.
        Arguments:
            chan        (int)   : the desired laser channel.
        Returns:
                        (float) : the current (in mA).
        """
        resp = yield self._read(chan, 'cc:current-act', prefix='type')
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
                yield self._write(chan, 'cc:current-set', curr, prefix='type')
        resp = yield self._read(chan, 'cc:current-set', prefix='type')
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
                yield self._write(chan, 'cc:current-clip', curr, prefix='type')
        resp = yield self._read(chan, 'cc:current-clip', prefix='type')
        returnValue(float(resp))


    '''
    TEMPERATURE FUNCTIONS
    '''
    @setting(321, 'Temperature Actual', chan='i', returns='v')
    def tempActual(self, c, chan):
        """
        Returns the actual temperature of the selected laser head.
        Arguments:
            chan    (int)   : the desired laser channel.
                    (float) : the temperature (in K).
        """
        resp = yield self._read(chan, 'tc:temp-act', prefix='type')
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
                raise Exception('Error: target temperature is set too high. Must be less than 50C.')
            else:
                yield self._write(chan, 'tc:temp-set', temp, prefix='type')
        resp = yield self._read(chan, 'tc:temp-set', prefix='type')
        returnValue(float(resp))

    @setting(323, 'Temperature Max', chan='i', temp='v', returns='v')
    def tempMax(self, c, chan, temp=None):
        """
        Get/set the maximum temperature of the selected laser head.
        Arguments:
            chan    (int)           : the desired laser channel.
            temp    (float)         : the temperatures bound (maximum) in K.
        Returns:
                    (float)         : the temperatures bound (maximum) in K.
        """
        if temp is not None:
            if (temp <= 15) or (temp >= 50):
                raise Exception('Error: maximum temperature must not exceed factory maximum settings.')
            else:
                yield self._write(chan, 'tc:limits:temp-max', temp, prefix='type')
        resp = yield self._read(chan, 'tc:limits:temp-max', prefix='type')
        returnValue(float(resp))


    '''
    PIEZO FUNCTIONS
    '''
    @setting(411, 'Piezo Actual', chan='i', returns='v')
    def piezoActual(self, c, chan):
        """
        Returns the actual piezo voltage of the selected laser head.
        Arguments:
            chan    (int)   : the desired laser channel.
        Returns:
                    (float) : the piezo voltage (in V).
        """
        resp = yield self._read(chan, 'pc:voltage-act', prefix='type')
        returnValue(float(resp))

    @setting(412, 'Piezo Set', chan='i', voltage='v', returns='v')
    def piezoSet(self, c, chan, voltage=None):
        """
        Get/set the target piezo voltage of the selected laser head.
        Arguments:
            chan        (int)   : the desired laser channel.
            voltage     (float) : the piezo voltage (in V).
        Returns:
                        (float) : the piezo voltage (in V).
        """
        if voltage is not None:
            if (voltage <= 15) or (voltage >= 150):
                raise Exception('Error: target voltage is set too high. Must be less than 150V.')
            else:
                yield self._write(chan, 'pc:voltage-set', voltage, prefix='type')
        resp = yield self._read(chan, 'pc:voltage-set', prefix='type')
        returnValue(float(resp))

    @setting(413, 'Piezo Max', chan='i', voltage='v', returns='v')
    def piezoMax(self, c, chan, voltage=None):
        """
        Get/set the maximum voltage of the selected laser head.
        Arguments:
            chan        (int)   : the desired laser channel.
            voltage     (float) : the maximum piezo voltage (in V).
        Returns:
                        (float) : the maximum piezo voltage (in V).
        """
        if voltage is not None:
            if (voltage <= 15) or (voltage >= 150):
                raise Exception('Error: maximum temperature must not exceed factory maximum settings.')
            else:
                yield self._write(chan, 'pc:voltage-max', voltage, prefix='type')
        resp = yield self._read(chan, 'pc:voltage-max', prefix='type')
        returnValue(float(resp))


    '''
    SCAN FUNCTIONS
    '''
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
            yield self._write(chan, 'scan:enabled', status, prefix=None)
        resp = yield self._read(chan, 'scan:enabled', prefix=None)
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
        mode_to_output = {1: 51, 2: 56, 3: 50}
        if mode is not None:
            if mode not in (0, 1, 2):
                raise Exception("Error: invalid scan mode. Must be one of (0, 1, 2).")
            yield self._write(chan, 'scan:output-channel', mode_to_output[mode], prefix=None)
        resp = yield self._read(chan, 'scan:output-channel', prefix=None)
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
            yield self._write(chan, 'scan:signal-type', shape, prefix=None)
        resp = yield self._read(chan, 'scan:signal-type', prefix=None)
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
            yield self._write(chan, 'scan:amplitude', amp, prefix=None)
        resp = yield self._read(chan, 'scan:amplitude', prefix=None)
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
            yield self._write(chan, 'scan:offset', offset, prefix=None)
        resp = yield self._read(chan, 'scan:offset', prefix=None)
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
            yield self._write(chan, 'scan:frequency', freq, prefix=None)
        resp = yield self._read(chan, 'scan:enabled', prefix=None)
        returnValue(resp)


    # FEEDBACK
    @setting(611, 'Feedback Mode', chan='i', mode='i', returns='i')
    def feedbackMode(self, c, chan, mode=None):
        """
        Assign an input channel for piezo control.
        Arguments:
            chan        (int)   : the desired laser channel.
            mode        (int)   : the parameter for feedback to control: (0 = Off, 1 = Current, 2 = Temperature, 3 = Piezo)
        Returns:
                        (int)   : the parameter for feedback to control
        """
        conv_dict = {1: 0, 2: 1, 3: 2, 4: 4}
        if mode is not None:
            if mode not in (1, 2, 3, 4):
                raise Exception('Error: input channel must be one of (1, 2, 3, 4).')
            else:
                # convert channel to device value
                mode = conv_dict[mode]
                yield self._write(chan, 'pc:external-input', mode, prefix='type')
        resp = yield self._read(chan, 'pc:external-input', prefix='type')
        returnValue(resp)

    @setting(612, 'Feedback Channel', chan='i', input_chan='i', returns='i')
    def feedbackChannel(self, c, chan, input_chan=None):
        """
        Assign an input channel for feedback.
        Arguments:
            chan        (int)   : the desired laser channel.
            input_chan  (int)   : the input channel for the feedback signal. Can be one of (1, 2, 3, 4).
        Returns:
                        (int)   : the input channel for the feedback signal.
        """
        conv_dict = {1: 0, 2: 1, 3: 2, 4: 4}
        if input_chan is not None:
            if input_chan not in (1, 2, 3, 4):
                raise Exception('Error: input channel must be one of (1, 2, 3, 4).')
            else:
                # convert channel to device value
                input_chan = conv_dict[input_chan]
                yield self._write(chan, 'pc:external-input', input_chan, prefix='type')
        resp = yield self._read(chan, 'pc:external-input', prefix='type')
        returnValue(resp)

    @setting(613, 'Feedback Factor', chan='i', factor='v', returns='v')
    def feedbackFactor(self, c, chan, factor=None):
        """
        Get/set the feedback input factor.
        Arguments:
            chan        (int)   : the desired laser channel.
            factor      (float) : the feedback input factor.
        Returns:
                        (float) : the feedback input factor.
        """
        if factor is not None:
            if (factor < 0.01) or (factor > 10):
                raise Exception('Error: ARC factor must be within [0.001, 10].')
            else:
                yield self._write(chan, 'pc:external-input:factor', factor, prefix='type')
        resp = yield self._read(chan, 'pc:external-input:factor', prefix='type')
        returnValue(resp)


    '''
    HELPER FUNCTIONS
    '''
    @inlineCallbacks
    def _read(self, chan, param, prefix):
    # def _read(self, chan, param, prefix="type"):

        # sanitize input
        if chan not in self.channels.keys():
            raise ValueError('Invalid channel: {}'.format(chan))

        # get target device
        dev_name, laser_num = self.channels[chan]['dev_params']
        dev = self.devices[dev_name]

        # add relevant prefixes to query string
        if prefix == "type":
            prefixstr = '{:s}:'.format(DEVICE_TYPE_PREFIX[self.channels[chan]['type']])
        elif prefix is None:
            prefixstr = ''

        # query device
        querystr = 'laser{:d}:{}{}'.format(laser_num, prefixstr, param)
        #print('\n\tDEBUG (_read): {}'.format(querystr))
        resp = yield dev.get(querystr)
        returnValue(resp)

    @inlineCallbacks
    def _write(self, chan, param, value, prefix):
    # def _write(self, chan, param, value, prefix="type"):
        # sanitize input
        if chan not in self.channels.keys():
            raise Exception('Error: invalid channel.')

        # get target device
        dev_name, laser_num = self.channels[chan]['dev_params']
        dev = self.devices[dev_name]

        # add relevant prefixes to query string
        if prefix == "type":
            prefixstr = '{:s}:'.format(DEVICE_TYPE_PREFIX[self.channels[chan]['type']])
        elif prefix is None:
            prefixstr = ''

        # write to device
        writestr = 'laser{:d}:{}{}'.format(laser_num, prefixstr, param)
        # print('\n\tDEBUG (_write): {}'.format(writestr))
        yield dev.set(writestr, value)

    @inlineCallbacks
    def _poll(self):
        """
        Update listeners with actual values of current, temperature, and piezo voltage.
        """
        for chan_num in self.channels.keys():
            curr = yield self.currentActual(None, chan_num)
            temp = yield self.tempActual(None, chan_num)
            voltage = yield self.piezoActual(None, chan_num)
            self.current_update((chan_num, curr))
            self.temperature_update((chan_num, temp))
            self.piezo_update((chan_num, voltage))


if __name__ == '__main__':
    from labrad import util
    util.runServer(TopticaServer())
