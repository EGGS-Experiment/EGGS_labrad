# Changelog
# 1.3: Created serverConnected() to identify devices on a given server once
#     it has completed its registration with the LabRAD manager. Before this
#     device registration would fail if the server had a custom IDN handling
#     function because this setting could not be properly accessed through the
#     LabRAD manager at the time of execution.
# 1.4.0: Updated for Python 3
# 1.4.1: Case is ignored when matching device names
# 1.4.2:
#   Changed parseIDNResponse function to account for problems where string has more than 4 parts
#   Removed *CLS call in lookupDeviceName
# 1.4.3:
#   Added support for pattern matching to allow wrappers to cover a broader range of devices.
#
"""
### BEGIN NODE INFO
[info]
name = GPIB Device Manager
version = 1.4.3
description = Manages discovery and lookup of GPIB devices

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 5
### END NODE INFO
"""
import re
from twisted.internet.reactor import callLater
from twisted.internet.defer import DeferredList, DeferredLock

from labrad.units import Value
from labrad.server import LabradServer, setting, inlineCallbacks, returnValue

UNKNOWN = '<unknown>'
# todo: finish implementing regex
# todo: finish documenting functions and cleaning up
# todo: write arg/return docstrings


def parseIDNResponse(idn_str):
    """
    Parse the response from *IDN? to get mfr and model info.
    Arguments:
        idn_str (str):  the *IDN? response.
    Returns:
                (str):  the manufacturer and model info.
    """
    mfr, model, ver, rev = idn_str.split(',', 3)
    # convert response to uppercase
    return mfr.strip().upper() + ' ' + model.strip().upper()


