"""
### BEGIN NODE INFO
[info]
name = UCLA_piezo
version = 1.0
description =
instancename = UCLA_piezo

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.devices import DeviceServer, DeviceWrapper
from labrad.server import setting
from labrad.types import Value
from twisted.internet.defer import inlineCallbacks, returnValue

TIMEOUT = Value(1.0, 's')


class UCLAPiezo_device(DeviceWrapper):

    @inlineCallbacks
    def connect(self, server, port):
        """Connect to a piezo device."""
        print
        'connecting to "%s" on port "%s"...' % (server.name, port),
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
        """Write a data value"""
        p = self.packet()
        p.write_line(code)
        yield p.send()

    @inlineCallbacks
    def read(self):
        """Read a line of data"""
        p = self.packet()
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)

    @inlineCallbacks
    def query(self, code):
        """ Write, then read. """
        p = self.packet()
        p.write_line(code)
        p.read_line()
        ans = yield p.send()
        returnValue(ans.read_line)


class UCLAPiezo(DeviceServer):
    name = 'UCLAPiezo'
    deviceName = 'UCLAPiezo'
    deviceWrapper = UCLAPiezo_device

    """
    UCLA piezo controller box (4 channel controller designed by Peter Yu and Christian Schneider)
    registry should contain a folder called 'settings' with 4 channel key value pairs ex.
    ucla_piezo_chan_4 (1.4V, false, 'name')
    
    """

    @inlineCallbacks
    def initServer(self):
        print
        'loading config info...',
        self.reg = self.client.registry()
        yield self.loadConfigInfo()
        yield self.reg.cd(['', 'settings'], True)
        yield DeviceServer.initServer(self)

    @inlineCallbacks
    def loadConfigInfo(self):
        """Load configuration information from the registry."""
        reg = self.reg
        yield reg.cd(['', 'Servers', 'UCLAPiezo', 'Links'], True)
        dirs, keys = yield reg.dir()
        p = reg.packet()
        for k in keys:
            p.get(k, key=k)
        ans = yield p.send()
        self.serialLinks = dict((k, ans[k]) for k in keys)

    @setting(100, 'get_device_info')
    def get_device_info(self, c):
        dev = self.selectDevice(c)
        output = 'id?'
        yield dev.write(output)
        device_type = yield dev.read()
        device_id = yield dev.read()
        hardware_id = yield dev.read()
        firmware = yield dev.read()
        returnValue([device_type, device_id, hardware_id, firmware])

    @setting(101, 'set_voltage', chan='i', voltage='v[V]')
    def set_voltage(self, c, chan, voltage):
        dev = self.selectDevice(c)
        output = 'vout.w ' + str(chan) + ' ' + str(voltage['V'])
        yield dev.write(output)
        setting = yield self.reg.get('ucla_piezo_chan_' + str(chan))
        state = setting[1]
        name = setting[2]
        yield self.reg.set('ucla_piezo_chan_' + str(chan), (voltage, state, name))

    @setting(102, 'piezo_output', chan='i', state='b')
    def piezo_output(self, c, chan, state):
        dev = self.selectDevice(c)
        if state:
            output = 'out.w ' + str(chan) + ' 1'
        else:
            output = 'out.w ' + str(chan) + ' 0'
        yield dev.write(output)
        setting = yield self.reg.get('ucla_piezo_chan_' + str(chan))
        voltage = setting[0]
        name = setting[2]
        yield self.reg.set('ucla_piezo_chan_' + str(chan), (voltage, state, name))


if __name__ == "__main__":
    from labrad import util
    util.runServer(UCLAPiezo())
