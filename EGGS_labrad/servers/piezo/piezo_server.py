"""
### BEGIN NODE INFO
[info]
name = piezo_controller
version = 1.0
description =
instancename = piezo_controller

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
from labrad.types import Value
from twisted.internet.defer import inlineCallbacks, returnValue

TIMEOUT = Value(1, 's')


class piezo_wrapper(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a UCLA piezo controller."""
        print('connecting to "%s" on port "%s"...' % (server.name, port), )
        self.server = server
        self.ctx = server.context()
        self.port = port
        p = self.packet()
        p.open(port)
        p.baudrate(38400)
        p.read()  # clear out the read buffer
        p.timeout(TIMEOUT)
        yield p.send()

    def packet(self):
        """Create a packet in our private context."""
        return self.server.packet(context=self.ctx)

    def shutdown(self):
        """Disconnect from the serial port when we shut down."""
        return self.packet().close().send()

    @inlineCallbacks
    def write(self, code):
        """Write a data value to the heat switch."""
        yield self.packet().write(code).send()

    @inlineCallbacks
    def query(self, code):
        """ Write, then read. """
        p = self.packet()
        p.write_line(code)
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)


class piezo_server(DeviceServer):
    name = 'piezo_controller'
    deviceWrapper = piezo_wrapper

    @inlineCallbacks
    def initServer(self):
        self.current_state = {}
        print('loading config info...', )
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield DeviceServer.initServer(self)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'piezo_controller', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)
        # Get output state and last value of current set
        yield reg.cd(['', 'Servers', 'piezo_controller', 'parameters'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.params = dict((k, ans[k]) for k in keys)
        for key in self.params:
            self.current_state[key] = list(self.params[key])

    @inlineCallbacks
    def findDevices(self):
        """Find available devices from list stored in the registry."""
        devs = []
        for name, (serServer, port) in self.serialLinks.items():
            if serServer not in self.client.servers:
                continue
            server = self.client[serServer]
            ports = yield server.list_serial_ports()
            if port not in ports:
                continue
            devName = '%s - %s' % (serServer, port)
            devs += [(devName, (server, port))]
        returnValue(devs)

    @setting(100, channel='i', value='v[V]')
    def set_voltage(self, c, channel, value):
        '''
        Sets the value of the voltage.
        '''
        self.voltage = value
        dev = self.selectDevice(c)
        yield dev.write('vout.w ' + str(channel) + ' ' + str((value['V'])) + '\r\n')
        self.current_state[str(channel)][0] = value['V']
        # self.update_registry(channel)

    @setting(101, channel='i', value='b')
    def set_output_state(self, c, channel, value):
        '''
        Turn a channel on or off
        '''
        self.output = value
        dev = self.selectDevice(c)
        yield dev.write('out.w ' + str(channel) + ' ' + str(int(value)) + '\r\n')
        self.current_state[str(channel)][1] = int(value)

    @setting(102, value='b')
    def set_remote_state(self, c, value):
        '''
        Turn the remote mode on
        '''

        dev = self.selectDevice(c)
        yield dev.write('remote.w ' + str(int(value)) + '\r\n')

    @setting(200, channel='i', returns='b')
    def get_output_state(self, c, channel, value):
        '''
        Get the output state of the specified channel. State is unknown when
        server is first started or restarted.
        '''

        return self.current_state[str(channel)][1]

    @setting(201, channel='i', returns='v')
    def get_voltage(self, c, channel):
        return self.current_state[str(channel)][0]


if __name__ == "__main__":
    from labrad import util

    util.runServer(piezo_server())
