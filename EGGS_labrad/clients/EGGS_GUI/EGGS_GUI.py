from socket import gethostname
from os import environ, _exit, path
from twisted.internet.defer import inlineCallbacks

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QGridLayout, QApplication

from EGGS_labrad.clients import QDetachableTabWidget


class EGGS_gui(QMainWindow):

    name = gethostname() + ' EGGS GUI'
    LABRADPASSWORD = environ['LABRADPASSWORD']

    def __init__(self, reactor, clipboard=None, parent=None):
        super(EGGS_gui, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.cxn = None
        self.setWindowTitle(self.name)
        #self.setStyleSheet("background-color:black; color:white; border: 1px solid white")
        # set window icon
        path_root = environ['EGGS_LABRAD_ROOT']
        icon_path = path.join(path_root, 'eggs.png')
        self.setWindowIcon(QIcon(icon_path))
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
        #self.tabWidget.setMovable(True)
        # create subwidgets
        # use connection class for scriptscanner only
        script_scanner = self.makeScriptScannerWidget(self.reactor, cxn)
        cryovac = self.makeCryovacWidget(self.reactor, cxn)
        trap = self.makeTrapWidget(self.reactor, cxn)
        lasers = self.makeLaserWidget(self.reactor, cxn)
        wavemeter = self.makeWavemeterWidget(self.reactor, cxn)
        imaging = self.makeImagingWidget(self.reactor, cxn)
        # create tabs for each subwidget
        self.tabWidget.addTab(script_scanner, '&Script Scanner')
        self.tabWidget.addTab(cryovac, '&Cryovac')
        self.tabWidget.addTab(trap, '&Trap')
        self.tabWidget.addTab(lasers, '&Lasers')
        self.tabWidget.addTab(wavemeter, '&Wavemeter')
        self.tabWidget.addTab(imaging, '&Imaging')
        # put it all together
        layout.addWidget(self.tabWidget)
        self.setCentralWidget(centralWidget)

    def makeScriptScannerWidget(self, reactor, cxn):
        from EGGS_labrad.clients.script_scanner_gui import script_scanner_gui
        scriptscanner = script_scanner_gui(reactor)
        return scriptscanner

    def makeCryovacWidget(self, reactor, cxn):
        # import constituent widgets
        from EGGS_labrad.clients.cryovac_clients.lakeshore336_client import lakeshore336_client
        from EGGS_labrad.clients.cryovac_clients.niops03_client import niops03_client
        from EGGS_labrad.clients.cryovac_clients.twistorr74_client import twistorr74_client
        from EGGS_labrad.clients.cryovac_clients.RGA_client import RGA_client
        from EGGS_labrad.clients.cryovac_clients.fma1700a_client import fma1700a_client
        #from EGGS_labrad.clients.cryovac_clients.f70_client import f70_client
        clients = {
            lakeshore336_client:            {"pos": (0, 0)},
            RGA_client:                     {"pos": (0, 1)},
            twistorr74_client:              {"pos": (0, 2)},
            niops03_client:                 {"pos": (1, 1)},
            fma1700a_client:                {"pos": (1, 2)}
        }
        return self._createTabLayout(clients, reactor, cxn)

    def makeTrapWidget(self, reactor, cxn):
        from EGGS_labrad.clients.trap_clients.RF_client import RF_client
        from EGGS_labrad.clients.trap_clients.DC_client import DC_client
        from EGGS_labrad.clients.stability_client.stability_client import stability_client
        from EGGS_labrad.clients.functiongenerator_client.functiongenerator_client import functiongenerator_client
        clients = {
            DC_client:                      {"pos": (0, 1, 1, 2)},
            stability_client:               {"pos": (0, 0, 2, 1)},
            functiongenerator_client:       {"pos": (1, 2)},
            RF_client:                      {"pos": (1, 1)}
        }
        return self._createTabLayout(clients, reactor, cxn)

    def makeLaserWidget(self, reactor, cxn):
        from EGGS_labrad.clients.SLS_client.SLS_client import SLS_client
        from EGGS_labrad.clients.toptica_client.toptica_client import toptica_client
        #from EGGS_labrad.clients.shutter_client import shutter_client
        clients = {
            SLS_client:                     {"pos": (0, 0)},
            toptica_client:                 {"pos": (0, 1)}
        }
        return self._createTabLayout(clients, reactor, cxn)

    def makeWavemeterWidget(self, reactor, cxn):
        from EGGS_labrad.clients.wavemeter_client.multiplexer_client import multiplexer_client
        clients = {
            multiplexer_client:             {"pos": (0, 0)}
        }
        return self._createTabLayout(clients, reactor)

    def makeImagingWidget(self, reactor, cxn):
        from EGGS_labrad.clients.PMT_client.PMT_client import PMT_client
        from EGGS_labrad.clients.slider_client.slider_client import slider_client
        clients = {
            PMT_client:                     {"pos": (0, 0)},
            slider_client:                  {"pos": (0, 1)}
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
    client_tmp = EGGS_gui(reactor)
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
