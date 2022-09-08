
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QWidget, QSplitter, QVBoxLayout,\
    QPlainTextEdit, QGridLayout, QMenu, QColumnView

# todo: set colors
# todo: create signals/whatever to interact w/connections client
# todo: make arguments a list
# todo: use qcolumnview


class RegistryBrowserWidget(QColumnView):
    """
    todo: document
    """

    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.parent = parent

        # specific initialization

        self.model = QStandardItemModel(self)
        self.setModel(self.model)
        parent = self.model.invisibleRootItem()

        #
        for child in ['a','b','c', 'aa','bb','cc']:
            child_item = QStandardItem(child)
            parent.appendRow(child_item)
            child_item_21 = QStandardItem('1')
            child_item_22 = QStandardItem('2')
            child_item_23 = QStandardItem('3')
            child_item.appendRow(child_item_21)
            child_item.appendRow(child_item_22)
            child_item.appendRow(child_item_23)
            # if isinstance(children, dict):
            #     populateTree(children[child], child_item)

        # self.setColumnCount(9)
        # self.setHeaderLabels([
        #     "ID", "Name", "Server?",
        #     "Server Requests", "Server Responses",
        #     "Client Requests", "Client Responses",
        #     "Messages Sent", "Messages Received",
        # ])
        # self.setSortingEnabled(True)
        # self.sortByColumn(0, Qt.AscendingOrder)
        #
        # self.setContextMenuPolicy(Qt.CustomContextMenu)
        # self.customContextMenuRequested.connect(self.popupMenu)

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


class RegistryEditorWidget(QWidget):
    """
    todo: document
    """

    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.makeLayout()

    def makeLayout(self):
        # make widgets
        # todo: set fonts
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
        todo
        """
        # remove old server documentation
        self.server_description.clear()

        # add new server documentation
        self.server_num.setText(str(server_data[0]))
        self.server_name.setText(server_data[1])
        self.server_description.appendPlainText(server_data[2])


class RegistryGUI(QWidget):
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
        # create browser widget
        self.browserWidget = RegistryBrowserWidget(self.parent)
        browser_widget_holder = QWidget()
        browser_layout = QVBoxLayout(browser_widget_holder)
        browser_layout.addWidget(QLabel('Browser:'))
        browser_layout.addWidget(self.browserWidget)

        # create editor widget
        self.editorWidget = RegistryEditorWidget(self.parent)
        editor_widget_holder = QWidget()
        editor_layout = QVBoxLayout(editor_widget_holder)
        editor_layout.addWidget(QLabel('Editor:'))
        editor_layout.addWidget(self.editorWidget)

        # create splitter
        splitter_widget = QSplitter()
        splitter_widget.setOrientation(Qt.Horizontal)
        splitter_widget.addWidget(browser_widget_holder)
        splitter_widget.addWidget(editor_widget_holder)

        # create title widget
        title_widget = QLabel('LabRAD Registry')
        title_widget.setFont(QFont('MS Shell Dlg 2', pointSize=20))
        title_widget.setAlignment(Qt.AlignCenter)

        # create layout
        layout = QVBoxLayout(self)
        layout.addWidget(title_widget,      stretch=1)
        layout.addWidget(splitter_widget,   stretch=20)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(RegistryBrowserWidget)
