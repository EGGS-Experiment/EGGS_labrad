from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QLabel, QTreeWidget, QTreeWidgetItem, QWidget, QSplitter, QVBoxLayout,\
    QPlainTextEdit, QGridLayout, QMenu, QColumnView, QListWidgetItem, QPushButton, QHBoxLayout, QListWidget, QScrollArea,\
    QLineEdit

from EGGS_labrad.clients.Widgets import QCustomGroupBox
# todo: use qcolumnview
# todo: make keys and directories look different
# todo: copy
# todo: function to allow changing of key/directory name
# todo: double click away sets readonly of edito to false
# todo: enable click away
# todo: display key value on rhs in browser
# todo: add cliked and qpoint thing
# todo: convert string to code


class RegistryBrowserWidget(QWidget):
    """
    Data vault window used to select datasets for plotting.
    Creates a client connection to LabRAD to access the datavault and grapher servers.
    """
    changeDirectory = pyqtSignal(str)
    makeDirectory = pyqtSignal(list)
    removeDirectory = pyqtSignal(str)
    openKey = pyqtSignal(str)
    makeKey = pyqtSignal(list)
    removeKey = pyqtSignal(str)

    refreshDirectory = pyqtSignal()


    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.parent = parent

        # specific initialization
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popupMenu)
        self.current_directory = None
        self.initializeGUI()

    def initializeGUI(self):
        # create widgets
        self.browser = QListWidget()
        self.browser.itemDoubleClicked.connect(lambda _item: self.onDoubleClick(_item))
        self.directoryLabel = QLabel('Home')
        browserScroll = QScrollArea()
        browserScroll.setWidget(self.directoryLabel)
        browserScroll.setWidgetResizable(True)
        browserScroll.setFixedHeight(40)

        # create layout
        mainLayout = QGridLayout(self)
        mainLayout.addWidget(QLabel('Directory Location:'))
        mainLayout.addWidget(browserScroll)
        mainLayout.addWidget(self.browser)
        self.setWindowTitle('Registry')

    def set(self, directory_list, directories, keys):
        """
        Displays the directory information.
        Arguments:
            directory_list (list(str)): the name of the directory to display.
            directories (list(str)): a list of all subdirectories in the current directory.
            keys (list(str)): a list of all keys in the current directory.
        """
        # remove old directories
        self.browser.clear()

        # set directory name
        self.current_directory = directory_list
        self.directoryLabel.setText('\\'.join(directory_list))

        # create previous directory item
        prevdir_item = QListWidgetItem('...')
        prevdir_item.setData(Qt.UserRole, 'dir')
        self.browser.addItem(prevdir_item)

        # set directories
        for subdirectory_name in directories:
            subdirectory_item = QListWidgetItem(subdirectory_name)
            subdirectory_item.setData(Qt.UserRole, "dir")
            self.browser.addItem(subdirectory_item)

        # set datasets
        for key_name in keys:
            key_item = QListWidgetItem(key_name)
            key_item.setData(Qt.UserRole, "key")
            self.browser.addItem(key_item)

    def onDoubleClick(self, item):
        """
        Process a double click event.
        Arguments:
            ind (QModelIndex): the index of the item.
        """
        # get type of item that was clicked
        item_type, item_text = item.data(Qt.UserRole), item.text()

        # change directory
        if item_type == 'dir':
            self.changeDirectory.emit(item_text)
        # open key
        elif item_type == 'key':
            self.openKey.emit(item_text)

    def popupMenu(self, pos):
        """
        Creates a popupMenu upon right-clicking.
        Arguments:
            pos (QPoint): the position of the right-clicked item.
        """
        # set up menu
        menu = QMenu()
        actionDict = {}
        item = self.browser.currentItem()
        item_text = None

        # options if an item is selected
        if item is not None:
            item_type, item_text = item.data(Qt.UserRole), item.text()
            # directory options
            if (item_type == 'dir') and (item.text() != '...'):
                actionDict['removeDirectoryAction'] = menu.addAction('Delete Directory')
            # key options
            elif item_type == 'key':
                actionDict['removeKeyAction'] = menu.addAction('Delete Key')
        # options if nothing is selected
        else:
            actionDict['refreshAction'] = menu.addAction('Refresh')
            actionDict['makeDirectoryAction'] = menu.addAction('New Directory')
            actionDict['makeKeyAction'] = menu.addAction('New Key')

        # process actions
        action = menu.exec_(self.mapToGlobal(pos))
        if action == actionDict.get('refreshAction'):
            self.refreshDirectory.emit()
        elif action == actionDict.get('makeDirectoryAction'):
            self.makeDirectory.emit(self.current_directory)
        elif action == actionDict.get('makeKeyAction'):
            self.makeKey.emit(self.current_directory)
        elif action == actionDict.get('removeDirectoryAction'):
            self.removeDirectory.emit(item_text)
        elif action == actionDict.get('removeKeyAction'):
            self.removeKey.emit(item_text)


