from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QDoubleSpinBox, QComboBox, QGridLayout, QTreeWidget, QTreeWidgetItem,\
    QWidget, QSplitter, QHBoxLayout, QVBoxLayout, QGridLayout

from EGGS_labrad.clients.Widgets import TextChangingButton as _TextChangingButton, QClientMenuHeader

# todo: make right click open menu to close
# todo: make right clock open documentation in RHS


class ConnectionTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.setWindowTitle("LabRAD Connections")

        # specific initialization
        self.setColumnCount(9)
        self.setHeaderLabels([
            "ID", "Type", "Name",
            "Server Requests", "Server Responses",
            "Client Requests", "Client Responses",
            "Messages Sent", "Messages Received",

        ])
        self.connection_dict = {}

    def createConnection(self, connection_data):
        """
        Creates and returns a QTreeWidgetItem that represents a LabRAD connection.
        Arguments:
            connection_data (dataset_location, dataset_name, artist_name): a unique identifier for an artist.
        """
        # create connection item
        connection_id = connection_data[0]
        connection_data = list(map(str, connection_data))
        connection_item = QTreeWidgetItem(self, connection_data)
        # add connection_item to connection_dict
        self.connection_dict[connection_id] = connection_item
        return connection_item

    def removeConnection(self, connection_ID):
        """
        Removes the QTreeWidgetItem corresponding to a given connection ID.
        Arguments:
            connection_ID   (int): the connection ID of the connection_item to be removed.
        """
        try:
            # get connection item and its index
            connection_item = self.connection_dict.pop(connection_ID)
            connection_item_index = self.indexOfTopLevelItem(connection_item)
            # remove from widget
            self.takeTopLevelItem(connection_item_index)
        except KeyError as e:
            print("Error in connectionClient.removeConnection: connection ID {} not associated with a connection.".format(connection_ID))
            print(e)


class DocumentationTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__()
        # general initialization
        self.setWindowTitle("LabRAD Connections")
        # specific initialization
        self.setColumnCount(2)
        self.setHeaderLabels(["ID", "Name"])
        # test
        self.documentation_dict = {}

    def createDocumentation(self, setting_data):
        """
        Creates and returns a QTreeWidgetItem that holds
            the documentation for a server Setting.
        Arguments:
            setting_data    (tmp): a unique identifier for an artist.
        """
        # create documentation item
        setting_id, setting_name = setting_data[0: 2]
        documentation_data = [str(setting_id), setting_name]
        documentation_item = QTreeWidgetItem(self, documentation_data)
        documentation_item.setExpanded(True)

        # add connection_item to connection_dict
        self.documentation_dict[setting_id] = documentation_item

        # add text to documentation item
        for text_data in setting_data[2:]:
            # create setting documentation objects
            setting_documentation = QTreeWidgetItem(documentation_item, [text_data])
            setting_documentation.setFirstColumnSpanned(True)
            # make setting documentation objects children of documentation_data
            documentation_item.addChild(setting_documentation)

    def clear(self, connection_ID):
        """
        Removes all documentation objects.
        """
        for index in range(self.topLevelItemCount()):
            documentation_item = self.takeTopLevelItem(index)
            documentation_item.takeChildren()


class ConnectionsGUI(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        # general initialization
        self.setWindowTitle("LabRAD Connections")
        # make UI
        self.makeWidgets()
        self.showMaximized()

        # test tmp remove
        #self.connectionWidget.createConnection(("test server ID", "Server", "test server type", 0, 1, 2, 3, 4, 5))
        #self.documentationWidget.createDocumentation(("doc 1", "doc 2", "doc 3", "doc 4", "doc 5", "doc 6"))

    def makeWidgets(self):
        layout = QGridLayout(self)

        # create connection widget
        self.connectionWidget = ConnectionTreeWidget()

        # create documentation widget
        self.documentationWidget = DocumentationTreeWidget()
        documentation_widget_holder = QWidget()
        documentation_layout = QVBoxLayout(documentation_widget_holder)
        documentation_layout.addWidget(QLabel('Documentation:'))
        documentation_layout.addWidget(self.documentationWidget)

        # create splitter
        splitter_widget = QSplitter()
        splitter_widget.setOrientation(Qt.Horizontal)
        splitter_widget.addWidget(self.connectionWidget)
        splitter_widget.addWidget(documentation_widget_holder)
        layout.addWidget(splitter_widget)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(ConnectionsGUI)
