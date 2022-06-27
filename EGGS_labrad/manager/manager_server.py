# !/usr/bin/python

import sys
import os

if __name__ == "__main__":
    if os.name == "posix":
        sys.path.insert(0, os.path.join(os.environ['HOME'], 'src/pylabrad-0.93.1/'))
    elif os.name == "nt":
        base_path = "U://"

import labrad
from labrad.server import LabradServer, setting, ServerProtocol
import datetime
from twisted.python import log
import collections
import delphi_compat


class NamedMessage(object):
    def __init__(self, name):
        self.name = name
        self.listeners = set()

    def enable(self, source, ctx, ID):
        self.listeners.add((source, ctx, ID))

    def disable(self, source, ctx, ID):
        self.listeners.discard((source, ctx, ID))

    def disable_all(self, source):
        for k in list(self.listeners):
            if k[0] == source:
                self.listeners.discard(k)


class Setting(object):
    def __init__(self, ID, name, desc, input_types, output_types, remarks):
        self.ID = ID
        self.name = name
        self.desc = desc
        self.input_types = input_types
        self.output_types = output_types
        self.remarks = remarks


class ClientConnection(object):
    def __init__(self, ID, name):
        self.ID = ID
        self.name = name
        self.contexts = set()
        self.sent_pkts = 0
        self.recv_pkts = 0


class ServerConnection(ClientConnection):
    def __init__(self, ID, name, desc, remarks):
        super(ServerConnection, self).__init__(ID, name)
        self.desc = desc
        self.remarks = remarks
        self.settings = {}
        self.visible = False
        self.notifyID = None
        self.notifyAll = False


class DummyTransport(object):
    def getPeer(self):
        peer = collections.namedtuple('peer', ['host', 'port'])
        return peer('0.0.0.0', 0)


class InMemoryProtocol(ServerProtocol):
    def __init__(self, manager, ID):
        ServerProtocol.__init__(self)
        self.manager = manager
        self.ID = ID
        self.transport = DummyTransport()

    def handlePacket(self, ID, dest, context, request, records):
        ServerProtocol.handlePacket(self, ID, dest, context, request, records)

    def sendPacket(self, dest, context, request, records):
        # print "dest: %s, ctx: %s, req: %s, rec: %s" % (dest, context, request, records)
        self.manager.handlePacket(self.ID, dest, context, request, records)


class InMemoryServer(LabradServer):
    protocol = InMemoryProtocol