class RegistryEditorWidget(QWidget):
    """
    GUI for editing directories and key/value pairs in the registry.
    """
    createDirectorySignal = pyqtSignal(str, list)
    createKeySignal = pyqtSignal(str, str, list)

    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.makeLayout()

    def makeLayout(self):
        # action
        action_label = QLabel('Action:')
        self.action_text = QLabel('N/A')
        self.action_text.setAlignment(Qt.AlignLeft)

        # directory
        directory_label = QLabel('Directory:')
        self.directory_text = QLabel('Home')
        browserScroll = QScrollArea()
        browserScroll.setWidget(self.directory_text)
        browserScroll.setWidgetResizable(True)
        browserScroll.setFixedHeight(40)

        # editable
        name_label = QLabel('Name:')
        self.name_edit = QLineEdit()
        self.name_edit.setReadOnly(True)
        value_label = QLabel("Value:")
        self.value_edit = QLineEdit()
        self.value_edit.setReadOnly(True)

        # save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(lambda: self.save())

        # lay out
        layout = QGridLayout(self)
        layout.addWidget(action_label,                      0, 0, 1, 1)
        layout.addWidget(self.action_text,                  0, 1, 1, 1)
        layout.addWidget(self.save_button,                  0, 2, 1, 1)
        layout.addWidget(directory_label,                   1, 0, 1, 1)
        layout.addWidget(self.directory_text,               1, 1, 1, 7)
        layout.addWidget(name_label,                        2, 0, 1, 1)
        layout.addWidget(self.name_edit,                    2, 1, 1, 7)
        layout.addWidget(value_label,                       3, 0, 1, 1)
        layout.addWidget(self.value_edit,                   3, 1, 1, 7)

    def makeDirectory(self, directory):
        """
        Create a new directory.
        Arguments:
            directory (list(str)): the directory to create the new subdirectory in.
        """
        self.action_text.setText('Create new directory')
        self.directory_text.setText('\\'.join(directory))
        self.name_edit.clear()
        self.name_edit.setReadOnly(False)
        self.value_edit.clear()
        self.value_edit.setReadOnly(True)

    def makeKey(self, directory):
        """
        Create a new key-value pair.
        Arguments:
            directory (list(str)): the directory to create the new subdirectory in.
        """
        self.action_text.setText('Create new key')
        self.directory_text.setText('\\'.join(directory))
        self.name_edit.clear()
        self.name_edit.setReadOnly(False)
        self.value_edit.clear()
        self.value_edit.setReadOnly(False)

    def openKey(self, keyname, value, directory):
        """
        Display a key and its values.
        Arguments:
            keyname (str): the name of the key to open.
            value (?): the value to set the key to.
            directory (list(str)): the directory to create the new subdirectory in.
        """
        self.action_text.setText('Editing key')
        self.directory_text.setText('\\'.join(directory))
        self.name_edit.setReadOnly(False)
        self.name_edit.setText(keyname)
        self.value_edit.setReadOnly(False)
        self.value_edit.setText(str(value))

    def save(self):
        # call correct signal
        if 'directory' in self.action_text.text().lower():
            directory_name = self.name_edit.text()
            self.createDirectorySignal.emit(directory_name, ['Home'])
        elif 'key' in self.action_text.text().lower():
            key_name = self.name_edit.text()
            key_value = self.value_edit.text()
            self.createKeySignal.emit(key_name, key_value, ['Home'])
        # reset editor widget
        self.action_text.setText('N/A')
        self.directory_text.setText('Home')
        self.name_edit.clear()
        self.name_edit.setReadOnly(True)
        self.value_edit.clear()
        self.value_edit.setReadOnly(True)


class RegistryGUI(QWidget):
    """
    GUI for the LabRAD Registry page.
    Uses RegistryBrowserWidget and RegistryEditorWidget.
    """
    makeDirectory = pyqtSignal(str)
    makeKey = pyqtSignal(str, str)

    def __init__(self, parent=None):
        # general initialization
        super().__init__()
        self.setWindowTitle("LabRAD Connections")
        self.parent = parent

        # make UI
        self.makeWidgets()
        self.connect()
        self.showMaximized()

    def makeWidgets(self):
        # create browser widget
        self.browserWidget = RegistryBrowserWidget(self.parent)

        # create editor widget
        self.editorWidget = RegistryEditorWidget(self.parent)

        # create splitter
        splitter_widget = QSplitter()
        splitter_widget.setOrientation(Qt.Vertical)
        splitter_widget.addWidget(QCustomGroupBox(self.browserWidget, "Browser"))
        splitter_widget.addWidget(QCustomGroupBox(self.editorWidget, "Editor"))
        splitter_widget.setStretchFactor(0, 6)
        splitter_widget.setStretchFactor(1, 2)

        # create title widget
        title_widget = QLabel('LabRAD Registry')
        title_widget.setFont(QFont('MS Shell Dlg 2', pointSize=20))
        title_widget.setAlignment(Qt.AlignCenter)

        # create layout
        layout = QVBoxLayout(self)
        layout.addWidget(title_widget,      stretch=1)
        layout.addWidget(splitter_widget,   stretch=20)

    def connect(self):
        self.browserWidget.makeKey.connect(lambda _dirlist: self.editorWidget.makeKey(_dirlist))
        self.browserWidget.makeDirectory.connect(lambda _dirlist: self.editorWidget.makeDirectory(_dirlist))


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(RegistryBrowserWidget)
