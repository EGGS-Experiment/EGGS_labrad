"""
Contains utilities to create connections to LabRAD.
"""

__all__ = ["connection"]

from twisted.internet.defer import inlineCallbacks, returnValue


class connection(object):
    """
    The shared connection object allows multiple asynchronous
    clients to share a single connection to the manager.

    version = 1.0.1
    """

    def __init__(self, **kwargs):
        # holds servers that we need
        self._servers = {}
        # holds startup actions for each server
        self._on_connect = {}
        # holds disconnect actions for each server
        self._on_disconnect = {}
        # set name from kwargs
        if 'name' not in kwargs:
            kwargs['name'] = ''
        self.name = kwargs['name']
    
    @inlineCallbacks
    def connect(self):
        """
        Connect asynchronously to the labrad manager.
        """
        import os
        LABRADHOST = os.environ['LABRADHOST']
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(host=LABRADHOST, name=self.name)
        yield self.setupListeners()
        returnValue(self)

    @inlineCallbacks
    def context(self):
        """
        Returns a context object.
        Follows the same form as one would use on a normal cxn object.
        """
        context = yield self.cxn.context()
        returnValue(context)

    def disconnect(self):
        """
        Disconnect from the LabRAD manager.
        """
        self.cxn.disconnect()
    
    @inlineCallbacks
    def get_server(self, server_name):
        """
        Ensures that a server is available and connects to it.
        Needed since setting a nonexistent server as an attribute
        will cause the program to freeze.
        """
        connected = yield self._confirm_connected(server_name)
        if connected:
            returnValue(self._servers[server_name])
        else:
            raise Exception('{} not available.'.format(server_name))
        
    @inlineCallbacks
    def add_on_connect(self, server_name, action):
        """
        Adds a given action (a function) to be executed when the server connects.
        Arguments:
            server_name     (str)   : the connected server
            action          (func)  : the function to run when the server connects
        """
        # check if server is connected; do nothing if not
        connected = yield self._confirm_connected(server_name)
        if not connected:
            print('{} not available.'.format(server_name))
            return
        # add action to list of server disconnect actions
        try:
            self._on_connect[server_name].append(action)
        except KeyError:
            self._on_connect[server_name] = [action]
    
    @inlineCallbacks
    def add_on_disconnect(self, server_name, action):
        """
        Adds a given action (a function) to be executed when the server disconnects.
        Arguments:
            server_name     (str)   : the connected server
            action          (func)  : the function to run when the server disconnects
        """
        # check if server is connected; do nothing if not
        connected = yield self._confirm_connected(server_name)
        if not connected:
            print('{} not available.'.format(server_name))
            return
        # add action to list of server disconnect actions
        try:
            self._on_disconnect[server_name].append(action)
        except KeyError:
            self._on_disconnect[server_name] = [action]


    # SIGNALS
    @inlineCallbacks
    def setupListeners(self):
        """
        Sets up listeners and signals.
        Receives a message and executes some actions whenever any server is connected or disconnected.
        """
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self._follow_server_connect, source=None, ID=9898989)
        yield self.cxn.manager.addListener(listener=self._follow_server_disconnect, source=None, ID=9898989 + 1)

    @inlineCallbacks
    def _follow_server_connect(self, c, message):
        """
        Runs when any new server connects.
        Checks to see if connected server is one we need,
        and if so, runs actions specified by add_on_connect.
        """
        # message is a tuple of (messageID, servername)
        server_name = message[1]
        print('server connect: {}'.format(server_name))
        # check to see if we need server
        if server_name in self._servers.keys():
            yield self.cxn.refresh()
            print('{} connected'.format(server_name))
            self._servers[server_name] = yield self.cxn[server_name]
            # run startup actions
            actions = self._on_connect[server_name]
            for action in actions:
                yield action()

    @inlineCallbacks
    def _follow_server_disconnect(self, c, message):
        """
        Runs when any server disconnects.
        Checks to see if disconnected server is one we are using,
        and if so, runs actions specified by add_on_disconnect.
        """
        # message is a tuple of (messageID, servername)
        server_name = message[1]
        print('server disconnect: {}'.format(server_name))
        # check to see if we are using server
        if server_name in self._servers.keys():
            print('{} disconnected'.format(server_name))
            self._servers[server_name] = None
            # run disconnect actions
            actions = self._on_disconnect[server_name]
            for action in actions:
                yield action()


    # HELPER
    @inlineCallbacks
    def _confirm_connected(self, server_name):
        """
        Checks to see whether a given server is available
        and adds it to the list of connected servers
        """
        if server_name not in self._servers:
            try:
                self._servers[server_name] = yield self.cxn[server_name]
            except Exception as e:
                returnValue(False)
        returnValue(True)


if __name__ == '__main__':
    from twisted.internet import reactor
    app = connection()
    reactor.callWhenRunning(app.connect)
    reactor.run()
