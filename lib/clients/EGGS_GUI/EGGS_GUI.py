from PyQt4 import QtGui
from twisted.internet.defer import inlineCallbacks, returnValue
import sys
from barium.lib.clients.gui.detachable_tab import DetachableTabWidget

class BARIUM_GUI(QtGui.QMainWindow):
    def __init__(self, reactor, clipboard, parent=None):
        super(BARIUM_GUI, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect_labrad()

    @inlineCallbacks
    def connect_labrad(self):
        from common.lib.clients.connection import connection
        cxn = connection(name = 'Barium GUI Client')
        yield cxn.connect()
        self.create_layout(cxn)

    #Highest level adds tabs to big GUI
    def create_layout(self, cxn):
	    #creates central layout
        centralWidget = QtGui.QWidget()
        layout = QtGui.QHBoxLayout()

	    #create subwidgets to be added to tabs
        script_scanner = self.makeScriptScannerWidget(reactor, cxn)
        wavemeter = self.makeWavemeterWidget(reactor)
        laser_control = self.makeLaserControlWidget(reactor)
        control = self.makeControlWidget(reactor)
        frequency = self.makeFrequencyWidget(reactor)
        switch = self.makePMTCameraSwitchWidget(reactor)

        # add tabs
        self.tabWidget = QtGui.QTabWidget()
        #self.tabWidget = DetachableTabWidget()
        self.tabWidget.addTab(laser_control, '&Laser Control')
        self.tabWidget.addTab(wavemeter, '&Wavemeter')
        self.tabWidget.addTab(control, '&Trap Control')
        self.tabWidget.addTab(frequency, '&Oscillators')
        self.tabWidget.addTab(script_scanner, '&Script Scanner')
        self.tabWidget.addTab(switch, '&Switches')

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
        from common.lib.clients.script_scanner_gui.script_scanner_gui import script_scanner_gui
        scriptscanner = script_scanner_gui(reactor, cxn = cxn)
        return scriptscanner

    def makeWavemeterWidget(self, reactor):
        from common.lib.clients.Multiplexer.multiplexerclient import wavemeterclient
        wavemeter = wavemeterclient(reactor)
        return wavemeter

    def makeLaserControlWidget(self, reactor):
        from barium.lib.clients.Software_Laser_Lock_Client.laser_control_client import laser_control_client
        control = laser_control_client(reactor)
        return control

    def makeControlWidget(self, reactor):
        from barium.lib.clients.TrapControl_client.TrapControl_client import TrapControlClient
        control = TrapControlClient(reactor)
        return control

    def makeFrequencyWidget(self,reactor):
        from barium.lib.clients.FrequencyControl_client.FrequencyControl_client import FrequencyControlClient
        frequency = FrequencyControlClient(reactor)
        return frequency

    def makePMTCameraSwitchWidget(self,reactor):
        from barium.lib.clients.PMTCameraSwitch_client.PMTCameraSwitch_client import PMTCameraSwitchClient
        switch = PMTCameraSwitchClient(reactor)
        return switch

    def closeEvent(self, x):
        self.reactor.stop()

if __name__=="__main__":
    a = QtGui.QApplication( sys.argv )
    clipboard = a.clipboard()
    import qt4reactor
    qt4reactor.install()
    from twisted.internet import reactor
    BariumGUI = BARIUM_GUI(reactor, clipboard)
    BariumGUI.setWindowIcon(QtGui.QIcon('C:/Users/barium133/Code/barium/BARIUM_IONS.png'))
    BariumGUI.setWindowTitle('Barium GUI')
    BariumGUI.show()
    reactor.run()
