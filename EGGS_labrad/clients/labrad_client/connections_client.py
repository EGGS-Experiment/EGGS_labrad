from PyQt5.QtCore import Qt
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.labrad_client.connections_gui import ConnectionsGUI


class ConnectionsClient(GUIClient):
    """
    Displays all connections to the LabRAD manager
    as well as their documentation.
    """

    name = 'Connections Client'
    servers = {'mgr': 'Manager'}
    POLL_INTERVAL = 5

    def getgui(self):
        if self.gui is None:
            # we have to pass self to ConnectionsGUI
            # to allow ConnectionsGUI to interact with us
            self.gui = ConnectionsGUI(self)
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # create main polling loop
        self.refresher = LoopingCall(self.getConnectionInfo)
        # create holding dictionaries
        self.connection_dict = {}

    @inlineCallbacks
    def initData(self):
        yield self.getConnectionInfo()

    def initGUI(self):
        # todo: close connection
        # todo: open documentation
        #self.gui.ip_lockswitch.toggled.connect(lambda status: self.lock_ip(status))
        self.refresher.start(self.POLL_INTERVAL, now=False)


    # SLOTS
    @inlineCallbacks
    def getConnectionInfo(self):
        """
        Gets information on all connections from the manager and
            updates the display.
        """
        # get servers
        connection_info = yield self.mgr.connection_info()
        connection_info = {data[0: 2]: data for data in connection_info}

        # get new and old servers
        old_connections = set(self.connection_dict.keys())
        current_connections = set(connection_info.keys())
        additions = current_connections - old_connections
        deletions = old_connections - current_connections
        persistent = old_connections.intersection(current_connections)

        # remove deleted servers
        for connection_ident in deletions:
            connection_item = self.connection_dict.pop(connection_ident)
            self.gui.connectionWidget.removeConnection(connection_item)

        # add new servers
        for connection_ident in additions:
            # get connection data
            connection_data = connection_info[connection_ident]
            # create connection item and add it to connection_dict
            connection_item = self.gui.connectionWidget.createConnection(connection_data)
            self.connection_dict[connection_ident] = connection_item

        # update old servers
        for connection_ident in persistent:
            connection_data = connection_info[connection_ident]
            connection_item = self.connection_dict[connection_ident]
            for i, val in enumerate(connection_data):
                connection_item.setData(i, Qt.DisplayRole, val)

    @inlineCallbacks
    def updateDocumentation(self, server_ID):
        """
        Gets the documentation for the given server and displays
            it in the Documentation Widget.
        Arguments:
            server_ID   (int)   : the server ID to get documentation for.
        """
        # get documentation for the server
        server_info = yield self.mgr.help(server_ID)
        # get server settings
        setting_data = yield self.mgr.lr_settings(server_ID)
        # get documentation for each setting
        for th1 in range(5):
            th1 = yield self.mgr.help((server_ID, th1))
            # todo: add documentation to list
        # todo: create documentation
        #self.gui.

    # @inlineCallbacks
    # def onDoubleclick(self, item):
    #     item = self.dataListWidget.currentItem().text()
    #     # previous directory
    #     if item == '...':
    #         yield self.dv.cd(1, context=self._context)
    #         if len(self.directoryString) > 1:
    #             self.directoryString.pop()
    #             self.directoryLabel.setText('\\'.join(self.directoryString))
    #         self.populate()
    #     else:
    #         try:
    #             # next directory
    #             yield self.dv.cd(str(item), context=self._context)
    #             self.directoryString.append(str(item))
    #             self.directoryLabel.setText('\\'.join(self.directoryString))
    #             self.populate()
    #         except:
    #             # plot if no directories left
    #             path = yield self.dv.cd(context=self._context)
    #             if self.root is not None:
    #                 yield self.root.do_plot((path, str(item)), self.tracename, False)
    #             else:
    #                 yield self.grapher.plot((path, str(item)), self.tracename, False)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(ConnectionsClient)
