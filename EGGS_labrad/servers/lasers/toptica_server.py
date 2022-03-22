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
from twisted.internet.defer import returnValue, inlineCallbacks

from toptica.lasersdk.client import Client, NetworkConnection


class TopticaServer(LabradServer):
    """
    Talks to Toptica devices.
    """

    name = 'Toptica Server'


    # DEVICE CONNECTION
    @setting(111111, 'Device Select', node='s', port='s', returns=['', '(ss)'])
    def deviceSelect(self, c, node=None, port=None):
        """
        Attempt to connect to serial device on the given node and port.
        Arguments:
            node    (str)   : the node to connect on
            port    (str)   : the port to connect to
        Returns:
                    (str,str): the connected node and port (empty if no connection)
        """
        # do nothing if device is already selected
        if self.ser:
            Exception('A serial device is already opened.')
        # set parameters if specified
        elif (node is not None) and (port is not None):
            self.serNode = node
            self.port = port
        # connect to default values if no arguments at all
        elif ((node is None) and (port is None)) and (self.serNode and self.port):
            pass
        # raise error if only node or port is specified
        else:
            raise Exception('Insufficient arguments.')

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
                print('Unknown connection error')
            raise e
        except Exception as e:
            self.ser = None
            print(e)
        else:
            return (self.serNode, self.port)

    @setting(111112, 'Device Close', returns='')
    def deviceClose(self, c):
        """
        Closes the current serial device.
        """
        if self.ser:
            self.ser.close()
            self.ser = None
            print('Serial connection closed.')
        else:
            raise Exception('No device selected.')

    @setting(111113, 'Device Info', returns='(ss)')
    def deviceInfo(self, c):
        """
        Returns the currently connected serial device's
        node and port.
        Returns:
            (str)   : the node
            (str)   : the port
        """
        if self.ser:
            return (self.serNode, self.port)
        else:
            raise Exception('No device selected.')


    # DIRECT SERIAL COMMUNICATION
    @setting(222224, 'Serial Write', data='s', returns='')
    def serial_write(self, c, data):
        """
        Directly write to the serial device.
        Args:
            data    (str)   : the data to write to the device
        """
        yield self.ser.acquire()
        yield self.ser.write(data)
        self.ser.release()

    @setting(222225, 'Serial Read', stop=['i: read a given number of characters',
                                          's: read until the given character'], returns='s')
    def serial_read(self, c, stop=None):
        """
        Directly read the serial buffer.
        Returns:
                    (str)   : the device response (stripped of EOL characters)
        """
        yield self.ser.acquire()
        if stop is None:
            resp = yield self.ser.read()
        elif type(stop) == int:
            resp = yield self.ser.read(stop)
        elif type(stop) == str:
            resp = yield self.ser.read_line(stop)
        self.ser.release()
        returnValue(resp)


if __name__ == '__main__':
    from labrad import util
    util.runServer(TopticaServer())
