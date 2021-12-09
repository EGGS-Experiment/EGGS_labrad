#imports
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QListWidget, QListWidgetItem, QMenu

from FitWindowWidget import FitWindow
from ParameterListWidget import ParameterList
from DataVaultListWidget import DataVaultList
from PredictSpectrumWidget import PredictSpectrum

from GUIConfig import traceListConfig

class TraceList(QListWidget):
    """
    Manages the datasets that are being plotted.
    Basically the left-hand column of each GraphWidget.
    """

    def __init__(self, parent, root=None):
        super(TraceList, self).__init__()
        self.parent = parent
        self.root = root
        self.windows = []
        self.config = traceListConfig()
        self.setStyleSheet("background-color:%s;" % self.config.background_color)
        try:
            self.use_trace_color = self.config.use_trace_color
        except AttributeError:
            self.use_trace_color = False

        self.name = 'pmt'
        self.initUI()

    def initUI(self):
        self.trace_dict = {}
        item = QListWidgetItem('Traces')
        item.setCheckState(Qt.Checked)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.popupMenu)


    def addTrace(self, ident, color):
        item = QListWidgetItem(ident)

        if self.use_trace_color:
            foreground_color = self.parent.getItemColor(color)
            item.setForeground(foreground_color)
        else:
            item.setForeground(QColor(255, 255, 255))
        item.setBackground(QColor(0, 0, 0))

        item.setCheckState(Qt.Checked)
        self.addItem(item)
        self.trace_dict[ident] = item

    def removeTrace(self, ident):
        item = self.trace_dict[ident]
        row = self.row(item)
        self.takeItem(row)
        item = None

    def changeTraceListColor(self, ident, new_color):
        item = self.trace_dict[ident]
        item.setForeground(self.parent.getItemColor(new_color))

    def popupMenu(self, pos):
        menu = QMenu()
        item = self.itemAt(pos)
        if (item == None): 
            dataaddAction = menu.addAction('Add Data Set')
            spectrumaddAction = menu.addAction('Add Predicted Spectrum')

            action = menu.exec_(self.mapToGlobal(pos))
            if action == dataaddAction:
                dvlist = DataVaultList(self.parent.name, root=self.root)
                self.windows.append(dvlist)
                dvlist.show()

            if action == spectrumaddAction:
                ps = PredictSpectrum(self)
                self.windows.append(ps)
                ps.show()



        else:
            ident = str(item.text())
            parametersAction = menu.addAction('Parameters')
            togglecolorsAction = menu.addAction('Toggle colors')
            fitAction = menu.addAction('Fit')
            selectColorMenu = menu.addMenu("Select color")
            redAction = selectColorMenu.addAction("Red")
            greenAction = selectColorMenu.addAction("Green")
            yellowAction = selectColorMenu.addAction("Yellow")
            cyanAction = selectColorMenu.addAction("Cyan")
            magentaAction = selectColorMenu.addAction("Magenta")
            whiteAction = selectColorMenu.addAction("White")
            colorActionDict = {redAction:"r", greenAction:"g", yellowAction:"y", cyanAction:"c", magentaAction:"m", whiteAction:"w"}

            action = menu.exec_(self.mapToGlobal(pos))
            
            if action == parametersAction:
                # option to show parameters in separate window
                dataset = self.parent.artists[ident].dataset
                pl = ParameterList(dataset)
                self.windows.append(pl)
                pl.show()

            if action == togglecolorsAction:               
                # option to change color of line
                new_color = self.parent.colorChooser.next()
                #self.parent.artists[ident].artist.setData(color = new_color, symbolBrush = new_color)
                self.parent.artists[ident].artist.setPen(new_color)
                if self.parent.show_points:
                    self.parent.artists[ident].artist.setData(pen = new_color, symbolBrush = new_color)
                    self.changeTraceListColor(ident, new_color)
                else:
                    self.parent.artists[ident].artist.setData(pen = new_color)
                    self.changeTraceListColor(ident, new_color)

            if action == fitAction:
                dataset = self.parent.artists[ident].dataset
                index = self.parent.artists[ident].index
                fw = FitWindow(dataset, index, self)
                self.windows.append(fw)
                fw.show()

            if action in colorActionDict.keys():
                new_color = colorActionDict[action]
                self.parent.artists[ident].artist.setPen(new_color)
                if self.parent.show_points:
                    self.parent.artists[ident].artist.setData(pen = new_color, symbolBrush = new_color)
                    self.changeTraceListColor(ident, new_color)
                else:
                    self.parent.artists[ident].artist.setData(pen = new_color)
                    self.changeTraceListColor(ident, new_color)
