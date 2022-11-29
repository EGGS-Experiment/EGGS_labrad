# General class representing device server
# that communicates with serial ports.

# Handles writing, reading operations from
# serial port, as well as connecting.

# Subclass this if you are writing a device
# server that communicates using serial port

# Only connects to one port right now.
# Might be cleaner to keep it this way.

# ===============================================================================
#
# 2011 - 01 - 26
#
# Changed LabradServer.findSerial() to include serNode parameter.
# Default behavior is to use c['Serial Node'] attribute.
#
# Added LabradServer._matchSerial() to check for serial server match,
# since we search both on initialization and on new server connecting.
#
# Changed many docstrings to be more useful ( specify exceptions raised, etc. )
#
# Added checkConnection decorator that modifies setting to raise exception
# if self.ser is empty.
#
# ===============================================================================

# ===============================================================================
# 2011 - 01 - 31
#
# Changed SerialDeviceServer.initSerial and SerialDeviceServer.SerialConnection.__init__ to include timeout parameter.
#
# Got rid of checkConnection decorator, replaced with method SerialDeviceServer.checkConnection.
# ===============================================================================

# ===============================================================================
# 2021 - 10 - 17
#
# Added COM port connection to SerialDeviceServer class instead of having all
# subclasses write their own
# ===============================================================================

# ===============================================================================
# 2021 - 11 - 10
#
# Added selectDevice and closeDevice to change which port we connect to on the fly.
#
# Removed initServer stuff such that servers don't connect to ports on startup.
# ===============================================================================

# ===============================================================================
# 2021 - 11 - 15
#
# Fixed flushinput and flushoutput functions.
#
# Servers now flush input and output buffers on connection to device.
# ===============================================================================

# ===============================================================================
# 2021 - 11 - 15
#
# Added read_all to ser for use with SLS.
# ===============================================================================

# ===============================================================================
# 2021 - 11 - 22
#
# Servers now connect on startup if either node and port or node and regkey are
# specified. If neither, server still starts up, just without a connection.
# ===============================================================================

# ===============================================================================
# 2021 - 12 - 06
#
# Added comm lock setting to SerialConnection class to allow atomic read/write.
# ===============================================================================

# ===============================================================================
# 2021 - 12 - 12
#
# selectDevice now accepts empty arguments, which returns the port and node
# if a connection already exists, and creates a new connection if a
# connection does not already exist and the port and node are already specified.
# ===============================================================================

# ===============================================================================
# 2021 - 12 - 19
#
# Added debug setting, which makes serial bus server print r/w.
#
# Direct serial communication settings can now choose EOL/length of read.
# ===============================================================================

# ===============================================================================
# 2022 - 01 - 21
#
# Added new setting "device_info" which returns node and port if a connection
# is opened.
#
# Empty call to device_select now does default connection instead.
# ===============================================================================

# ===============================================================================
# 2022 - 03 - 12
#
# Added back SelectPortFromReg function that gets default values
# from registry before looking to hardcoded server file values.
#
# Removed checkConnection function since it's a one-liner.
#
# Made serverConnected signal function call initSerial upon
# connection of required serial bus server.
# ===============================================================================

from twisted.internet.defer import returnValue, inlineCallbacks, DeferredLock

from labrad.errors import Error
from labrad.server import LabradServer, setting

__all__ = ["SerialDeviceError", "SerialConnectionError", "SerialDeviceServer"]


# ERROR CLASSES
class SerialDeviceError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class SerialConnectionError(Exception):
    errorDict = {0: 'Could not find serial server in list',
                 1: 'Could not connect to a serial device',
                 2: 'Attempting to use serial connection when not connected'}

    def __init__(self, code):
        self.code = code

    def __str__(self):
        return self.errorDict[self.code]


