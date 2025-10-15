from socket import gethostname
from os import environ, _exit, path
from twisted.internet.defer import inlineCallbacks

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QGridLayout, QApplication, QScrollArea

from EGGS_labrad.clients import QDetachableTabWidget


class EGGS_GUI(QMainWindow):
    """
    EGGS GUI

    The main labrad experimental interface for the EGGS experiment.
    """

    name = gethostname() + ' EGGS GUI'
    LABRADPASSWORD = environ['LABRADPASSWORD']

    def __init__(self, reactor, clipboard=None, parent=None):
        super(EGGS_GUI, self).__init__(parent)

        # setup pyqt elements
        self.clipboard = clipboard
        self.reactor = reactor
        self.cxn = None

        # configure GUI elements
        self.setWindowTitle(self.name)
        #self.setStyleSheet("background-color:black; color:white; border: 1px solid white")

        # set window icon
        path_root = environ['EGGS_LABRAD_ROOT']
        icon_path = path.join(path_root, 'eggs.png')
        self.setWindowIcon(QIcon(icon_path))

        # connect to labrad asynchronously
        d = self.connect()
        d.addCallback(self.makeLayout)

    @inlineCallbacks
    def connect(self):
        """
        Create an asynchronous labrad connection.
        """
        # get labrad connection parameters
        LABRADHOST =        environ['LABRADHOST']
        LABRADPASSWORD =    environ['LABRADPASSWORD']

        # create and return the async labrad cxn
        # note: need to return it since it'll be used to instantiate the GUIClients
        from labrad.wrappers import connectAsync
        self.cxn = yield connectAsync(LABRADHOST, name=self.name, password=LABRADPASSWORD)
        # todo: should this be a returnValue???
        return self.cxn


    def makeLayout(self, cxn):
        """
        Create and lay out EGGS GUI.
        Arguments:
            cxn: an asynchronous labrad connection object.
        """
        # central layout
        centralWidget = QWidget()
        layout = QHBoxLayout(centralWidget)
        self.tabWidget = QDetachableTabWidget()

        # create subwidgets - each will be a separate tab
        # script_scanner =    self.makeScriptScannerWidget(self.reactor, cxn)
        cryovac =           self.makeCryovacWidget(self.reactor, cxn)
        trap =              self.makeTrapWidget(self.reactor, cxn)
        lasers =            self.makeLaserWidget(self.reactor, cxn)
        wavemeter =         self.makeWavemeterWidget(self.reactor, cxn)

        # create tabs for each subwidget
        # self.tabWidget.addTab(script_scanner, '&Script Scanner')
        self.tabWidget.addTab(cryovac, '&Cryovac')
        self.tabWidget.addTab(trap, '&Trap')
        self.tabWidget.addTab(lasers, '&Lasers')
        self.tabWidget.addTab(wavemeter, '&Wavemeter')

        # put it all together
        layout.addWidget(self.tabWidget)
        self.setCentralWidget(centralWidget)


    """TAB WIDGETS"""
    # def makeScriptScannerWidget(self, reactor, cxn):
    #     from EGGS_labrad.clients.script_scanner_gui import script_scanner_gui
    #     # note: no need to initialize script_scanner_gui with a labrad cxn
    #     # since it creates its own
    #     scriptscanner = script_scanner_gui(reactor)
    #     return scriptscanner

    def makeCryovacWidget(self, reactor, cxn):
        # import constituent widgets
        from EGGS_labrad.clients.cryovac_clients.lakeshore336_client import lakeshore336_client
        from EGGS_labrad.clients.cryovac_clients.niops03_client import niops03_client
        from EGGS_labrad.clients.cryovac_clients.twistorr74_client import twistorr74_client
        from EGGS_labrad.clients.cryovac_clients.RGA_client import RGA_client

        # create client dict for programmatic initialization
        clients = {
            lakeshore336_client:    {"pos": (0, 0)},
            RGA_client:             {"pos": (0, 1)},
            twistorr74_client:      {"pos": (0, 2)},
            niops03_client:         {"pos": (1, 1)}
        }
        return self._createTabLayout(clients, reactor, cxn)

    def makeTrapWidget(self, reactor, cxn):
        # import constituent widgets
        from EGGS_labrad.clients.trap_clients.RF_client import RF_client
        from EGGS_labrad.clients.trap_clients.DC_client import DC_client
        from EGGS_labrad.clients.powersupply_client.gpp3060_client import gpp3060_client
        from EGGS_labrad.clients.PMT_client.PMT_client import PMT_client
        from EGGS_labrad.clients.ARTIQ_client.DDS_client import DDS_client
        from EGGS_labrad.clients.ionization_laser_shutter_client.ionization_laser_shutter_client import IonizationLasersShuttersClient as ion_client

        # create client dict for programmatic initialization
        clients = {
            DC_client:              {"pos": (0, 0, 2, 3)},
            DDS_client:             {"pos": (0, 3, 2, 2)},
            PMT_client:             {"pos": (2, 0, 1, 1)},
            ion_client:             {"pos": (2, 1, 1, 1)},
            RF_client:              {"pos": (2, 2, 1, 1)},
            gpp3060_client:         {"pos": (2, 3, 1, 1)},
        }

        return self._createTabLayout(clients, reactor, cxn)

    def makeLaserWidget(self, reactor, cxn):
        # import constituent widgets
        from EGGS_labrad.clients.SLS_client.SLS_client import SLS_client
        from EGGS_labrad.clients.toptica_client.toptica_client import toptica_client
        from EGGS_labrad.clients.injection_lock_diode_client.injection_lock_temperature_client import InjectionLockTemperatureClient
        from EGGS_labrad.clients.injection_lock_diode_client.injection_lock_current_client import InjectionLockCurrentClient

        # create client dict for programmatic initialization
        clients = {
            SLS_client:             {"pos": (0, 0, 2, 2)},
            toptica_client:         {"pos": (2, 0, 2, 2)},
            InjectionLockTemperatureClient: {"pos": (0, 2, 2, 2)},
            InjectionLockCurrentClient: {"pos": (2, 2, 2, 2)}
        }
        return self._createTabLayout(clients, reactor, cxn)

    def makeWavemeterWidget(self, reactor, cxn):
        # import constituent widgets
        from EGGS_labrad.clients.wavemeter_client.multiplexer_client import multiplexer_client

        # create client dict for programmatic initialization
        clients = {
            multiplexer_client:     {"pos": (0, 0)}
        }
        # note: no need to initialize multiplexer_client with a labrad cxn
        # since it creates its own - especially since it's on a different network
        return self._createTabLayout(clients, reactor)


    """HELPER FUNCTIONS"""

    def close(self):
        """
        Attempt to safely close the GUI (non-trivial).
        Disconnects the labrad connection and stops the event reactor.
        """
        # attempt to close the labrad connection
        try:
            self.cxn.disconnect()
        except Exception as e:
            print(e)

        # attempt to stop the event reactor
        try:
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
        # create a scrollable holder widget to organize each tab
        tab_area = QScrollArea()
        holder_widget = QWidget()
        holder_layout = QGridLayout(holder_widget)

        # instantiate each sub-client and add them to the tab
        for client, config in clientDict.items():

            # get configuration settings for each client
            position =  config["pos"]
            args =      config.get("args", ())
            kwargs =    config.get("kwargs", {})

            # start up client
            try:
                client_tmp = client(reactor, cxn=cxn, *args, **kwargs)
            except Exception as e:
                print(client, repr(e))

            # try to add the sub-client's GUI object to the tab holder
            try:
                # retrieve GUI for GUIClient classes
                if hasattr(client_tmp, 'getgui'):
                    holder_layout.addWidget(client_tmp.getgui(), *position)
                    print(client)
                # otherwise, hope the client has some attribute called "gui"
                elif hasattr(client_tmp, 'gui'):
                    holder_layout.addWidget(client_tmp.gui, *position)

            except Exception as e:
                print(e)

        # set up QScrollArea to allow scrolling
        tab_area.setWidget(holder_widget)
        tab_area.setWidgetResizable(True)
        return tab_area


if __name__ == "__main__":
    # set up QApplication
    app = QApplication([])
    try:
        import qt5reactor
        qt5reactor.install()
    except Exception as e:
        print(repr(e))

    # instantiate client with a reactor
    from twisted.internet import reactor
    client_tmp = EGGS_GUI(reactor)

    # show gui and start reactor
    client_tmp.showMaximized()
    reactor.callWhenRunning(app.exec)
    reactor.addSystemEventTrigger('after', 'shutdown', client_tmp.close)
    reactor.runReturn()

    # close client on exit
    try:
        client_tmp.close()
    except Exception as e:
        print(repr(e))
