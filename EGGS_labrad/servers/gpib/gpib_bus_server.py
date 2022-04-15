# CHANGELOG
#
# 2011 December 10 - Peter O'Malley & Jim Wenner
#
# Fixed bug where doesn't add devices if no SOCKETS connected.
#
# 2011 December 5 - Jim Wenner
#
# Added ability to read TCPIP (Ethernet) devices if configured to use
# sockets (i.e., fixed port address). To do this, added getSocketsList
# function and changed refresh_devices.
#
# 2011 December 3 - Jim Wenner
#
# Added ability to read TCPIP (Ethernet) devices. Must be configured
# using VXI-11 or LXI so that address ends in INSTR. Does not accept if
# configured to use sockets. To do this, changed refresh_devices.
#
# To be clear, the gpib system already supported ethernet devices just fine
# as long as they weren't using raw socket protocol. The changes that
# were made here and in the next few revisions are hacks to make socket
# connections work, and should be improved.
#
# 2021 October 17 - Clayton Ho
# Added back automatic device polling
# 2021 November 25 - Clayton Ho
# Added configurable device polling
# 2021 December 15 - Clayton Ho
# Subclassed it from PollingServer to support polling
# instead of using server methods


"""
### BEGIN NODE INFO
[info]
name = GPIB Bus
version = 1.5.2
description = Gives access to GPIB devices via pyvisa.
instancename = %LABRADNODE% GPIB Bus

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 100
### END NODE INFO
"""
import pyvisa as visa
from labrad.units import WithUnit
from labrad.server import setting
from labrad.errors import DeviceNotSelectedError
from EGGS_labrad.servers import PollingServer

KNOWN_DEVICE_TYPES = ('GPIB', 'TCPIP', 'USB')


class GPIBBusServer(PollingServer):
    """
    Provides direct access to GPIB-enabled devices.
    """

    name = '%LABRADNODE% GPIB Bus'
    defaultTimeout = WithUnit(1.0, 's')
    POLL_ON_STARTUP = True

    def initServer(self):
        super().initServer()
        self.devices = {}
        self.refreshDevices()

    def _poll(self):
        self.refreshDevices()

    def refreshDevices(self):
        """
        Refresh the list of known devices on this bus.
        Currently supported are GPIB devices and GPIB over USB.
        """
        try:
            rm = visa.ResourceManager()
            addresses = [str(x) for x in rm.list_resources()]
            additions = set(addresses) - set(self.devices.keys())
            deletions = set(self.devices.keys()) - set(addresses)
            for addr in additions:
                try:
                    if not addr.startswith(KNOWN_DEVICE_TYPES):
                        continue
                    instr = rm.open_resource(addr)
                    instr.write_termination = ''
                    instr.clear()
                    if addr.endswith('SOCKET'):
                        instr.write_termination = '\n'
                    self.devices[addr] = instr
                    self.sendDeviceMessage('GPIB Device Connect', addr)
                except Exception as e:
                    print('Failed to add ' + addr + ':' + str(e))
                    raise
            for addr in deletions:
                del self.devices[addr]
                self.sendDeviceMessage('GPIB Device Disconnect', addr)
        except Exception as e:
            print('Problem while refreshing devices:', str(e))
            raise e

    def sendDeviceMessage(self, msg, addr):
        print(msg + ': ' + addr)
        self.client.manager.send_named_message(msg, (self.name, addr))

    def initContext(self, c):
        c['timeout'] = self.defaultTimeout

    def getDevice(self, c):
        if 'addr' not in c:
            raise DeviceNotSelectedError("No GPIB address selected.")
        if c['addr'] not in self.devices:
            raise Exception('Could not find device ' + c['addr'])
        instr = self.devices[c['addr']]
        return instr

    @setting(0, addr='s', returns='s')
    def address(self, c, addr=None):
        """
        Get or set the GPIB address for this context.

        To get the addresses of available devices,
        use the list_devices function.
        """
        if addr is not None:
            c['addr'] = addr
        return c['addr']

    @setting(2, time='v[s]', returns='v[s]')
    def timeout(self, c, time=None):
        """
        Get or set the GPIB timeout.
        """
        if time is not None:
            c['timeout'] = time
        return c['timeout']

    @setting(3, data='s', returns='')
    def write(self, c, data):
        """
        Write a string to the GPIB bus.
        """
        self.getDevice(c).write(data)

    @setting(8, data='y', returns='')
    def write_raw(self, c, data):
        """
        Write a string to the GPIB bus.
        """
        self.getDevice(c).write_raw(data)

    @setting(4, n_bytes='w', returns='s')
    def read(self, c, n_bytes=None):
        """
        Read from the GPIB bus.

        Termination characters, if any, will be stripped.
        This includes any bytes corresponding to termination in
        binary data. If specified, reads only the given number
        of bytes. Otherwise, reads until the device stops sending.
        """
        instr = self.getDevice(c)
        if n_bytes is None:
            ans = instr.read_raw()
        else:
            ans = instr.read_raw(n_bytes)
        ans = ans.strip().decode()
        return ans

    @setting(5, data='s', returns='s')
    def query(self, c, data):
        """
        Make a GPIB query, a write followed by a read.

        This query is atomic.  No other communication to the
        device will occur while the query is in progress.
        """
        instr = self.getDevice(c)
        instr.write(data)
        ans = instr.read_raw()
        # convert from bytes to string for python 3
        ans = ans.strip().decode()
        return ans

    @setting(7, n_bytes='w', returns='y')
    def read_raw(self, c, n_bytes=None):
        """
        Read raw bytes from the GPIB bus.

        Termination characters, if any, will not be stripped.
        If n_bytes is specified, reads only that many bytes.
        Otherwise, reads until the device stops sending.
        """
        instr = self.getDevice(c)
        if n_bytes is None:
            ans = instr.read_raw()
        else:
            ans = instr.read_raw(n_bytes)
        return bytes(ans)

    @setting(20, returns='*s')
    def list_devices(self, c):
        """
        Get a list of devices on this bus.
        """
        return sorted(self.devices.keys())

    @setting(21)
    def refresh_devices(self, c):
        """
        Manually refresh devices.
        """
        self.refreshDevices()

    def _poll_fail(self, failure):
        print('Polling failed.')


__server__ = GPIBBusServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
