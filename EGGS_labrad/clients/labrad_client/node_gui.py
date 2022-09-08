from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QWidget, QSplitter, QVBoxLayout,\
    QPlainTextEdit, QGridLayout, QMenu, QTableWidget, QTableWidgetItem, QPushButton

# todo: may have to create custom item/model views

# store servers as dicts


class NodeServerWidgetItem(QTreeWidgetItem):
    """
    todo: document
    """

    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.parent = parent


class NodeTableWidget(QTableWidget):
    """
    todo: document
    """

    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.parent = parent

        # specific initialization
        self.setColumnCount(9)
        self.setHeaderLabels([
            "ID", "Name", "Server?",
            "Server Requests", "Server Responses",
            "Client Requests", "Client Responses",
            "Messages Sent", "Messages Received",
        ])
        self.setSortingEnabled(True)
        self.sortByColumn(0, Qt.AscendingOrder)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popupMenu)

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

    def popupMenu(self, pos):
        """
        todo: document
        """
        # set up menu
        menu = QMenu()
        actionDict = {}
        item = self.itemAt(pos)

        # permanent options
        actionDict['closeConnectionAction'] = menu.addAction('Close Connection')

        # process actions
        action = menu.exec_(self.mapToGlobal(pos))
        if action == actionDict.get('closeConnectionAction'):
            self.parent.closeConnection(item)
            pass


class ConnectionsGUI(QWidget):
    """
    todo: document
    """

    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.setWindowTitle("LabRAD Connections")
        self.parent = parent

        # make UI
        self.makeWidgets()
        self.showMaximized()

    def makeWidgets(self):
        # create connection widget
        self.connectionWidget = ConnectionTreeWidget(self.parent)
        connection_widget_holder = QWidget()
        connection_layout = QVBoxLayout(connection_widget_holder)
        connection_layout.addWidget(QLabel('Connections:'))
        connection_layout.addWidget(self.connectionWidget)

        # create documentation widget
        self.serverDocumentationWidget = ServerDocumentationWidget(self.parent)
        self.settingDocumentationWidget = SettingDocumentationWidget(self.parent)
        documentation_widget_holder = QWidget()
        documentation_layout = QVBoxLayout(documentation_widget_holder)
        documentation_layout.addWidget(QLabel('Documentation:'))
        documentation_layout.addWidget(self.serverDocumentationWidget,      stretch=1)
        documentation_layout.addWidget(self.settingDocumentationWidget,     stretch=4)

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
        layout.addWidget(title_widget,      stretch=1)
        layout.addWidget(splitter_widget,   stretch=20)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(ConnectionsGUI)
