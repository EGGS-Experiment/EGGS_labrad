# General class representing device server
# that communicates with serial ports.

# Handles writing, reading operations from
# serial port, as well as connecting.

# Subclass this if you are writing a device
# server that communicates using serial port

# Only connects to one port right now.
# Might be cleaner to keep it this way.

#===============================================================================
#
# 2011 - 01 - 26
# 
# Changed LabradServer.findSerial() to include serNode parameter.
# Default behavior is to use self.serNode attribute.
# 
# Added LabradServer._matchSerial() to check for serial server match,
# since we search both on initialization and on new server connecting.
# 
# Changed many docstrings to be more useful ( specify exceptions raised, etc. )
# 
# Added checkConnection decorator that modifies setting to raise exception
# if self.ser is empty.
#
#===============================================================================

#===============================================================================
# 2011 - 01 - 31
# 
# Changed SerialDeviceServer.initSerial and SerialDeviceServer.SerialConnection.__init__ to include timeout parameter.
# 
# Got rid of checkConnection decorator, replaced with method SerialDeviceServer.checkConnection.
#===============================================================================

#===============================================================================
# 2021 - 10 - 17
#
# Added COM port connection to SerialDeviceServer class instead of having all subclasses write their own
#===============================================================================

#===============================================================================
# 2021 - 11 - 10
#
# Added selectDevice and closeDevice to change which port device connects to on the fly
#
# Removed initServer stuff such that servers don't connect to ports on startup
#===============================================================================

#===============================================================================
# 2021 - 11 - 15
#
# Fixed flushinput and flushoutput functions
#
# Servers now flush input and output buffers on connection to device
#===============================================================================

#===============================================================================
# 2021 - 11 - 15
#
# Added read_all to ser for use with SLS
#===============================================================================

#===============================================================================
# 2021 - 11 - 22
#
# Servers now connect on startup if either node and port or node and regkey are
# specified. If neither, server still starts up, just without a connection.
#===============================================================================

# imports
from twisted.internet.defer import returnValue, inlineCallbacks, DeferredLock

from labrad.types import Error
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
                 1: 'Serial server not connected',
                 2: 'Attempting to use serial connection when not connected'}
    def __init__(self, code):
        self.code = code
    def __str__(self):
        return self.errorDict[self.code]

