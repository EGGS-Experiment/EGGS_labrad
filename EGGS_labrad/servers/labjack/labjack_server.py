"""
Copied over from the KRb experiment at JILA: https://github.com/krbjila/labrad_tools/blob/master/labjack/labjack_server.py
Added minor formatting changes.

### BEGIN NODE INFO
[info]
name = LabJack Server
version = 1.0.0
description = Connects to LabJack's T-series devices

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""
from labrad.units import WithUnit
from labrad.server import Signal, setting
from twisted.internet.defer import returnValue, inlineCallbacks, DeferredLock

from EGGS_labrad.servers import ContextServer

from labjack import ljm
# todo: comm lock
# todo: signals for updating

_LABJACK_DATA_TYPES = {
    'UINT16':   ljm.constants.UINT16,
    'UINT32':   ljm.constants.UINT32,
    'INT32':    ljm.constants.INT32,
    'FLOAT':    ljm.constants.FLOAT32,
}


class LabJackServer(ContextServer):
    """
    Talks to LabJack's T-series devices via the LJM module.
    """

    name =              'LabJack Server'
    regKey =            'LabJack Server'
    # device_address =    '192.168.1.78'

    # timeout = WithUnit(5.0, 's')
    # baudrate = 28800
    #
    # POLL_ON_STARTUP = False
    # POLL_INTERVAL_ON_STARTUP = 5

    # # SIGNALS
    # buffer_update = Signal(999999, 'signal: buffer_update', '(ss)')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create instance variables
        self.device_handle =    None
        self.comm_lock =        DeferredLock


    '''
    STARTUP & SHUTDOWN
    '''
    def initServer(self):
        """
        todo: document
        """
        # call parent initServer to support further subclassing
        super().initServer()

        # # attempt to get default device parameters from registry (this overrides hard-coded values)
        # if self.regKey is not None:
        #     print('RegKey specified. Looking in registry for default node and port.')
        #     try:
        #         ip_address = yield self.getPortFromReg(self.regKey)
        #         self.device_address = ip_address
        #     except Exception as e:
        #         print('Unable to find LabJack device address in registry. Using hard-coded values if they exist.')
        #
        # # open connection on startup if default address is specified
        # if self.device_address:
        #     print('Default LabJack address specified. Connecting to device on startup.')
        #     try:
        #         self.device_handle = ljm.openS("ANY", "ETHERNET", self.device_address)
        #     except Exception as e:
        #         self.device_handle = None
        #         print('Unable to connect to default LabJack device.')

    @inlineCallbacks
    def getPortFromReg(self, regDir=None):
        """
        Finds default node and port values in
        the registry given the directory name.

        @param regKey: String used to find key match.
        @return: Name of port
        @raise PortRegError: Error code 0.  Registry does not have correct directory structure (['','Ports']).
        @raise PortRegError: Error code 1.  Did not find match.
        """
        # todo: fix up and make usable
        reg = self.client.registry
        # There must be a 'Ports' directory at the root of the registry folder
        try:
            tmp = yield reg.cd()
            yield reg.cd(['', 'Servers', regDir])
            node = yield reg.get('default_node')
            port = yield reg.get('default_port')
            yield reg.cd(tmp)
            returnValue((node, port))
        except Exception as e:
            yield reg.cd(tmp)

    def stopServer(self):
        """
        Attempt to close the labjack connection before shutdown.
        """
        super().stopServer()

        # check to see if labjack device is connected
        if self.device_handle is not None:
            try:
                ljm.close(self.device_handle)
            except Exception as e:
                print('Warning: unable to close LabJack device handle: {}'.format(repr(e)))


    '''
    CONNECT
    '''
    @setting(1, 'Device List', returns='*(iii)')
    def device_list(self, c):
        """
        Get a list of available devices.
        """
        detected_devices = ljm.listAll(ljm.constants.dtTSERIES, ljm.constants.ctTCP)
        dev_models, dev_cxns, dev_serialnums = detected_devices[1:4]
        device_list = list(zip(dev_models, dev_cxns, dev_serialnums))
        return device_list

    @setting(2, 'Device Select', dev_specs='(iii)', returns='i')
    def device_select(self, c, dev_specs):
        """
        Select a device.
        """
        # do nothing if a device is already selected
        if self.device_handle is not None:
            raise Exception('Error: A device connection is already opened.')

        # open connection to device
        try:
            device_handle = ljm.open(*dev_specs)
        except Exception as e:
            print('Error: unable to connect to device: {}'.format(repr(e)))
            device_handle = -1

        self.device_handle = device_handle
        return device_handle

    @setting(3, 'Device Close', returns='')
    def device_close(self, c):
        """
        Closes the current labjack device.
        """
        if self.device_handle is not None:
            ljm.close(self.device_handle)
            self.device_handle = None
            print('Labjack connection closed.')
        else:
            raise Exception('No device selected.')

    @setting(4, 'Device Info', returns='i')
    def device_info(self, c):
        """
        Returns the currently connected device's handle.
        Returns:
            (int)   : the connected device's handle.
        """
        if self.device_handle is not None:
            return self.device_handle
        else:
            return -1


    '''
    READ
    '''
    @inlineCallbacks
    @setting(11, name='s', returns='v')
    def read_name(self, c, name):
        """
        Read a value from a named register on the LabJack.

        NOTE: READING FROM A REGISTER WITH THIS METHOD SETS THIS PORT TO HIGH REGARDLESS OF THE INITIAL VALUE
        """
        value = yield ljm.eReadName(self.device_handle, name)
        returnValue(value)

    @inlineCallbacks
    @setting(13, name='s', returns='i')
    def read_state(self, c, name):
        """
        Read a value from a DIO register on the LabJack.
        """
        # find the index from the port name given
        ind = int(''.join([letter for letter in name[::-1] if letter.isdigit()]))

        # get the values of all the DIO ports
        DIO_values = yield ljm.eReadName(self.device_handle, 'DIO_STATE')

        # return the value of the DIO port requested
        returnValue(int(bin(int(DIO_values))[-ind]))

    @inlineCallbacks
    @setting(15, address='i', data_type='s', returns='v')
    def read_address(self, c, address):
        """
        Read a value from a register on the LabJack.
        """
        # convert user input data type to labjack data type
        # todo
        value = yield ljm.eReadAddress(self.device_handle, address)
        returnValue(value)

    @inlineCallbacks
    @setting(17, names='*s', returns='*v')
    def read_names(self, c, names):
        """
        Read values from multiple named registers on the LabJack.
        """
        values = yield ljm.eReadNames(self.device_handle, len(names), names)
        returnValue(values)

    @inlineCallbacks
    @setting(19, addresses='*i', returns='*v')
    def read_addresses(self, c, addresses):
        """
        Read values from multiple registers on the LabJack.
        """
        # convert user input data type to labjack data type
        # todo
        values = yield ljm.eReadAddresses(self.device_handle, len(addresses), addresses)
        returnValue(values)


    '''
    WRITE
    '''
    @inlineCallbacks
    @setting(10, name='s', value='v')
    def write_name(self, c, name, value):
        """
        Write a value to a named register on the LabJack.
        """
        ljm.eWriteName(self.device_handle, name, value)

    @inlineCallbacks
    @setting(12, address='i', value='v')
    def write_address(self, c, address, value):
        """
        Write a value to a register on the LabJack.
        """
        # convert user input data type to labjack data type
        # todo
        ljm.eWriteAddress(self.device_handle, address, value)

    @inlineCallbacks
    @setting(14, names='*s', values='*v')
    def write_names(self, c, names, values):
        """
        Write values to multiple named registers on the LabJack.
        """
        ljm.eWriteNames(self.device_handle, len(names), names, values)

    @inlineCallbacks
    @setting(16, addresses='*i', values='*v')
    def write_addresses(self, c, addresses, values):
        """
        Write values to multiple registers on the LabJack.
        """
        # convert user input data type to labjack data type
        # todo
        ljm.eWriteAddresses(self.device_handle, len(addresses), addresses, values)


if __name__ == "__main__":
    from labrad import util
    util.runServer(LabJackServer())
