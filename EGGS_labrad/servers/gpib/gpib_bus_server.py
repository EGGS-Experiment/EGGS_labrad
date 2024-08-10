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
#
# 2021 November 25 - Clayton Ho
# Added configurable device polling
#
# 2021 December 15 - Clayton Ho
# Subclassed it from PollingServer to support polling
# instead of using server methods
#
# 2022 November 6 - Clayton Ho
# Copied over some changes made by Landon in UCLALabrad repository:
#   - _refreshDevices now closes devices before deleting them from the holding dictionary
#   - timeout function now actually sets the timeout with the GPIB device instead of just storing it within the context
#
# 2022 November 20 - Clayton Ho
# Removed stupid use of read_raw/write in read() and query().
# Removed TCPIP as a recognized device type since all bus servers will recognize the network device, leading to duplicates.
# Implemented stopServer, which closes any and all open devices (yes, this isn't tremendously necessary, but whatever).
#
# 2022 December 28 - Clayton Ho (updated to 1.5.4)
# Fixed error handling in _refreshDevices; bus server now works nearly perfectly.
#

"""
### BEGIN NODE INFO
[info]
name = GPIB Bus
version = 1.5.4
description = Gives access to GPIB devices via pyvisa.
instancename = %LABRADNODE% GPIB Bus

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 10
### END NODE INFO
"""
import pyvisa as visa
from labrad.units import WithUnit
from labrad.server import setting
from labrad.errors import DeviceNotSelectedError
from EGGS_labrad.servers import PollingServer

KNOWN_DEVICE_TYPES = ('GPIB', 'USB')

# todo: move changelog somewhere else
# todo: write function & setting documentation


class GPIBBusServer(PollingServer):
    """
    Provides direct access to GPIB-enabled devices.
    """

    name = '%LABRADNODE% GPIB Bus'
    defaultTimeout = WithUnit(10.0, 's')
    POLL_ON_STARTUP = True


    # GENERAL
    def initServer(self):
        super().initServer()
        self.devices = {}
        # tmp remove
        #self.rm = visa.ResourceManager()
        # tmp remove close
        self._refreshDevices()

    def stopServer(self):
        """
        Close all open devices.
        """
        for dev in self.devices.values():
            try:
                dev.close()
            except Exception as e:
                print("Error on closing: {}".format(e))

    def initContext(self, c):
        # todo: do I have to call parent's initContext to add c to listeners?
        c['timeout'] = self.defaultTimeout

    def _poll(self):
        self._refreshDevices()

    def _poll_fail(self, failure):
        print('Polling failed.')


    # DEVICES & MESSAGES
    def getDevice(self, c):
        """
        Returns the GPIB device stored within the given context, if any.
        """
        if 'addr' not in c:
            raise DeviceNotSelectedError("No GPIB address selected.")
        if c['addr'] not in self.devices:
            raise Exception('Could not find device ' + c['addr'])
        instr = self.devices[c['addr']]
        return instr

    def _refreshDevices(self):
        """
        Refresh the list of known devices on this bus.
        Currently supported are GPIB devices and GPIB over USB.
        """
        try:
            rm = visa.ResourceManager()

            # get only desired device names
            addresses = set([
                str(addr)
                for addr in rm.list_resources()
                if addr.startswith(KNOWN_DEVICE_TYPES)
            ])

            # get additions and deletions
            additions = addresses - set(self.devices.keys())
            deletions = set(self.devices.keys()) - addresses

            # process newly connected devices
            for addr in additions:
                try:
                    instr = rm.open_resource(addr)

                    # set up device communication
                    instr.timeout = self.defaultTimeout['ms']
                    instr.query_delay = 0.01
                    # todo: why do we set termination like this? maybe b/c we want to figure out termination ourselves?
                    instr.write_termination = ''
                    if addr.endswith('SOCKET'):
                        instr.write_termination = '\n'
                    instr.clear()

                    # recognize device and let listeners know
                    self.devices[addr] = instr
                    self.sendDeviceMessage('GPIB Device Connect', addr)

                except Exception as e:
                    print('Failed to add {}'.format(addr))
                    print('\tError: {}'.format(e))

                    # ensure problematic device is removed from self.devices
                    if addr in self.devices:
                        del self.devices[addr]

            # process disconnected devices
            for addr in deletions:
                self.devices[addr].close()
                del self.devices[addr]
                self.sendDeviceMessage('GPIB Device Disconnect', addr)

        except Exception as e:
            print('Problem while refreshing devices: {}'.format(e))
            raise e

    def sendDeviceMessage(self, msg, addr):
        """
        Sends a message to the console regarding device activity
        Args:
            msg     (str):  Message to send.
            addr    (idk):  the device address.
        """
        # todo: document this lmao
        print('{}: {}'.format(msg, addr))
        self.client.manager.send_named_message(msg, (self.name, addr))


    # SETTINGS
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
            self.getDevice(c).timeout = time['ms']
        return WithUnit(self.getDevice(c).timeout / 1000.0, 's')

    @setting(3, data='s', returns='')
    def write(self, c, data):
        """
        Write a string to the GPIB bus.
        """
        self.getDevice(c).write(data)

    @setting(8, data='y', returns='')
    def write_raw(self, c, data):
        """
        Write a raw string to the GPIB bus.
        """
        self.getDevice(c).write_raw(data)

    @setting(4, returns='s')
    def read(self, c):
        """
        Read from the GPIB bus.

        Termination characters, if any, will be stripped.
        This includes any bytes corresponding to termination in
        binary data.
        """
        ans = self.getDevice(c).read()
        return ans.strip()

    @setting(6, n_bytes='w', returns='y')
    def read_raw(self, c, n_bytes=None):
        """
        Read raw bytes from the GPIB bus.

        Termination characters, if any, will not be stripped.
        If n_bytes is specified, reads only that many bytes.
        Otherwise, reads until the device stops sending.
        """
        ans = None
        instr = self.getDevice(c)
        if n_bytes is None:
            ans = instr.read_raw()
        else:
            ans = instr.read_raw(n_bytes)
        return bytes(ans)

    @setting(7, data='s', returns='s')
    def query(self, c, data):
        """
        Make a GPIB query (a write followed by a read).

        This query is atomic. No other communication to the
        device will occur while the query is in progress.
        """
        ans = self.getDevice(c).query(data)
        return ans.strip()

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
        self._refreshDevices()


__server__ = GPIBBusServer()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
