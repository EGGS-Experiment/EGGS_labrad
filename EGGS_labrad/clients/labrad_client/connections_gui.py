from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QGridLayout, QTreeWidget, QTreeWidgetItem,\
    QWidget, QSplitter, QHBoxLayout, QVBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton as _TextChangingButton, QClientMenuHeader

# todo: make right click open menu to close
# todo: make double click open documentation in RHS
# todo: set colors
# todo: set relative ratio of sizes


class ConnectionTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.setWindowTitle("LabRAD Connections")
        self.parent = parent

        # specific initialization
        self.setColumnCount(9)
        self.setHeaderLabels([
            "ID", "Type", "Name",
            "Server Requests", "Server Responses",
            "Client Requests", "Client Responses",
            "Messages Sent", "Messages Received",

        ])

    def createConnection(self, connection_data):
        """
        Creates and returns a QTreeWidgetItem that represents a LabRAD connection.
        Arguments:
            connection_data (dataset_location, dataset_name, artist_name): a unique identifier for an artist.
        """
        # create connection item
        connection_data = list(map(str, connection_data))
        connection_item = QTreeWidgetItem(self, connection_data)
        return connection_item

    def removeConnection(self, connection_item):
        """
        Removes the QTreeWidgetItem corresponding to a given connection ID.
        Arguments:
            connection_item (QTreeWidgetItem): the connection ID of the connection_item to be removed.
        """
        try:
            # get connection item and its index
            connection_item_index = self.indexOfTopLevelItem(connection_item)
            # remove from widget
            self.takeTopLevelItem(connection_item_index)
        except KeyError as e:
            print("Error in connectionClient.removeConnection: {}".format(e))


class DocumentationTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.setWindowTitle("LabRAD Connections")
        self.documentation_dict = {}
        self.parent = parent

        # specific initialization
        self.setColumnCount(2)
        self.setHeaderLabels(["ID", "Name"])

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

        # add documentation_item to documentation_dict
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
        # general initialization
        super().__init__()
        self.setWindowTitle("LabRAD Connections")
        self.parent = parent

        # make UI
        self.makeWidgets()
        self.showMaximized()

        # todo: create signals/whatever to interact w/connections client

        # test tmp remove
        self.connectionWidget.createConnection(("test server ID", "Server", "test server type", 0, 1, 2, 3, 4, 5))
        self.documentationWidget.createDocumentation(("doc 1", "doc 2", "doc 3", "doc 4", "doc 5", "doc 6"))

    def makeWidgets(self):
        # create connection widget
        self.connectionWidget = ConnectionTreeWidget(self.parent)
        connection_widget_holder = QWidget()
        connection_layout = QVBoxLayout(connection_widget_holder)
        connection_layout.addWidget(QLabel('Connections:'))
        connection_layout.addWidget(self.connectionWidget)

        # create documentation widget
        self.documentationWidget = DocumentationTreeWidget(self.parent)
        documentation_widget_holder = QWidget()
        documentation_layout = QVBoxLayout(documentation_widget_holder)
        documentation_layout.addWidget(QLabel('Documentation:'))
        documentation_layout.addWidget(self.documentationWidget)

        # create splitter
        splitter_widget = QSplitter()
        splitter_widget.setOrientation(Qt.Horizontal)
        splitter_widget.addWidget(connection_widget_holder)
        splitter_widget.addWidget(documentation_widget_holder)

        # create title widget
        title_widget = QLabel('LabRAD Connections')
        title_widget.setFont(QFont('MS Shell Dlg 2', pointSize=20))
        title_widget.setAlignment(Qt.AlignCenter)

        # create layout
        layout = QVBoxLayout(self)
        layout.addWidget(title_widget)
        layout.addWidget(splitter_widget)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(ConnectionsGUI)
