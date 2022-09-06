from socket import gethostname
from twisted.internet.defer import inlineCallbacks
from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QListWidget, QScrollArea

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.labrad_client.connections_gui import ConnectionsGUI

class ConnectionsClient(GUIClient):
    """
    Data vault window used to select datasets for plotting.
    Creates a client connection to LabRAD to access the datavault and grapher servers.
    """

    def initializeGUI(self):
        mainLayout = QGridLayout(self)
        self.directoryString = ['Home']
        self.directoryTitle = QLabel('Directory:')
        self.directoryLabel = QLabel('\\'.join(self.directoryString))
        self.dataListWidget = QListWidget()
        self.dataListWidget.doubleClicked.connect(self.onDoubleclick)
        self.dataListWidgetScroll = QScrollArea()
        self.dataListWidgetScroll.setWidget(self.directoryLabel)
        self.dataListWidgetScroll.setWidgetResizable(True)
        self.dataListWidgetScroll.setFixedHeight(40)
        mainLayout.addWidget(self.directoryTitle)
        mainLayout.addWidget(self.dataListWidgetScroll)
        mainLayout.addWidget(self.dataListWidget)
        self.setWindowTitle('Data Vault')
        self.populate()

    @inlineCallbacks
    def populate(self):
        # remove old directories
        self.dataListWidget.clear()
        self.dataListWidget.addItem('...')
        # get new directory
        ls = yield self.dv.dir(context=self._context)
        self.dataListWidget.addItems(sorted(ls[0]))
        if ls[1] is not None:
            self.dataListWidget.addItems(sorted(ls[1]))

    @inlineCallbacks
    def onDoubleclick(self, item):
        item = self.dataListWidget.currentItem().text()
        # previous directory
        if item == '...':
            yield self.dv.cd(1, context=self._context)
            if len(self.directoryString) > 1:
                self.directoryString.pop()
                self.directoryLabel.setText('\\'.join(self.directoryString))
            self.populate()
        else:
            try:
                # next directory
                yield self.dv.cd(str(item), context=self._context)
                self.directoryString.append(str(item))
                self.directoryLabel.setText('\\'.join(self.directoryString))
                self.populate()
            except:
                # plot if no directories left
                path = yield self.dv.cd(context=self._context)
                if self.root is not None:
                    yield self.root.do_plot((path, str(item)), self.tracename, False)
                else:
                    yield self.grapher.plot((path, str(item)), self.tracename, False)
