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
        self.record_button = TextChangingButton(("Stop Recording", "Start Recording"))
        self.save_button = QPushButton("Save")

        # display
        qBox_intTrace = QGroupBox('Interferometer')
        qBox_intTrace_layout = QGridLayout(qBox_intTrace)
        pg.setConfigOption('background', 'w')

        # configure pyqtgraph
        pg.setConfigOption('antialias', False)
        from importlib.util import find_spec
        if find_spec('OpenGL'):
            pg.setConfigOption('useOpenGL', True)
            pg.setConfigOption('enableExperimental', True)

        # configure interferometer display
        self.trace_display = pg.PlotWidget(name='Fiber Noise Trace Trace', border=True)
        self.trace_display.showGrid(x=True, y=True, alpha=0.5)
        self.trace_display.setLimits(xMin=0, xMax=2000, yMin=0, yMax=3e8)
        self.trace_display.setMinimumHeight(400)
        self.trace_display.setMaximumWidth(1000)
        self.trace_display_legend = self.trace_display.addLegend(size=(200, 200))
        qBox_intTrace_layout.addWidget(self.trace_display)

        # final layout
        layout.addWidget(title,                                                         0, 0, 1, 2)
        layout.addWidget(QCustomGroupBox(self.trace_display, "Fiber Noise Trace"),      1, 0, 4, 1)
        layout.addWidget(qBox_intTrace, 1, 1, 3, 1)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(fibernoise_gui)
