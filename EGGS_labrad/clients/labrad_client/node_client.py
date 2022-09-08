from PyQt5.QtCore import Qt
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.labrad_client.connections_gui import ConnectionsGUI


class NodeClient(GUIClient):
    """
    Displays all connections to the LabRAD manager
    as well as their documentation.
    """

    name = 'Connections Client'
    servers = {'mgr': 'Manager'}
    POLL_INTERVAL = 1
    menuCreate = False

    def getgui(self):
        if self.gui is None:
            # we have to pass self to ConnectionsGUI
            # to allow ConnectionsGUI to interact with us
            self.gui = ConnectionsGUI(self)
        return self.gui

    def initClient(self):
        # create main polling loop
        self.refresher = LoopingCall(self.getConnectionInfo)
        # create holding dictionaries
        self.connection_dict = {}

    @inlineCallbacks
    def initData(self):
        yield self.getConnectionInfo()

    def initGUI(self):
        self.gui.connectionWidget.itemDoubleClicked.connect(lambda connection_item, index: self.updateDocumentation(connection_item))
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
        connection_info = {(str(data[0]), data[1]): data for data in connection_info}

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
    def updateDocumentation(self, connection_item):
        """
        Gets the documentation for the given server and displays
            it in the Documentation Widget.
        Arguments:
            server_ident (str, str): the server identification to get documentation for.
        """
        # get and set documentation for the server
        server_ID, server_name = (connection_item.data(0, Qt.DisplayRole), connection_item.data(1, Qt.DisplayRole))
        server_info = yield self.mgr.help(int(server_ID))
        self.gui.serverDocumentationWidget.addServerDocumentation((server_ID, server_name, server_info[0]))

        # get and set documentation for all settings
        self.gui.settingDocumentationWidget.clear()
        setting_info = {}
        setting_data = yield self.mgr.lr_settings(server_name)
        for setting_number, setting_name in setting_data:
            documentation_tmp = yield self.mgr.help((int(server_ID), setting_number))
            documentation_tmp = (str(setting_number), setting_name, *documentation_tmp)
            setting_info[setting_number] = documentation_tmp
            # create documentation
            self.gui.settingDocumentationWidget.addSettingDocumentation(documentation_tmp)

    @inlineCallbacks
    def closeConnection(self, connection_item):
        """
        Close a LabRAD connection.
        Arguments:
            cxn_ident (str, str): the connection to close.
        """
        try:
            # remove connection item from GUI
            connection_ident = (connection_item.data(0, Qt.DisplayRole), connection_item.data(1, Qt.DisplayRole))
            connection_item = self.connection_dict.pop(connection_ident)
            self.gui.connectionWidget.removeConnection(connection_item)
            # close labrad connection
            yield self.mgr.close_connection(int(connection_ident[0]))
        except Exception as e:
            print('connection dict: {}'.format(self.connection_dict.keys()))
            print(e)


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(NodeClient)
