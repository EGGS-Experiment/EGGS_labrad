from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QWidget, QSplitter, QVBoxLayout, QPlainTextEdit, QGridLayout, QMenu

from EGGS_labrad.clients.Widgets import QCustomGroupBox
# todo: merge server and documentation widgets
# todo: make constituent widget functions available in composite GUI and have client only access those


class ConnectionTreeWidget(QTreeWidget):
    """
    GUI for displaying all connections to the LabRAD manager.
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
        Creates a popupMenu upon right-clicking.
        Arguments:
            pos (QPoint): the position of the right-clicked item.
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


class ServerDocumentationWidget(QWidget):
    """
    GUI for displaying server documentation.
    """

    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.makeLayout()

    def makeLayout(self):
        # make widgets
        server_num_label = QLabel("Server ID:")
        self.server_num = QLabel("N/A")
        server_name_label = QLabel("Server Name:")
        self.server_name = QLabel("N/A")
        server_description_label = QLabel("Server Description:")
        self.server_description = QPlainTextEdit()
        self.server_description.setReadOnly(True)
        # lay out
        layout = QGridLayout(self)
        layout.addWidget(server_num_label,          0, 0, 1, 1)
        layout.addWidget(self.server_num,           0, 1, 1, 1)
        layout.addWidget(server_name_label,         0, 2, 1, 1)
        layout.addWidget(self.server_name,          0, 3, 1, 1)
        layout.addWidget(server_description_label,  2, 0, 1, 1)
        layout.addWidget(self.server_description,   3, 0, 3, 4)

    def addServerDocumentation(self, server_data):
        """
        Display documentation for a new server.
        """
        # remove old server documentation
        self.server_description.clear()

        # add new server documentation
        self.server_num.setText(str(server_data[0]))
        self.server_name.setText(server_data[1])
        self.server_description.appendPlainText(server_data[2])


class SettingDocumentationWidget(QTreeWidget):
    """
    GUI for displaying server setting documentation.
    """

    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.documentation_dict = {}
        self.parent = parent

        # specific initialization
        self.setColumnCount(2)
        self.setHeaderLabels(["ID", "Name"])

    def addSettingDocumentation(self, setting_data):
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
        # todo: add title of what it is
        for text_data in setting_data[2:-1]:
            # create setting documentation objects
            setting_documentation = QTreeWidgetItem(documentation_item, [str(text_data)])
            setting_documentation.setFirstColumnSpanned(True)
            # make setting documentation objects children of documentation_data
            documentation_item.addChild(setting_documentation)

    def clear(self):
        """
        Removes all documentation objects.
        """
        # remove documentation_items in QTreeWidget
        for index in reversed(range(self.topLevelItemCount())):
            documentation_item = self.topLevelItem(index)
            documentation_item.takeChildren()
            self.takeTopLevelItem(index)

        # clear holding dictionary
        self.documentation_dict.clear()


class ConnectionsGUI(QWidget):
    """
    GUI for the LabRAD connections page.
    Uses ConnectionTreeWidget, ServerDocumentationWidget, and SettingDocumentationWidget.
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

        # create documentation widget
        self.serverDocumentationWidget = ServerDocumentationWidget(self.parent)
        self.settingDocumentationWidget = SettingDocumentationWidget(self.parent)
        documentation_widget_holder = QWidget()
        documentation_layout = QVBoxLayout(documentation_widget_holder)
        documentation_layout.addWidget(self.serverDocumentationWidget,      stretch=1)
        documentation_layout.addWidget(self.settingDocumentationWidget,     stretch=4)

        # create splitter
        splitter_widget = QSplitter()
        splitter_widget.setOrientation(Qt.Horizontal)
        splitter_widget.addWidget(QCustomGroupBox(self.connectionWidget, "Connections"))
        splitter_widget.addWidget(QCustomGroupBox(documentation_widget_holder, "Documentation"))
        splitter_widget.setStretchFactor(0, 8)
        splitter_widget.setStretchFactor(1, 2)
        # splitter_widget.moveSplitter(50, 0)
        # splitter_widget.moveSplitter(50, 1)

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