# DEVICE CLASS
class SerialDeviceServer(LabradServer):
    """
    Base class for serial device servers.

    Contains a number of methods useful for using labrad's serial server.
    Functionality comes from ser attribute, which represents a connection that performs reading and writing to a serial port.
    Subclasses should assign some or all of the following attributes:

    name: Something short but descriptive
    port: Name of serial port (Better to look this up in the registry using regKey and getPortFromReg())
    regKey: Short string used to find port name in registry
    serNode: Name of node running desired serial server.  Used to identify correct serial server.
    timeOut: Time to wait for response before giving up.
    """

    # node parameters
    name = 'SerialDevice'
    reg_key = None
    default_port = None
    default_node = None

    # serial connection parameters
    timeout = None

    baudrate = None
    bytesize = None
    parity = None
    stopbits = None

    serial_connection_dict = {}

    class SerialConnection(object):
        """
        Wrapper for our server's client connection to the serial server.
        @raise labrad.types.Error: Error in opening serial connection
        """

        def __init__(self, ser, context, port, **kwargs):
            # parse kwargs
            timeout = kwargs.get('timeout')
            baudrate = kwargs.get('baudrate')
            bytesize = kwargs.get('bytesize')
            parity = kwargs.get('parity')
            stopbits = kwargs.get('stopbits')
            self.ctxt = context
            # serial parameters

            ser.open(port, context=self.ctxt)

            if timeout is not None: ser.timeout(timeout, context=self.ctxt)
            if baudrate is not None: ser.baudrate(baudrate, context=self.ctxt)
            if bytesize is not None: ser.bytesize(bytesize, context=self.ctxt)
            if parity is not None: ser.parity(parity, context=self.ctxt)
            if stopbits is not None: ser.stopbits(stopbits, context=self.ctxt)
            # serial r/w
            self.write = lambda s: ser.write(s, context=self.ctxt)
            self.write_line = lambda s: ser.write_line(s, context=self.ctxt)
            self.read = lambda x=0: ser.read(x, context=self.ctxt)
            self.read_line = lambda x='': ser.read_line(x, context=self.ctxt)
            self.read_as_words = lambda x=0: ser.read_as_words(x, context=self.ctxt)
            # other
            self.close = lambda: ser.close(context=self.ctxt)
            self.flush_input = lambda: ser.flush_input(context=self.ctxt)
            self.flush_output = lambda: ser.flush_output(context=self.ctxt)
            self.ID = ser.ID
            # comm lock
            self.comm_lock = DeferredLock()
            self.acquire = lambda: self.comm_lock.acquire()
            self.release = lambda: self.comm_lock.release()
            # buffer
            self.buffer_size = lambda size: ser.buffer_size(size, context=self.ctxt)
            self.buffer_input_waiting = lambda: ser.in_waiting(context=self.ctxt)
            self.buffer_output_waiting = lambda: ser.out_waiting(context=self.ctxt)
            self.get_simulated_device_errors = lambda: ser.get_device_errors(context=self.ctxt)

    # SETUP
    @inlineCallbacks
    def initServer(self):
        # call parent initServer to support further subclassing
        super().initServer()
        # get default node and port from registry (this overrides hard-coded values)
        if self.reg_key is not None:
            print('RegKey specified. Looking in registry for default node and port.')

            node, port = yield self.getPortFromReg(self.reg_key)
            self.default_node = node
            self.default_port = port

        # open connection on startup if default node and port are specified

        if self.default_node and self.default_port:

            print('Default node and port specified. Connecting to device on startup.')
            try:
                serStr = yield self.findSerial(self.default_node)
                yield self.initSerial(serStr, self.default_port, timeout=self.timeout, baudrate=self.baudrate,
                                      bytesize=self.bytesize, parity=self.parity, stopbits=self.stopbits)
            except SerialConnectionError as e:
                if (self.default_node, self.default_port) in self.serial_connection_dict:
                    del self.serial_connection_dict[(self.default_node, self.default_port)]
                if e.code == 0:
                    print('Could not find serial server for node: %s' % self.serNode)
                    print('Please start correct serial server')
                elif e.code == 1:
                    print('Error opening serial connection')
                else:
                    raise Exception('Unknown connection error')
            except Error:
                # maybe check for serialutil.SerialException?
                print('Unknown connection error')
                raise

    @inlineCallbacks
    def stopServer(self):
        """
        Close serial connection before exiting.
        """
        super().stopServer()
        for conn in self.serial_connection_dict.values():
            yield conn.acquire()
            try:
                conn.close()
            finally:
                conn.release()

    def initContext(self, c):
        for node, port in self.serial_connection_dict:
            if self.default_node and self.default_port and self._matchSerial(self.default_node,
                                                                             node) and port == self.default_port:
                c['Serial Connection'] = self.serial_connection_dict[(node, port)]
                c['Serial Node'] = node
                c['Serial Port'] = port
                return
        c['Serial Connection'] = None
        c['Serial Node'] = None
        c['Serial Port'] = None

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

    # SERIAL
    @inlineCallbacks
    def initSerial(self, serStr, port, **kwargs):
        """
        Attempts to initialize a serial connection
        using a given key for the node and port string.
        Sets server's ser attribute if successful.

        @param serStr: Key for serial server
        @param port: Name of port to connect to
        @raise SerialConnectionError: Error code 1.  Raised if we could not create serial connection.
        """
        # set default timeout if not specified
        if kwargs.get('timeout') is None and self.default_timeout:
            kwargs['timeout'] = self.default_timeout
        # print connection status
        print('Attempting to connect at:')
        print('\tserver:\t%s' % serStr)
        print('\tport:\t%s' % port)
        print(
            '\ttimeout:\t%s\n\n' % (str(kwargs.get('timeout')) if kwargs.get('timeout') is not None else 'No timeout'))
        # find relevant serial server
        cli = self.client
        try:
            # get server wrapper for serial server
            ser = cli.servers[serStr]
            # instantiate SerialConnection convenience class
            self.serial_connection_dict[(serStr, port)] = self.SerialConnection(ser, self.client.context(), port,
                                                                                **kwargs)
            # clear input and output buffers
            yield self.serial_connection_dict[(serStr, port)].flush_input()
            yield self.serial_connection_dict[(serStr, port)].flush_output()
            print('Serial connection opened.')
        except Error:
            if (serStr, port) in self.serial_connection_dict:
                del self.serial_connection_dict[(serStr, port)]
            raise SerialConnectionError(1)

    @inlineCallbacks
    def findSerial(self, serNode=None):
        """
        Find appropriate serial server.

        @param serNode: Name of labrad node possessing desired serial port
        @return: Key of serial server
        @raise SerialConnectionError: Error code 0.  Could not find desired serial server.
        """
        if not serNode:
            serNode = self.default_node
        cli = self.client
        # look for servers with 'serial' and serNode in the name, take first result
        servers = yield cli.manager.servers()
        try:
            returnValue([i[1] for i in servers if self._matchSerial(serNode, i[1])][0])
        except IndexError:
            raise SerialConnectionError(0)

    @staticmethod
    def _matchSerial(serNode, potMatch):
        """
        Checks if server name is the correct serial server.

        @param serNode: Name of node of desired serial server
        @param potMatch: Server name of potential match
        @return: boolean indicating comparison result
        """
        serMatch = ('serial' in potMatch.lower())
        nodeMatch = serNode.lower() in potMatch.lower()
        return serMatch and nodeMatch

    # SIGNALS

    def serverConnected(self, ID, name):
        """
        Attempt to connect to last connected serial bus server upon server connection.
        """
        # check if we aren't connected to a device, port and node are fully specified,
        # and connected server is the required serial bus server
        if (c['Serial Connection'] is None) and self.default_port and self.default_node and (
        self._matchSerial(self.default_node, name)):
            print(name, 'connected after we connected.')
            yield self.deviceSelect(None)

    def serverDisconnected(self, ID, name):
        """
        Close serial device connection (if we are connected).
        """
        for bus_server in [ser for (ser, port) in self.serial_connection_dict]:
            if bus_server == name:
                print('Serial bus server ' + name + ' disconnected. Relaunch the serial server')
                for context_obj in self.contexts.values():
                    if 'Serial Connection' in context_obj.data and context_obj.data['Serial Connection'] and \
                            context_obj.data['Serial Node'] == name:
                        context_obj.data['Serial Connection'] = None
                        context_obj.data['Serial Port'] = None
                        context_obj.data['Serial Node'] = None
                for (node, port) in list(self.serial_connection_dict.keys()):
                    if node == name:
                        del self.serial_connection_dict[(node, port)]

    # SETTINGS

    # DEVICE SELECTION
    @setting(111111, 'Device Select', node='s', port='s', timeout='v[s]', baudrate='w', bytesize='w', parity='w',
             stopbits='w', returns=['', '(ss)'])
    def deviceSelect(self, c, node=None, port=None, timeout=None, baudrate=None, bytesize=None, parity=None,
                     stopbits=None):
        """
        Attempt to connect to serial device on the given node and port.
        Arguments:
            node    (str)   : the node to connect on
            port    (str)   : the port to connect to
        Returns:
                    (str,str): the connected node and port (empty if no connection)
        """
        # do nothing if device is already selected
        if 'Serial Connection' in c and c['Serial Connection']:
            raise Exception('A serial device is already opened.')
        # set parameters if specified
        elif (node is not None) and (port is not None):
            desired_node = node
            desired_port = port

        # connect to default values if no arguments at all
        elif ((node is None) and (port is None)) and (self.default_node and self.default_port):
            desired_node = self.default_node
            desired_port = self.default_port

        # raise error if only node or port is specified
        else:
            raise Exception('Insufficient arguments.')
        try:
            desired_node = yield self.findSerial(desired_node)
            if (desired_node, desired_port) not in self.serial_connection_dict:
                yield self.initSerial(desired_node, desired_port, timeout=self.timeout, baudrate=self.baudrate,
                                      bytesize=self.bytesize, parity=self.parity, stopbits=self.stopbits)
        except SerialConnectionError as e:
            if (desired_node, desired_port) in self.serial_connection_dict:
                del self.serial_connection_dict[(desired_node, desired_port)]
            if e.code == 0:
                print('Could not find serial server for node: %s' % desired_node)
                print('Please start correct serial server')
            elif e.code == 1:
                print('Error opening serial connection')
            else:
                print('Unknown connection error')
            raise e
        except Exception as e:
            self.ser = None
            print(e)
        c['Serial Connection'] = self.serial_connection_dict[(desired_node, desired_port)]
        c['Serial Node'] = desired_node
        c['Serial Port'] = desired_port
        return (c['Serial Node'], c['Serial Port'])

    @setting(111112, 'Device Close', returns='')
    def deviceClose(self, c):
        """
        Closes the current serial device.
        """
        if c['Serial Connection']:
            c['Serial Connection'].close()
            del self.serial_connection_dict[(c['Serial Node'], c['Serial Port'])]
            c['Serial Connection'] = None
            c['Serial Port'] = None
            c['Serial Node'] = None
            print('Serial connection closed.')
        else:
            raise Exception('No device selected.')

    @setting(111113, 'Connection Info', returns='(ss)')
    def connectionInfo(self, c):
        """
        Returns the currently connected serial device's
        node and port.
        Returns:
            (str)   : the node
            (str)   : the port
        """
        if c['Serial Connection']:
            return (c['Serial Node'], c['Serial Port'])
        else:
            return ("", "")

    # DIRECT SERIAL COMMUNICATION
    @setting(222223, 'Serial Query', data='s', stop=['i: read a given number of characters',
                                                     's: read until the given character'], returns='s')
    def serial_query(self, c, data, stop=None):
        """
        Write any string and read the response.
        Args:
            data    (str)   : the data to write to the device
            stop            : the stop parameter (either EOL character or the # of characters to read)
        Returns:
                    (str)   : the device response (stripped of EOL characters)
        """
        yield c['Serial Connection'].acquire()
        try:
            yield c['Serial Connection'].write(data)
            if stop is None:
                resp = yield c['Serial Connection'].read()
            elif type(stop) == int:
                resp = yield c['Serial Connection'].read(stop)
            elif type(stop) == str:
                resp = yield c['Serial Connection'].read_line(stop)
        finally:
            c['Serial Connection'].release()
        returnValue(resp)

    @setting(222224, 'Serial Write', data='s', returns='')
    def serial_write(self, c, data):
        """
        Directly write to the serial device.
        Args:
            data    (str)   : the data to write to the device
        """
        yield c['Serial Connection'].acquire()
        try:
            yield c['Serial Connection'].write(data)
        finally:
            c['Serial Connection'].release()

    @setting(222225, 'Serial Read', stop=['i: read a given number of characters',
                                          's: read until the given character'], returns='s')
    def serial_read(self, c, stop=None):
        """
        Directly read the serial buffer.
        Returns:
                    (str)   : the device response (stripped of EOL characters)
        """
        yield c['Serial Connection'].acquire()
        try:
            if stop is None:
                resp = yield c['Serial Connection'].read()
            elif type(stop) == int:
                resp = yield c['Serial Connection'].read(stop)
            elif type(stop) == str:
                resp = yield c['Serial Connection'].read_line(stop)
        finally:
            c['Serial Connection'].release()
        returnValue(resp)

    # HELPER
    @setting(222231, 'Serial Flush', returns='')
    def serial_flush(self, c):
        """
        Flush the serial input and output buffers.
        """
        yield c['Serial Connection'].acquire()
        try:
            yield c['Serial Connection'].flush_input()
            yield c['Serial Connection'].flush_output()
        finally:
            c['Serial Connection'].release()

    # HELPER
    @setting(222235, 'Get Simulated Device Errors', returns='*(sss)')
    def get_simulated_device_errors(self, c):
        """
        Flush the serial input and output buffers.
        """
        yield c['Serial Connection'].acquire()
        try:
            resp = yield c['Serial Connection'].get_simulated_device_errors()


        finally:
            c['Serial Connection'].release()
        returnValue(resp)