class ManagerServer(InMemoryServer):
    name = 'Manager'

    def __init__(self, name, uuid):
        LabradServer.__init__(self)
        self.name = name
        self.uuid = uuid
        self.server_list = {1: ServerConnection(1, 'Manager',
                                                'The LabRAD Manager handles the interactions between parts of the LabRAD system.',
                                                '')}
        self.client_list = {}
        self.next_ID = 2
        self.serverID_cache = {}  # name -> ID
        self.context_cache = {}
        self.server_list[1].visible = True
        self.named_messages = {}

        for s in self._findSettingHandlers():
            self._checkSettingConflicts(s)
            self.settings[s.ID] = s
            info = s.getRegistrationInfo()
            self.s__register_setting(None, *info)

    def initServer(self):
        print
        "Manager server initializing"
        pass

    def _connectionMade(self, protocol):
        self._cxn = protocol

    @setting(1, "Servers", returns="*(w,s)")
    def servers(self, c):
        '''
        Returns a list of available servers containing their name and ID
        '''
        return [(k, v.name) for k, v in self.server_list.items() if v.visible]

    @setting(2, 'Settings', server_name=['s: Retrieve settings for server with this name',
                                         'w: Retrieve settings for server with this ID'], returns='*(w, s)')
    def lr_settings(self, c, server_name=1):
        '''
        Returns list of available settings for a server containing their name and ID
        '''
        ID = self.server_to_ID(server_name)
        setting_list = self.server_list[ID].settings
        return [(k, v.name) for k, v in setting_list.items()]

    @setting(3, 'Lookup', serverID=['s', 'w'],
             settingID=['s', '*s'], returns=['w', '(ww)', '(w, *w)'])
    def lookup(self, c, serverID, settingID=0):
        '''
        Looks up a collection of server settings and retrieves their IDs
        '''

        serverID = self.server_to_ID(serverID)
        settings = self.server_list[serverID]
        if settingID == 0:
            return serverID
        if isinstance(settingID, str):
            return (serverID, self.setting_to_ID(serverID, settingID))
        else:
            return (serverID, [self.setting_to_ID(serverID, s) for s in settingID])

    @setting(10, 'Help', server_name=['s', 'w'], setting_name=['s', 'w'], returns=['ss', '(s, *s, *s, s)'])
    def help(self, c, server_name=None, setting_name=None):
        'Returns the help information for a server or setting'
        server_name = server_name or 1
        server_ID = self.server_to_ID(server_name)
        server = self.server_list[server_ID]
        if setting_name is None:
            return (server.desc, server.remarks)
        else:
            setting_ID = self.setting_to_ID(server_ID, setting_name)
            setting = server.settings[setting_ID]
            return (setting.desc, setting.input_types, setting.output_types, setting.remarks)

    @setting(11, 'Host ID', returns='(ss)')
    def host_id(self, c):
        '''
        Returns the manager host ID which can be used to uniquely identify a manager instance
        '''
        return (self.name, self.uuid)

    @setting(12, 'XKCD Random', returns='i')
    def xkcd_rand(self, c):
        '''
        http://xkcd.com/221/
        '''
        return 4

    @setting(30, 'Notify On Connect', settingID='w: setting to send notifications')
    def notify_on_connect(self, c, settingID=None):
        '''
        (DEPRECATED) Requests notifications if a server connects
        '''
        print
        "Calling depricated notify on connect for server ID %s", c.ID
        self.subscribe_to_named_message(c, 'Server Connect', setting, bool(setting))

    @setting(31, 'Notify On Disconnect', settingID='w: setting to send notifications')
    def notify_on_disconnect(self, c, settingID):
        '''
        (DEPRECATED) Requests notifications if a server disconnects
        '''
        print
        "Calling depricated notify on disconnect for server ID %s", c.ID
        self.subscribe_to_named_message(c, 'Server Disconnect', setting, bool(setting))

    @setting(50, 'Expire Context',
             serverID=['w: Expire context on this server only', ': Expire context on all servers'],
             returns='w: Number of notified servers')
    def expire_context(self, c, serverID=None):
        '''
        Sends a context expiration notification to the respective server(s).
        '''
        if serverID and self.server_list[serverID].notifyID:
            server = self.server_list[serverID]
            self._cxn.sendPacket(server.ID, (0, 0), 0, [(server.notifyID, c.ID, '(ww)')])
            return 1
        else:
            count = 0
            for s in self.server_list.values():
                if s.notifyID:
                    self._cxn.sendPacket(s.ID, (0, 0), 0, [(s.notifyID, c.ID, '(ww)')])
                    count += 1
            return count

    @setting(60, 'Subscribe to Named Message', name='s', ID='w', enable='b', returns=[''])
    def subscribe_to_named_message(self, c, name, ID, enable):
        '''(Un-)Register as a recipient for a named message. If
        another module calls Send Named Message", every module that is
        subscribed to that named message will receive a copy of the
        message sent to the message ID provided

        NOTE: The message will contain the ID of the sender and the
        payload in the form (w, ?). Message names are not case
        sensitive!
        '''
        message = self.named_messages.setdefault(name.lower(), NamedMessage(name))
        if enable:
            message.enable(c.source, c.ID, ID)
        else:
            message.disable(c.source, c.ID, ID)

    @setting(61, 'Send Named Message', name='s', data='?')
    def send_named_message(self, c, name, data):
        '''
        Sends a message to all the recipients signed up for the given name.

        NOTE: Message names are not case sensitive!
        '''
        try:
            message = self.named_messages[name.lower()]
        except KeyError:
            return
        for (dest, ctx, ID) in message.listeners:
            self._cxn.sendPacket(dest, ctx, 0, [(ID, (c.source, data), '(w,?)')])

    @setting(100, 'S: Register Setting', ID='w', name='s', desc='s',
             input_types='*s', output_types='*s', remarks='s', returns=[''])
    def s__register_setting(self, c, ID, name, desc, input_types, output_types, remarks):
        '''
        Register a server setting with the LabRAD manager
        NOTE: THIS SETTING IS ONLY AVAILABLE FOR SERVER CONNECTIONS!
        '''
        if c is not None:
            server_ID = c.source
        else:
            server_ID = 1
        # if not output_types: # Make empty list -> only allow None.  Default should be for empty list to mean allow any
        #    output_types = ['']
        self.server_list[server_ID].settings[ID] = Setting(ID, name, desc, input_types, output_types, remarks)

    @setting(101, 'S: Unregister Setting', setting=['s: Unregister setting with this name',
                                                    'w: Unregister setting with this ID'],
             returns='w: ID of removed setting')
    def s__unregister_setting(self, c, setting):
        '''
        Removes a registered setting from the LabRAD Manager's list
        NOTE: THIS SETTING IS ONLY AVAILABLE FOR SERVER CONNECTIONS!
        '''
        server = self.server_list[c.source]
        setting = setting_to_ID(server.ID, setting)
        del server.settings[setting]
        return setting

    @setting(110, 'S: Notify on Context Expiration', setting=[
        '(w, b): Request notifications to be sent to this setting number, supporting "expire all" if boolean is True',
        ': Stop notifications'])
    def s__notify_on_context_expiration(self, c, setting=None):
        '''
        Requests notifications if a context is expired
        Note: When a client disconnects or requests it, the manager
        will send context expiration notifications to all servers who
        requested them. The expiration notification will be sent as a message
        (request ID 0) to the setting ID specified in this request. The record
        will be either of format "w" for the expiration of all contexts with
        this high-word (only used if boolean is True) or "(ww)" to specify the
        exact context to expire.  THIS SETTING IS ONLY AVAILABLE FOR SERVER
        CONNECTIONS!
        '''
        if setting:
            self.server_list[c.source].notifyID = setting[0]
            self.server_list[c.source].notifyAll = bool(setting[0])
        else:
            self.server_list[c.source].notifyID = None
            self.server_list[c.source].notifyAll = False

    @setting(120, 'S: Start Serving')
    def s__start_serving(self, c):
        '''
        Marks a server ready for use. Before a server calls this setting, it
        will not appear in the listing of available servers.
        NOTE: THIS SETTING IS ONLY AVAILABLE FOR SERVER CONNECTIONS!
        '''
        server = self.server_list[c.source]
        server.visible = True
        print
        "Starting serving"
        self.send_named_message(c, 'Server Connect', server.name)
        # self.send_named_message(ctx, 'Server Connect', server.name)

    @setting(200, 'Data To String', data='?', returns='s')
    def data_to_string(self, c, data):
        '''
        Returns an unambiguous string representation of the data sent to it
        '''
        return delphi_compat.data_to_string(data)

    @setting(201, 'String To Data', s='s', returns='?')
    def string_to_data(self, c, s):
        '''
        Turns a string generated by "Data To String" back into LabRAD Data
        '''
        return delphi_compat.string_to_data(s)

    @setting(1000, "Convert Units", value=['v', '*v'],
             tag='s', returns=['v', '*v'])
    def convert_units(self, c, value, tag):
        '''
        Converts units
        '''
        if isinstance(value, list):
            return [v.inUnitsOf(tag) for v in value]
        else:
            return value.inUnitsOf(tag)

    # @setting(12345, data='?', returns='s')
    # def pretty_print(self, c, data):
    #    pass

    def register_server(self, server_name, desc, remarks):
        '''
        Called by the dispatcher when we have a new server connection
        '''
        connected_servers = [c.name for c in self.server_list.values()]
        if server_name in connected_servers:
            return 0
        try:
            ID = self.serverID_cache[server_name]
        except KeyError:
            ID = self.allocate_ID()

        self.server_list[ID] = ServerConnection(ID, server_name, desc, remarks)
        self.serverID_cache[server_name] = ID
        return ID

    def register_client(self, client_name):
        '''
        Called by the dispatcher when we have a new client connection
        '''
        ID = self.allocate_ID()
        self.client_list[ID] = ClientConnection(ID, client_name)
        return ID

    def unregister_connection(self, ID):
        '''
        Called when a connection is dropped
        '''
        for nm in self.named_messages.values():
            nm.disable_all(ID)
        try:
            client = self.client_list[ID]
            context_list = client.contexts
            del self.client_list[ID]
        except KeyError:
            server = self.server_list[ID]
            ctx = collections.namedtuple('CTX', ['source'])(ID)
            self.send_named_message(ctx, 'Server Disconnect', server.name)
            context_list = server.contexts
            del self.server_list[ID]
        for s in self.server_list.values():
            self.expire_contexts_server_all(s, ID, context_list)

    def expire_contexts_server_all(self, server, ID, context_list):
        if server.notifyID is None or not context_list:
            return
        if server.notifyAll:
            self._cxn.sendPacket(server.ID, (0, 0), 0, [(server.notifyID, ID, 'w')])
        else:
            for ctx in context_list:
                if ctx[0] == ID:  # Only expire contexts owned by this client
                    self._cxn.sendPacket(server.ID, (0, 0), 0, [(server.notifyID, ctx, 'w')])

    def allocate_ID(self):
        ID = self.next_ID
        self.next_ID += 1
        return ID

    def server_to_ID(self, server_name):
        if isinstance(server_name, (int, long)):
            tmp = self.server_list[server_name]  # raise key error if not present
            return server_name
        for k, v in self.server_list.items():
            if v.name.lower() == server_name.lower():
                return k
        raise KeyError("Server %s not found" % (server_name,))

    def setting_to_ID(self, server_ID, setting_name):
        if isinstance(setting_name, (int, long)):
            tmp = self.server_list[server_ID].settings[setting_name]  # raise error if not present
            return setting_name
        setting_list = self.server_list[server_ID].settings
        for k, v in setting_list.items():
            if v.name.lower() == setting_name.lower():
                return k
        raise KeyError('Setting %s not found' % (setting_name,))

    def update_packet_counts(self, source, dest):
        if source in self.server_list:
            self.server_list[source].sent_pkts += 1
        elif source in self.client_list:
            self.client_list[source].sent_pkts += 1

        if dest in self.server_list:
            self.server_list[dest].recv_pkts += 1
        elif dest in self.client_list:
            self.client_list[dest].recv_pkts += 1

    def register_context(self, ID, ctx):
        '''
        Keep a list of known contexts so we can send notifications to
        servers.
        '''
        try:
            self.client_list[ID].contexts.add(ctx)
        except KeyError:
            self.server_list[ID].contexts.add(ctx)

    def update_types(self, source, dest, request, records):
        '''
        Update the list of records type tags with the accepted record types
        for the given setting.  Unit conversion will be done during flattening.
        '''
        if request == 0:
            return records  # Don't convert signals
        if request > 0:  # Requests
            server = self.server_list[dest]
        else:  # Responses
            server = self.server_list[source]
        for idx in range(len(records)):
            settingID = records[idx][0]
            if not settingID:
                continue
            data = records[idx][1]
            setting = server.settings[settingID]
            if request > 0:
                allowed_types = setting.input_types
                if not allowed_types:
                    continue
            else:
                if not setting.output_types:
                    continue
                allowed_types = setting.output_types + [labrad.types.LRError(labrad.types.LRAny())]
            # this is temporary fix.  It converts units and type
            # according to the old manager behavior.  The desired
            # behavior is for unit/type conversion to be done at the
            # client with the server simply shuttling packets.
            try:
                data, t = delphi_compat.convert_units(data, allowed_types)
            except Exception as e:
                print
                "Unable to convert data for request %d to setting %d" % (request, settingID)
                print
                "data: '%s', allowed types: '%s'" % (data, allowed_types)
                raise
            records[idx] = (settingID, data, t)
        return records

    def stopServer(self):
        print
        "Manager calling stopServer"

    @setting(20, 'Whitelist', entry=['s: Add this entry to the whitelist', ': Retreive the whitelist'], returns=['*s'])
    def whitelist(self, c, entry):
        '''
        Adds an entry to the whitelist to allow a new computer to connect to LabRAD
        NOTE: Not implemented yet
        '''
        return ['Whitelist not remotely accessible']

    @setting(21, 'Blacklist', entry=[': Retreive the list of blacklisted connections', 's: host to blacklist'],
             returns=['*s'])
    def blacklist(self, c, entry=None):
        '''
        Removes an entry from the whitelist to no longer allow a computer to connect to LabRAD
        NOTE: Not implemented yet
        '''
        return ['Blacklist not remotely accessible']

# if __name__ == '__main__':
#    __server__ = ManagerServer()
#    from labrad import util
#    util.runServer(__server__)