class PortRegError(SerialConnectionError):
    errorDict = {0: 'Registry not properly configured',
                 1: 'Key not found in registry',
                 2: 'No keys in registry'}


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
    port = None
    regKey = None
    serNode = None

    # serial connection parameters
    timeout = None
    baudrate = None
    bytesize = None
    parity = None

    # needed otherwise the whole thing breaks
    ser = None

    class SerialConnection(object):
        """
        Wrapper for our server's client connection to the serial server.
        @raise labrad.types.Error: Error in opening serial connection   
        """
        def __init__(self, ser, port, **kwargs):
            timeout = kwargs.get('timeout')
            baudrate = kwargs.get('baudrate')
            bytesize = kwargs.get('bytesize')
            parity = kwargs.get('parity')
            ser.open(port)
            if timeout is not None: ser.timeout(timeout)
            if baudrate is not None: ser.baudrate(baudrate)
            if bytesize is not None: ser.bytesize(bytesize)
            if parity is not None: ser.parity(parity)
            self.write = lambda s: ser.write(s)
            self.write_line = lambda s: ser.write_line(s)
            self.read = lambda x = 0: ser.read(x)
            self.read_line = lambda x = '': ser.read_line(x)
            self.read_as_words = lambda x = 0: ser.read_as_words(x) # changed here
            self.close = lambda: ser.close()
            self.flush_input = lambda: ser.flush_input()
            self.flush_output = lambda: ser.flush_output()
            self.ID = ser.ID
            # comm lock
            self.comm_lock = DeferredLock()
            self.acquire = lambda: self.comm_lock.acquire()
            self.release = lambda: self.comm_lock.release()


    # SETUP
    @inlineCallbacks
    def initServer(self):
        # call parent initserver to support further subclassing
        super().initServer()
        # open connection on startup if default node and port are specified
        if self.serNode and self.port:
            print('Default node and port specified. Connecting to device on startup.')
            try:
                serStr = yield self.findSerial(self.serNode)
                yield self.initSerial(serStr, self.port, baudrate=self.baudrate, timeout=self.timeout,
                                      bytesize=self.bytesize, parity=self.parity)
            except SerialConnectionError as e:
                self.ser = None
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
        if self.ser:
            yield self.ser.acquire()
            self.ser.close()
            self.ser.release()

    @inlineCallbacks
    def initSerial(self, serStr, port, **kwargs):
        """
        Initialize serial connection.
        
        Attempts to initialize a serial connection using
        given key for serial serial and port string.  
        Sets server's ser attribute if successful.
        
        @param serStr: Key for serial server
        @param port: Name of port to connect to
        
        @raise SerialConnectionError: Error code 1.  Raised if we could not create serial connection.
        """
        # set default timeout if not specified
        if kwargs.get('timeout') is None and self.timeout:
            kwargs['timeout'] = self.timeout
        # print connection status
        print('Attempting to connect at:')
        print('\tserver:\t%s' % serStr)
        print('\tport:\t%s' % port)
        print('\ttimeout:\t%s\n\n' % (str(self.timeout) if kwargs.get('timeout') is not None else 'No timeout'))

        # find relevant serial server
        cli = self.client
        try:
            # get server wrapper for serial server
            ser = cli.servers[serStr]
            # instantiate SerialConnection convenience class
            self.ser = self.SerialConnection(ser=ser, port=port, **kwargs)
            # clear input and output buffers
            yield self.ser.flush_input()
            yield self.ser.flush_output()
            print('Serial connection opened.')
        except Error:
            self.ser = None
            #print(str(Error))
            raise SerialConnectionError(1)

    @inlineCallbacks
    def getPortFromReg(self, regKey=None):
        """
        Find port string in registry given key.
        
        If you do not input a parameter, it will look for the first four letters of your name attribute in the registry port keys.
        
        @param regKey: String used to find key match.
        
        @return: Name of port
        
        @raise PortRegError: Error code 0.  Registry does not have correct directory structure (['','Ports']).
        @raise PortRegError: Error code 1.  Did not find match.
        """
        reg = self.client.registry
        # there must be a 'Ports' directory at the root of the registry folder
        try:
            tmp = yield reg.cd()
            yield reg.cd(['', 'Ports'])
            y = yield reg.dir()
            print(y)
            if not regKey:
                if self.name:
                    regKey = self.name[:4].lower()
                else:
                    raise SerialDeviceError('name attribute is None')
            portStrKey = filter( lambda x: regKey in x , y[1] )
            if portStrKey:
                portStrKey = portStrKey[0]
            else:
                raise PortRegError(1)
            portStrVal = yield reg.get(portStrKey)
            reg.cd(tmp)
            returnValue( portStrVal )
        except Error as e:
            reg.cd(tmp)
            if e.code == 17: raise PortRegError(0)

    @inlineCallbacks
    def selectPortFromReg(self):
        """
        Select port string from list of keys in registry
        
        @return: Name of port
        
        @raise PortRegError: Error code 0.  Registry not properly configured (['','Ports']).
        @raise PortRegError: Error code 1.  No port keys in registry.
        """
        reg = self.client.registry
        try:
            # change this back to 'Ports'
            yield reg.cd( ['', 'Ports'] )
            portDir = yield reg.dir()
            portKeys = portDir[1]
            if not portKeys: raise PortRegError( 2 )
            keyDict = {}
            map( lambda x , y: keyDict.update( { x:y } ) ,
                 [str( i ) for i in range( len( portKeys ) )] ,
                 portKeys )
            for key in keyDict:
                print(key, ':', keyDict[key])
            selection = None
            while True:
                print('Select the number corresponding to the device you are using:')
                selection = raw_input( '' )
                if selection in keyDict:
                    portStr = yield reg.get( keyDict[selection] )
                    returnValue(portStr)
        except Error as e:
            if e.code == 13: raise PortRegError(0)

    @inlineCallbacks
    def findSerial(self, serNode=None):
        """
        Find appropriate serial server
        
        @param serNode: Name of labrad node possessing desired serial port
        
        @return: Key of serial server
        
        @raise SerialConnectionError: Error code 0.  Could not find desired serial server.
        """
        if not serNode: serNode = self.serNode
        cli = self.client
        # look for servers with 'serial' and serNode in the name, take first result
        servers = yield cli.manager.servers()
        try:
            returnValue( [ i[1] for i in servers if self._matchSerial(serNode, i[1]) ][0] )
        except IndexError: raise SerialConnectionError(0)

    @staticmethod
    def _matchSerial(serNode, potMatch):
        """
        Checks if server name is the correct serial server
        
        @param serNode: Name of node of desired serial server
        @param potMatch: Server name of potential match
        
        @return: boolean indicating comparison result
        """
        serMatch = 'serial' in potMatch.lower()
        nodeMatch = serNode.lower() in potMatch.lower()
        return serMatch and nodeMatch

    def checkConnection(self):
        if not self.ser: raise SerialConnectionError(2)

    @inlineCallbacks
    def serverConnected(self, ID, name):
        """Check to see if we can connect to serial server now"""
        if self.ser is None and None not in (self.port, self.serNode) and self._matchSerial(self.serNode, name):
            yield self.initSerial(name, self.port)
            print('Serial server connected after we connected')

    def serverDisconnected(self, ID, name):
        """Close connection (if we are connected)"""
        if self.ser and self.ser.ID == ID:
            print('Serial server disconnected.  Relaunch the serial server')
            self.ser = None


    # SETTINGS
        # DEVICE SELECTION
    @setting(111111, 'Select Device', node='s', port='s', returns=['', '(ss)'])
    def selectDevice(self, c, node=None, port=None):
        """
        Attempt to connect to serial device on the given node and port.
        """
        # handle cases if connection already exists
        if self.ser:
            # empty call is getter if connection exists
            if (node is None) and (port is None):
                return (self.serNode, self.port)
            else:
                raise Exception('A serial device is already opened.')
        # set parameters if specified
        elif (node is not None) and (port is not None):
            self.serNode = node
            self.port = port
        # connect to default values if no args specified
        elif (node is None) and (port is None) and (self.serNode) and (self.port):
            pass
        # raise error if only node or port is specified
        else:
            raise Exception('Only one argument specified.')


        # try to find the serial server and connect to the designated port
        try:
            serStr = yield self.findSerial(self.serNode)
            yield self.initSerial(serStr, self.port, baudrate=self.baudrate, timeout=self.timeout,
                                  bytesize=self.bytesize, parity=self.parity)
        except SerialConnectionError as e:
            self.ser = None
            if e.code == 0:
                print('Could not find serial server for node: %s' % self.serNode)
                print('Please start correct serial server')
            elif e.code == 1:
                print('Error opening serial connection')
            else:
                raise Exception('Unknown connection error')
        except Exception as e:
            print(e)

    @setting(111112, 'Close Device', returns='')
    def closeDevice(self, c):
        if self.ser:
            self.ser.close()
            self.ser = None
            print('Serial connection closed')
        else:
            raise Exception('No device selected')


        # DIRECT SERIAL COMMUNICATION
    @setting(111113, 'Serial Query', data='s', returns='s')
    def serial_query(self, c, data):
        """Write any string and read the response."""
        yield self.ser.acquire()
        yield self.ser.write(data)
        resp = yield self.ser.read_line()
        self.ser.release()
        returnValue(resp)

    @setting(111114, 'Serial Write', data='s', returns='')
    def serial_write(self, c, data):
        """Directly write to the serial device."""
        yield self.ser.acquire()
        yield self.ser.write(data)
        self.ser.release()

    @setting(111115, 'Serial Read', returns='s')
    def serial_read(self, c):
        """Directly read the serial buffer."""
        yield self.ser.acquire()
        resp = yield self.ser.read()
        self.ser.release()
        returnValue(resp)
