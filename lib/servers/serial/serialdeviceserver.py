'''
Created on Dec 22, 2010

@author: christopherreilly
'''
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

#Imports
from twisted.internet.defer import returnValue, inlineCallbacks
from labrad.server import LabradServer, setting
from labrad.types import Error

#Error Classes
class SerialDeviceError( Exception ):
    def __init__( self, value ):
        self.value = value
    def __str__( self ):
        return repr( self.value )

class SerialConnectionError( Exception ):
    errorDict = {
        0:'Could not find serial server in list',
        1:'Serial server not connected',
        2:'Attempting to use serial connection when not connected'
        }
    def __init__( self, code ):
        self.code = code
    def __str__( self ):
        return self.errorDict[self.code]

class PortRegError(SerialConnectionError):
    errorDict = { 0:'Registry not properly configured' , 1:'Key not found in registry' , 2:'No keys in registry' }

#Device Class
NAME = 'SerialDevice'

class SerialDeviceServer(LabradServer):
    """
    Base class for serial device servers.
    
    Contains a number of methods useful for using labrad's serial server.
    
    Functionality comes from ser attribute, which represents a connection that performs reading and writing to a serial port. 
    
    subclasses should assign some or all of the following attributes:
    
    name: Something short but descriptive
    port: Name of serial port (Better to look this up in the registry using regKey and getPortFromReg())
    regKey: Short string used to find port name in registry
    serNode: Name of node running desired serial server.  Used to identify correct serial server.
    timeOut: Time to wait for response before giving up.
    """
    #node parameters
    name = NAME
    port = None
    regKey = None
    serNode = None

    #serial connection parameters
    timeout = None
    baudrate = None
    bytesize = None
    parity = None

    #can skip all of this and just initialize with a connection
    ser = None

    class SerialConnection():
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
            self.read = lambda x = 0: ser.read(x)
            self.read_until = lambda x = '\r': ser.read_until(x)
            self.read_as_words = lambda x = 0: ser.read_as_words(x) # changed here
            self.close = lambda: ser.close()
            self.flush_input = ser.flush_input()
            self.flush_output = ser.flush_output()
            self.ID = ser.ID

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
        if kwargs.get('timeout') is None and self.timeout: kwargs['timeout'] = self.timeout
        print('Attempting to connect at:')
        print('\tserver:\t%s' % serStr)
        print('\tport:\t%s' % port)
        print('\ttimeout:\t%s\n\n' % (str(self.timeout) if kwargs.get('timeout') is not None else 'No timeout'))
        cli = self.client
        try:
            # get server wrapper for serial server
            ser = cli.servers[serStr]
            # instantiate SerialConnection convenience class
            self.ser = self.SerialConnection(ser=ser, port=port, **kwargs)
            print('Serial connection opened.')
            #clear input and output buffers
            yield self.ser.flush_input()
            yield self.ser.flush_output()
        except Error:
            self.ser = None
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
        #There must be a 'Ports' directory at the root of the registry folder
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
            #change this back to 'Ports'
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
                    returnValue( portStr )
        except Error as e:
            if e.code == 13: raise PortRegError( 0 )

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
    def _matchSerial( serNode, potMatch ):
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

    def serverConnected(self, ID, name):
        """Check to see if we can connect to serial server now"""
        if self.ser is None and None not in ( self.port, self.serNode ) and self._matchSerial( self.serNode, name ):
            self.initSerial( name, self.port)
            print('Serial server connected after we connected')

    def serverDisconnected(self, ID, name):
        """Close connection (if we are connected)"""
        if self.ser and self.ser.ID == ID:
            print('Serial server disconnected.  Relaunch the serial server')
            self.ser = None

    @setting(111111, 'Select Device', node='s', port='s', returns='')
    def selectDevice(self, c, node, port):
        """
        Attempt to connect to serial device on the given node and port.
        """
        #check that node is specified
        if not node: raise SerialDeviceError('Must define serNode attributes')
        self.serNode = node
        #set port if assigned, otherwise get from registry
        if port:
            self.port = port
        elif self.regKey:
            self.port = yield self.getPortFromReg(self.regKey)
        #try to open serial connection
        try:
            serStr = yield self.findSerial(self.serNode)
            self.initSerial(serStr, self.port, baudrate=self.baudrate, timeout=self.timeout,
                            bytesize=self.bytesize, parity=self.parity)
        except SerialConnectionError as e:
            self.ser = None
            if e.code == 0:
                print('Could not find serial server for node: %s' % self.serNode)
                print('Please start correct serial server')
            elif e.code == 1:
                print('Error opening serial connection')
                print('Check set up and restart serial server')
            else:
                raise Exception('Unknown connection error')

    @setting(111112, 'Close Device', returns='')
    def closeDevice(self, c):
        if self.ser:
            self.ser.close()
            self.ser = None
            print('Serial Connection closed')
        else:
            raise Exception('No device selected')

    @setting(111113, 'Query', data='s')
    def query(self, c, data):
        """Write any string and read the response"""
        yield self.ser.write(data + '\r\n')
        resp = yield self.ser.read()
        return resp

    def stopServer(self):
        """
        Close serial connection before exiting.
        """
        if self.ser:
            self.ser.close()
