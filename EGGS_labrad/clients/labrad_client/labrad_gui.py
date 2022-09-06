from socket import gethostname
from os import environ, _exit, path
from twisted.internet.defer import inlineCallbacks

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QGridLayout, QApplication

from EGGS_labrad.clients import QDetachableTabWidget


class labradGUI(QMainWindow):

    name = gethostname() + ' LabRAD GUI'
    LABRADPASSWORD = environ['LABRADPASSWORD']

    def __init__(self, reactor, clipboard=None, parent=None):
        super().__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.cxn = None
        self.setWindowTitle(self.name)
        #self.setStyleSheet("background-color:black; color:white; border: 1px solid white")
        # set window icon
        # path_root = environ['EGGS_LABRAD_ROOT']
        # icon_path = path.join(path_root, 'eggs.png')
        # self.setWindowIcon(QIcon(icon_path))
        # connect devices synchronously
        d = self.connect()
        d.addCallback(self.makeLayout)

    @inlineCallbacks
    def connect(self):
        LABRADHOST = environ['LABRADHOST']
        LABRADPASSWORD = environ['LABRADPASSWORD']
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(LABRADHOST, name=self.name, password=LABRADPASSWORD)
        return self.cxn

    def makeLayout(self, cxn):
        # central layout
        centralWidget = QWidget()
        layout = QHBoxLayout(centralWidget)
        self.tabWidget = QDetachableTabWidget()

        # create subwidgets
        connections = self.makeConnectionWidget(self.reactor, cxn)

        # create tabs for each subwidget
        self.tabWidget.addTab(connections, '&Connections')

        # put it all together
        layout.addWidget(self.tabWidget)
        self.setCentralWidget(centralWidget)

    def makeConnectionWidget(self, reactor, cxn):
        from EGGS_labrad.clients.labrad_client.connections_client import ConnectionsClient
        clients = {
            ConnectionsClient:              {"pos": (0, 0)}
            #niops03_client:                 {"pos": (1, 1)},
        }
        return self._createTabLayout(clients, reactor, cxn)

    def close(self):
        try:
            self.cxn.disconnect()
            if self.reactor.running:
                self.reactor.stop()
            _exit(0)
        except Exception as e:
            print(e)
            _exit(0)

    def _createTabLayout(self, clientDict, reactor, cxn=None):
        """
        Creates a tab widget from constituent widgets stored in a dictionary.
        """
        holder_widget = QWidget()
        holder_layout = QGridLayout(holder_widget)
        for client, config in clientDict.items():
            # get configuration settings for each client
            position = config["pos"]
            args, kwargs = ((), {})
            try:
                args = config["args"]
            except KeyError:
                pass
            try:
                kwargs = config["kwargs"]
            except KeyError:
                pass
            # start up client
            try:
                client_tmp = client(reactor, cxn=cxn, *args, **kwargs)
            except Exception as e:
                print(client, e)
            # try to add GUI to tabwidget
            try:
                if hasattr(client_tmp, 'getgui'):
                    holder_layout.addWidget(client_tmp.getgui(), *position)
                elif hasattr(client_tmp, 'gui'):
                    holder_layout.addWidget(client_tmp.gui, *position)
            except Exception as e:
                print(e)
        return holder_widget


if __name__ == "__main__":
    # set up QApplication
    app = QApplication([])
    try:
        import qt5reactor
        qt5reactor.install()
    except Exception as e:
        print(e)
    # instantiate client with a reactor
    from twisted.internet import reactor
    client_tmp = labradGUI(reactor)
    # show gui
    client_tmp.showMaximized()
    # start reactor
    reactor.callWhenRunning(app.exec)
    reactor.addSystemEventTrigger('after', 'shutdown', client_tmp.close)
    reactor.runReturn()
    # close client on exit
    try:
        client_tmp.close()
    except Exception as e:
        print(e)
