from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QTabWidget
from PyQt5.QtGui import QIcon
from twisted.internet.defer import inlineCallbacks, returnValue
from barium.lib.clients.gui.detachable_tab import DetachableTabWidget

class EGGS_GUI(QMainWindow):
    def __init__(self, reactor, clipboard, parent=None):
        super(EGGS_GUI, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect()
        self.makeLayout(self.cxn)

    @inlineCallbacks
    def connect(self):
        from common.lib.clients.connection import connection
        self.cxn = connection(name = 'EGGS GUI Client')
        yield self.cxn.connect()

    #Highest level adds tabs to big GUI
    def makeLayout(self, cxn):
	    #creates central layout
        centralWidget = QWidget()
        layout = QHBoxLayout()

	    #create subwidgets to be added to tabs
        script_scanner = self.makeScriptScannerWidget(reactor, cxn)
        cryo = self.makeCryoWidget(reactor)

        # add tabs
        self.tabWidget = QTabWidget()
        #self.tabWidget = DetachableTabWidget()
        self.tabWidget.addTab(script_scanner, '&Script Scanner')
        self.tabWidget.addTab(cryo, '&Cryo')

        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle('Barium GUI')

#################### Here we will connect to individual clients and add sub-tabs #####################

######sub tab layout example#############
#    def makeLaserSubTab(self, reactor, cxn):
#        centralWidget = QtGui.QWidget()
#        layout = QtGui.QHBoxLayout()

#	wavemeter = self.makeWavemeterWidget(reactor, cxn)
#	M2 = self.makeM2Widget(reactor, cxn)
#	M2pump = self.makeM2PumpWidget(reactor, cxn)
#
#	subtabWidget = QtGui.QTabWidget()
#
#	subtabWidget.addTab(wavemeter, '&Wavemeter')
#	subtabWidget.addTab(M2, '&M2')
#	subtabWidget.addTab(M2pump, '&PumpM2')
#
#       self.setCentralWidget(centralWidget)
#        self.setWindowTitle('Lasers')
#	return subtabWidget

######create widgets with shared connection######


    def makeScriptScannerWidget(self, reactor, cxn):
        from EGGS_labrad.lib.clients.script_scanner_gui.script_scanner_gui import script_scanner_gui
        scriptscanner = script_scanner_gui(reactor, cxn = cxn)
        return scriptscanner

    def makeCryoWidget(self, reactor):
        from EGGS_labrad.lib.clients.lakeshore_client.lakeshore_client import lakeshore_client
        lakeshore = lakeshore_client(reactor)
        return lakeshore

    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    import sys, qt5reactor
    a = QApplication(sys.argv)
    clipboard = a.clipboard()
    qt5reactor.install()
    from twisted.internet import reactor
    EGGSGUI = EGGS_GUI(reactor, clipboard)
    #EGGSGUI.setWindowIcon(QIcon('C:/Users/barium133/Code/barium/BARIUM_IONS.png'))
    EGGSGUI.setWindowTitle('EGGS GUI')
    EGGSGUI.show()
    reactor.run()
