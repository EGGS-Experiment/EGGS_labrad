import os

from twisted.internet.defer import inlineCallbacks

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTabWidget, QGridLayout


class EGGS_gui(QMainWindow):

    name = 'EGGS GUI'
    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, clipboard=None, parent=None):
        super(EGGS_gui, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.connect()
        self.makeLayout(self.cxn)
        self.setWindowIcon(QIcon('/eggs.png'))
        self.setWindowTitle('EGGS GUI')

    @inlineCallbacks
    def connect(self):
        from EGGS_labrad.lib.clients.connection import connection
        self.cxn = connection(name=self.name)
        yield self.cxn.connect()
        print('cxn ok')
        ss = yield self.cxn.get_server('Script Scanner')
        thde=ss.get_queue()
        print(thde)
        try:
            yield self.getDeviceParams()
        except:
            print('ok')

    @inlineCallbacks
    def getDeviceParams(self):
        # print('gdp s')
        rf = yield self.cxn.get_server('RF Server')
        try:
            freq = yield rf.frequency()
            self.gui.wav_freq.setValue(freq / 1000)
            ampl = yield rf.amplitude()
            self.gui.wav_ampl.setValue(ampl)
            mod_freq = yield rf.modulation_frequency()
            self.gui.mod_freq.setValue(mod_freq / 1000)
            fm_dev = yield rf.fm_deviation()
            self.gui.mod_freq_dev.setValue(fm_dev / 1000)
            am_depth = yield rf.am_depth()
            self.gui.mod_ampl_depth.setValue(am_depth)
            pm_dev = yield rf.pm_deviation()
            self.gui.mod_phase_dev.setValue(pm_dev)
        except Exception as e:
            print(e)
        # print('gdp e')

    def makeLayout(self, cxn):
        print('ml s')
        #central layout
        centralWidget = QWidget()
        layout = QHBoxLayout()
        self.tabWidget = QTabWidget()

        #create subwidgets
        script_scanner = self.makeScriptScannerWidget(self.reactor, cxn)
        cryovac = self.makeCryovacWidget(self.reactor, self.cxn)
        trap = self.makeTrapWidget(self.reactor)

        #create tabs for each subwidget
        self.tabWidget.addTab(script_scanner, '&Script Scanner')
        # self.tabWidget.addTab(cryovac, '&Cryovac')
        # self.tabWidget.addTab(trap, '&Trap')

        #put it all together
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeScriptScannerWidget(self, reactor, cxn):
        from EGGS_labrad.lib.clients.script_scanner_gui import script_scanner_gui
        scriptscanner = script_scanner_gui(reactor, cxn=cxn)
        return scriptscanner

    def makeCryovacWidget(self, reactor, cxn):
        print('s1')
        from EGGS_labrad.lib.clients.cryovac_clients.lakeshore336_client import lakeshore336_client
        from EGGS_labrad.lib.clients.cryovac_clients.niops03_client import niops03_client
        from EGGS_labrad.lib.clients.cryovac_clients.twistorr74_client import twistorr74_client
        print('th1')
        lakeshore = lakeshore336_client(reactor, cxn=cxn.cxn)
        print('th2')
        niops = niops03_client(reactor, cxn=cxn.cxn)
        print('th3')
        twistorr = twistorr74_client(reactor, cxn=cxn.cxn)
        print('th4')

        #main layout
        holder_widget = QWidget()
        holder_layout = QGridLayout()
        holder_widget.setLayout(holder_layout)
        holder_layout.addWidget(lakeshore, 0, 0, 2, 2)
        holder_layout.addWidget(niops, 0, 1, 1, 1)
        holder_layout.addWidget(twistorr, 1, 1, 1, 1)
        # holder_layout.addWidget(lakeshore, 0, 0, 2, 2)
        # holder_layout.addWidget(niops, 0, 2, 1, 1)
        # holder_layout.addWidget(twistorr, 1, 2, 1, 1)
        # holder_layout.setColumnStretch(0, 1)
        # holder_layout.setColumnStretch(1, 1)
        # holder_layout.setColumnStretch(2, 1)
        # holder_layout.setRowStretch(0, 1)
        # holder_layout.setRowStretch(1, 1)
        # holder_layout.setRowStretch(2, 1)
        #todo: try size policy
        return holder_widget

    def makeTrapWidget(self, reactor):
        from EGGS_labrad.lib.clients.trap_clients.rf_client import rf_client
        rf_widget = rf_client(reactor)
        return rf_widget

    def closeEvent(self, event):
        self.cxn.disconnect()
        self.reactor.stop()


if __name__=="__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(EGGS_gui)
