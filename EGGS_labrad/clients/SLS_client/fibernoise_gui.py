import pyqtgraph as pg

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout, QPushButton

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox

class fibernoise_gui(QFrame):
    def __init__(self, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Fiber Noise Client")
        self.makeWidgets()

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        layout = QGridLayout(self)

        # title
        title = QLabel('Fiber Noise Client')
        title.setFont(QFont(shell_font, pointSize=16))
        title.setAlignment(Qt.AlignCenter)

        # buttons
        self.trace_button = QPushButton("Get Trace")
        self.save_button = QPushButton("Save")

        # configure pyqtgraph
        pg.setConfigOption('antialias', False)
        pg.setConfigOption('background', 'k')

        # configure interferometer display
        self.trace_display = pg.PlotWidget(name='Fiber Noise Trace', border=True)
        self.trace_display.showGrid(x=True, y=True, alpha=0.5)
        self.trace_display.setLimits(xMin=0, xMax=200, yMin=-1, yMax=1)
        self.trace_display.setMinimumHeight(400)
        self.trace_display.setMaximumWidth(1000)

        # final layout
        layout.addWidget(title,                                                         0, 0, 1, 2)
        layout.addWidget(QCustomGroupBox(self.trace_display, "Fiber Noise Trace"),      1, 0, 3, 2)
        layout.addWidget(self.trace_button,                                             4, 0, 1, 1)
        layout.addWidget(self.save_button,                                              4, 1, 1, 1)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(fibernoise_gui)
