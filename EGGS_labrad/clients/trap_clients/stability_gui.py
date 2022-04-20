import pyqtgraph as pg

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QGridLayout, QGroupBox

from EGGS_labrad.clients.Widgets import TextChangingButton


class stability_gui(QFrame):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(550, 900)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("Stability Client")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        # title
        self.all_label = QLabel('Stability Client')
        self.all_label.setFont(QFont(shell_font, pointSize=18))
        self.all_label.setAlignment(Qt.AlignCenter)
        # todo: put in qgroupbox
        # readout
        self.pickoff_display_label = QLabel('VPP (V)')
        self.pickoff_display = QLabel('000.000')
        self.pickoff_display.setFont(QFont(shell_font, pointSize=22))
        self.pickoff_display.setAlignment(Qt.AlignRight)
        self.pickoff_display.setStyleSheet('color: blue')
        # record button
        self.record_button = TextChangingButton(('Stop Recording', 'Start Recording'))
        self.record_button.setMaximumHeight(25)
        # a parameter
        self.aparam_display_label = QLabel('a-parameter')
        self.aparam_display = QLabel('0.0000')
        self.aparam_display.setFont(QFont(shell_font, pointSize=22))
        self.aparam_display.setAlignment(Qt.AlignRight)
        self.aparam_display.setStyleSheet('color: blue')
        # q parameter
        self.qparam_display_label = QLabel('q-parameter')
        self.qparam_display = QLabel('0.0000')
        self.qparam_display.setFont(QFont(shell_font, pointSize=22))
        self.qparam_display.setAlignment(Qt.AlignRight)
        self.qparam_display.setStyleSheet('color: blue')
        # wsec
        self.wsec_display_label = QLabel('Secular Frequency (x2pi MHz)')
        self.wsec_display = QLabel('000.000')
        self.wsec_display.setFont(QFont(shell_font, pointSize=22))
        self.wsec_display.setAlignment(Qt.AlignRight)
        self.wsec_display.setStyleSheet('color: blue')
        # stability plot display
        self.qBox_stability = QGroupBox('Mathieu Stability')
        qBox_stability_display = QGridLayout(self.qBox_stability)
        pg.setConfigOption('background', 'k')
        self.stability_display = pg.PlotWidget(name='Mathieu Stability Display', border=True)
        self.stability_display.showGrid(x=True, y=True, alpha=0.5)
        self.stability_display.setRange(xRange=[0, 1], yRange=[0, 1])
        self.stability_display.setMinimumHeight(400)
        self.stability_display.setMinimumWidth(400)
        self.stability_display.setMaximumWidth(500)
        self.stability_point = self.stability_display.plot(pen=pg.mkPen(color='r'), symbol='o')
        # todo: set width/size of pen
        # todo: draw mathieu stability
        # todo: prevent resizing of trace
        qBox_stability_display.addWidget(self.stability_display)
        # todo: open dialog box to change values

    def makeLayout(self):
        layout = QGridLayout(self)
        layout.addWidget(self.all_label,                    0, 0, 1, 4)
        layout.addWidget(self.pickoff_display_label,        1, 0, 1, 1)
        layout.addWidget(self.pickoff_display,              2, 0, 1, 1)
        layout.addWidget(self.aparam_display_label,         1, 1, 1, 1)
        layout.addWidget(self.aparam_display,               2, 1, 1, 1)
        layout.addWidget(self.qparam_display_label,         1, 2, 1, 1)
        layout.addWidget(self.qparam_display,               2, 2, 1, 1)
        layout.addWidget(self.wsec_display_label,           1, 3, 1, 1)
        layout.addWidget(self.wsec_display,                 2, 3, 1, 1)
        layout.addWidget(self.qBox_stability,               3, 0, 4, 4)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(stability_gui)
