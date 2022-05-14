import numpy as np
import pyqtgraph as pg

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QGridLayout, QGroupBox, QDoubleSpinBox, QPushButton, QTabWidget

from EGGS_labrad.clients.Widgets import TextChangingButton

_SHELL_FONT = 'MS Shell Dlg 2'


class stability_gui(QFrame):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(400, 600)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("Stability Client")

    def _makeParametersTab(self):
        """
        This tab displays the trap parameters and the resultant secular frequencies.
        This is independent of ion number.
        """
        # parameter box
        parameters = QWidget('Parameters')
        parameters_layout = QGridLayout(parameters)
        # title
        self.all_label = QLabel('Stability Client')
        self.all_label.setFont(QFont(_SHELL_FONT, pointSize=18))
        self.all_label.setAlignment(Qt.AlignCenter)
        # readout
        pickoff_display_label = QLabel('VPP (V)')
        self.pickoff_display = QLabel('000.00')
        # record button
        self.record_button = TextChangingButton(('Stop Recording', 'Start Recording'))
        self.record_button.setMaximumHeight(25)
        # a parameter
        aparam_display_label = QLabel('a-parameter')
        self.aparam_display = QLabel('0.0000')
        # q parameter
        qparam_display_label = QLabel('q-parameter')
        self.qparam_display = QLabel('0.000')
        # wsecr - radial
        wsecr_display_label = QLabel('\u03C9 Radial (x2\u03C0 MHz)')
        self.wsecr_display = QLabel('0.000')
        # wsecz - radial
        wsecz_display_label = QLabel('\u03C9 Axial (x2\u03C0 MHz)')
        self.wsecz_display = QLabel('0.000')

        # configure display elements
        for display in (self.pickoff_display, self.aparam_display, self.qparam_display, self.wsecr_display, self.wsecz_display):
            display.setFont(QFont(_SHELL_FONT, pointSize=22))
            display.setAlignment(Qt.AlignRight)
            display.setStyleSheet('color: blue')
        for display_label in (pickoff_display_label, aparam_display_label, qparam_display_label,
                              wsecr_display_label, wsecz_display_label):
            display_label.setAlignment(Qt.AlignRight)
        # layout parameter box elements
        parameters_layout.addWidget(pickoff_display_label,        1, 0, 1, 1)
        parameters_layout.addWidget(self.pickoff_display,         2, 0, 1, 1)
        parameters_layout.addWidget(aparam_display_label,         1, 1, 1, 1)
        parameters_layout.addWidget(self.aparam_display,          2, 1, 1, 1)
        parameters_layout.addWidget(qparam_display_label,         1, 2, 1, 1)
        parameters_layout.addWidget(self.qparam_display,          2, 2, 1, 1)
        parameters_layout.addWidget(wsecr_display_label,          3, 1, 1, 1)
        parameters_layout.addWidget(self.wsecr_display,           4, 1, 1, 1)
        parameters_layout.addWidget(wsecz_display_label,          3, 2, 1, 1)
        parameters_layout.addWidget(self.wsecz_display,           4, 2, 1, 1)
        parameters_layout.addWidget(self.record_button,           4, 0, 1, 1)

    def _makeIonTab(self):
        """
        This tab allows configuration of ion chain data to retrieve
        mode values (i.e. eigenvector components and mode frequencies).
        """
        pass


    def _makeTrapTab(self):
        """
        This tab allows configuration of trap parameters.
        """
        pass

    def _makeStabilityDisplayTab(self):
        """
        This tab draws the stability plot display.
        """
        self.qBox_stability = QGroupBox('Mathieu Stability')
        qBox_stability_display = QGridLayout(self.qBox_stability)
        pg.setConfigOption('background', 'k')
        self.stability_display = pg.PlotWidget(name='Mathieu Stability Display', border=True)
        self.stability_display.showGrid(x=True, y=True, alpha=0.5)
        self.stability_display.setRange(xRange=[0, 1], yRange=[0, 0.1])
        self.stability_display.setLimits(xMin=-0.1, xMax=1, yMin=-0.1, yMax=0.1)
        self.stability_display.setMaximumSize(400, 400)
        self.stability_display.setMinimumSize(300, 300)
        self.stability_display.setLabel('left', 'a')
        self.stability_display.setLabel('bottom', 'q')
        self.stability_point = self.stability_display.plot(symbol='o', symbolBrush=QColor(Qt.white))
        xarr = np.linspace(0, 1, 100)
        yarr = 0.5 * np.power(xarr, 2)
        self.stability_region = self.stability_display.plot(symbol=None, pen=QColor(Qt.red))
        self.stability_region2 = self.stability_display.plot(xarr, yarr, symbol=None, pen=QColor(Qt.red))
        # beta setting
        beta_setting_display = QLabel('\u03B2')
        beta_setting_display.setAlignment(Qt.AlignRight)
        self.beta_setting = QDoubleSpinBox()
        self.beta_setting.setFont(QFont('MS Shell Dlg 2', pointSize=14))
        self.beta_setting.setDecimals(1)
        self.beta_setting.setSingleStep(0.1)
        self.beta_setting.setRange(0, 1)
        self.beta_setting.setKeyboardTracking(False)
        self.beta_setting.setAlignment(Qt.AlignRight)
        # autoscale button
        self.autoscale = QPushButton("Autoscale")
        # lay out
        qBox_stability_display.addWidget(beta_setting_display, 0, 0, 1, 1)
        qBox_stability_display.addWidget(self.beta_setting, 1, 0, 1, 1)
        qBox_stability_display.addWidget(self.autoscale, 1, 1, 1, 1)
        qBox_stability_display.addWidget(self.stability_display, 2, 0, 3, 3)

    def _makeEigenTab(self):
        """
        This
        """
        pass

    def makeWidgets(self):
        # create tabwidget to store the Parameters and Chain tabs
        self.configBox = QTabWidget()
        self.displayBox = QTabWidget()
        # todo: create widgets from helper functions

    def makeLayout(self):
        layout = QGridLayout(self)
        layout.addWidget(self.all_label,                    0, 0, 1, 4)
        layout.addWidget(parameters,              1, 0, 2, 4)
        layout.addWidget(self.qBox_stability,               4, 0, 3, 4)

    def drawStability(self, beta=0.4):
        xarr = np.linspace(0, 1, 100)
        yarr = np.power(beta, 2) - 0.5 * np.power(xarr, 2)
        self.stability_region.setData(xarr, yarr)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(stability_gui)