class GPIBDeviceManager(LabradServer):
    """
    Manages autodetection and identification of GPIB devices.

    The device manager listens for "GPIB Device Connect" and
    "GPIB Device Disconnect" messages coming from GPIB bus servers.
    It attempts to identify the connected devices and forward the
    messages on to servers interested in particular devices.  For
    devices that cannot be identified by *IDN? in the usual way,
    servers can register an identification setting to be called
    by the device manager to properly identify the device.
    """
    name = 'GPIB Device Manager'
    
    @inlineCallbacks
    def initServer(self):
        """
        Initialize the server after connecting to the LabRAD manager.
        """
        self.knownDevices =     {}      # maps (server, channel) to (name, idn)
        self.deviceServers =    {}      # maps device name to list of interested servers.
                                        # each interested server is {'target':<>,'context':<>,'messageID':<>}
        self.identFunctions =   {}      # maps server to (setting, ctx) for ident
        self.identLock = DeferredLock()
        
        # named messages are sent with source ID first, which we ignore
        # python 3 no longer supports tuple unpacking, so we have to unpack it manually
        connect_func = lambda c, msg: self.gpib_device_connect(*msg[1])
        disconnect_func = lambda c, msg: self.gpib_device_disconnect(*msg[1])
        mgr = self.client.manager
        self._cxn.addListener(connect_func, source=mgr.ID, ID=10)
        self._cxn.addListener(disconnect_func, source=mgr.ID, ID=11)
        yield mgr.subscribe_to_named_message('GPIB Device Connect', 10, True)
        yield mgr.subscribe_to_named_message('GPIB Device Disconnect', 11, True)

        # do an initial scan of the available GPIB devices
        yield self.refreshDeviceLists()


    '''
    DEVICE DETECTION & IDENTIFICATION
    '''
    @inlineCallbacks
    def refreshDeviceLists(self):
        """
        Ask all GPIB bus servers for their available GPIB devices.
        """
        servers = [
            s for n, s in self.client.servers.items()
            if (('GPIB Bus' in n) or ('gpib_bus' in n)) and
               (('List Devices' in s.settings) or ('list_devices' in s.settings))
        ]
        serverNames = [s.name for s in servers]
        print('Pinging servers: {}'.format(serverNames))
        resp = yield DeferredList([s.list_devices() for s in servers])
        for serverName, (success, addrs) in zip(serverNames, resp):
            if not success:
                print('Failed to get device list for: {}'.format(serverName))
            else:
                print('{} has devices: {}'.format(serverName, addrs))
                for addr in addrs:
                    self.gpib_device_connect(serverName, addr)

    @inlineCallbacks
    def lookupDeviceName(self, server, channel):
        """
        Try to send a *IDN? query to lookup info about a device.

        Returns the name of the device and the actual response string
        to the identification query.  If the response cannot be parsed
        or the query fails, the name will be listed as '<unknown>'.
        """
        p = self.client.servers[server].packet()
        p.address(channel).timeout(Value(1, 's')).query('*IDN?')
        print('Sending *IDN? to: {}'.format((server, channel)))
        resp = None
        try:
            resp = (yield p.send()).query
            name = parseIDNResponse(resp)
        except Exception as e:
            print('Error sending *IDN? to: {}'.format((server, channel)))
            print(e)
            name = UNKNOWN
        returnValue((name, resp))

    def identifyDevice(self, server, channel, idn):
        """
        Try to identify a new device with all ident functions.

        Returns the first name returned by a successful identification.
        """
        @inlineCallbacks
        def _doIdentifyDevice():
            for identifier in list(self.identFunctions.keys()):
                name = yield self.tryIdentFunc(server, channel, idn, identifier)
                if name is not None:
                    returnValue(name)
            returnValue(UNKNOWN)
        return self.identLock.run(_doIdentifyDevice)

    def identifyDevicesWithServer(self, identifier):
        """
        Try to identify all unknown devices with a new server.
        """
        @inlineCallbacks
        def _doServerIdentify():
            #yield self.client.refresh()
            for (server, channel), (device, idn) in list(self.knownDevices.items()):
                if device != UNKNOWN:
                    continue
                name = yield self.tryIdentFunc(server, channel, idn, identifier)
                if name is None:
                    continue
                self.knownDevices[server, channel] = (name, idn)
                if name in self.deviceServers:
                    self.notifyServers(name, server, channel, True)
        return self.identLock.run(_doServerIdentify)        

    @inlineCallbacks
    def tryIdentFunc(self, server, channel, idn, identifier):
        """
        Try calling one registered identification function.

        If the identification succeeds, returns the new name,
        otherwise returns None.
        """
        try:
            # todo: is this client refresh necessary?
            yield self.client.refresh()
            s = self.client[identifier]
            setting, context = self.identFunctions[identifier]

            print('Trying to identify device: {}'.format((server, channel)))
            print('on server', identifier,)
            print('with *IDN?:', repr(idn))

            if idn is None:
                resp = yield s[setting](server, channel, context=context)
            else:
                resp = yield s[setting](server, channel, idn, context=context)

            if resp is not None:
                print('Server {} identified device {} {} as "{}"'.format(identifier, server, channel, resp))
                returnValue(resp)

        except Exception as e:
            print('Error during ident: {}'.format(e))


    '''
    SIGNAL FUNCTIONS
    '''
    @inlineCallbacks
    def gpib_device_connect(self, gpibBusServer, channel):
        """
        Handle messages when devices connect.
        """
        print('Device Connect: {}'.format((gpibBusServer, channel)))
        if (gpibBusServer, channel) in self.knownDevices:
            return

        # attempt to identify device by querying *IDN?
        yield self.client.refresh()
        device, idnResult = yield self.lookupDeviceName(gpibBusServer, channel)
        # if that fails, try other ident functions
        if device == UNKNOWN:
            device = yield self.identifyDevice(gpibBusServer, channel, idnResult)

        # forward message if someone cares about this device
        self.knownDevices[gpibBusServer, channel] = (device, idnResult)
        if device in self.deviceServers:
            self.notifyServers(device, gpibBusServer, channel, True)

    def gpib_device_disconnect(self, server, channel):
        """
        Handle messages when devices disconnect.
        """
        print('Device Disconnect: {}'.format((server, channel)))
        if (server, channel) not in self.knownDevices:
            return

        # todo: document
        device, idnResult = self.knownDevices[server, channel]
        del self.knownDevices[server, channel]

        # forward message if someone cares about this device
        if device in self.deviceServers:
            self.notifyServers(device, server, channel, False)

    def notifyServers(self, device, server, channel, isConnected):
        """
        Notify all registered servers about a device status change.
        """
        for s in self.deviceServers[device]:
            rec = s['messageID'], (device, server, channel, isConnected)
            print('Sending message to GPIBManagedServers: {} {} {}'.format(s['target'], s['context'], [rec]))
            self.client._sendMessage(s['target'], [rec], context=s['context'])

    def serverConnected(self, ID, name):
        """
        New GPIBManagedServers will register directly with us, before they
        have even completed their registration with the LabRAD manager as a server.
        We will get this signal once they are accessible through the LabRAD client
        so that we can probe them for devices. This ordering matters mainly if
        the new server has a custom IDN parsing function.
        """
        recognizeServer = False
        for device, serverInfo in list(self.deviceServers.items()):
            if serverInfo[0]['target'] == ID:
                recognizeServer = True
        if recognizeServer:
            callLater(0, self.identifyDevicesWithServer, ID)
        
    def serverDisconnected(self, ID, name):
        """
        Disconnect devices when a bus server disconnects.
        """
        for (server, channel) in list(self.knownDevices.keys()):
            if server == name:
                self.gpib_device_disconnect(server, channel)
    
    def expireContext(self, c):
        """
        Stop sending notifications when a context expires.
        """
        print('Expiring context: {}'.format(c.ID))
        # device servers
        deletions = []
        for device, servers in list(self.deviceServers.items()):
            # remove all registrations with this context
            servers = [s for s in servers if s['context'] != c.ID]
            self.deviceServers[device] = servers
            # if no one is left listening to this device, delete the list
            if not len(servers):
                deletions.append(device)
        for device in deletions:
            del self.deviceServers[device]

        # ident functions
        deletions = []
        for src, idents in list(self.identFunctions.items()):
            # remove all registrations with this context
            idents = [i for i in idents if i[1] != c.ID]
            self.identFunctions[src] = idents
            # if no one is left listening to this device, delete the list
            if not len(idents):
                deletions.append(src)
        for src in deletions:
            del self.identFunctions[src]


    '''
    SETTINGS
    '''
    @setting(1, 'Register Server',
             devices=['s', '*s'], messageID='w',
             returns='*(s{device} s{server} s{address}, b{isConnected})')
    def register_server(self, c, devices, messageID):
        """
        Register as a server that handles a particular GPIB device(s).

        Returns a list with information about all matching devices that
        have been connected up to this point:
        [(device name, gpib server name, gpib channel, bool)]

        After registering, messages will be sent to the registered
        message ID whenever a matching device connects or disconnects.
        The clusters sent in response to this setting and those sent as
        messages have the same format.  For messages, the final boolean
        indicates whether the device has been connected or disconnected,
        while in response to this function call, the final boolean is
        always true, since we only send info about connected devices.

        The device name is determined by parsing the response to a *IDN?
        query.  To handle devices that don't support *IDN? correctly, use
        the 'Register Ident Function' in addition.
        """
        # managed device servers can specify device names as string or a list of strings
        if isinstance(devices, str):
            devices = [devices]
        found = []
        # search through
        for device in devices:
            # convert to uppercase
            device = device.upper()
            # store GPIB managed device server details
            servers = self.deviceServers.setdefault(device, [])
            servers.append({'target': c.source,
                            'context': c.ID,
                            'messageID': messageID})
            # check the new device against all known devices
            for (server, channel), (known_device, idnResult) in self.knownDevices.items():
                if device != known_device:
                    continue
                found.append((device, server, channel, True))
        return found

    @setting(2, 'Register Ident Function', setting=['s', 'w'])
    def register_ident_function(self, c, setting):
        """Specify a setting to be called to identify devices.

        This setting must accept either of the following:

            s, s, s: server, address, *IDN? response
            s, s:    server, address

        If a device returned a non-standard response to a *IDN? query
        (including possibly an empty string), then the first call signature
        will be used.  If the *IDN? query timed out or otherwise failed,
        the second call signature will be used.  As a server writer, you
        must choose which of these signatures to support.  Note that if the
        device behavior is unpredictable (sometimes it returns a string,
        sometimes it times out), you may need to support both signatures.
        """
        self.identFunctions[c.source] = setting, c.ID

    @setting(10, 'Dump Info')
    def dump_info(self, c):
        """
        Returns information about the server status.

        This info includes currently known devices, registered device
        servers, and registered identification functions.

        Returns:
            tuple(str, str, str):   a tuple composed of all known devices, device servers, and ident functions.
                                    Each str is a dict object simply converted into a string.
        """
        return (str(self.knownDevices),
                str(self.deviceServers),
                str(self.identFunctions))


__server__ = GPIBDeviceManager()

if __name__ == '__main__':
    from labrad import util
    util.runServer(__server__)
