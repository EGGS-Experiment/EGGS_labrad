import numpy as np
import pyqtgraph as pg

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QGridLayout, QGroupBox, QDoubleSpinBox, QPushButton, QTabWidget, QComboBox

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

    def _makeStabilityTab(self):
        """
        This tab displays the trap parameters and the resultant secular frequencies.
        This is independent of ion number.
        Part of the Parameters QTabWidget.
        """
        # parameter box
        stability_widget = QWidget()
        stability_widget_layout = QGridLayout(stability_widget)
        # readout
        pickoff_display_label = QLabel('VPP (V)')
        self.pickoff_display = QLabel('000.00')
        # # record button
        # self.record_button = TextChangingButton(('Stop Recording', 'Start Recording'))
        # self.record_button.setMaximumHeight(25)
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
        # anharmonic_limit
        anharmonic_limit_label = QLabel("Anharmonic Limit (%)")
        self.anharmonic_limit = QLabel("00.00")

        # configure display elements
        for display in (self.pickoff_display, self.aparam_display, self.qparam_display, self.wsecr_display, self.wsecz_display):
            display.setFont(QFont(_SHELL_FONT, pointSize=22))
            display.setAlignment(Qt.AlignRight)
            display.setStyleSheet('color: blue')
        for display_label in (pickoff_display_label, aparam_display_label, qparam_display_label,
                              wsecr_display_label, wsecz_display_label):
            display_label.setAlignment(Qt.AlignRight)
        # layout parameter box elements
        stability_widget_layout.addWidget(pickoff_display_label,          1, 0, 1, 1)
        stability_widget_layout.addWidget(self.pickoff_display,           2, 0, 1, 1)
        stability_widget_layout.addWidget(aparam_display_label,           1, 1, 1, 1)
        stability_widget_layout.addWidget(self.aparam_display,            2, 1, 1, 1)
        stability_widget_layout.addWidget(qparam_display_label,           1, 2, 1, 1)
        stability_widget_layout.addWidget(self.qparam_display,            2, 2, 1, 1)
        stability_widget_layout.addWidget(wsecr_display_label,            3, 1, 1, 1)
        stability_widget_layout.addWidget(self.wsecr_display,             4, 1, 1, 1)
        stability_widget_layout.addWidget(wsecz_display_label,            3, 2, 1, 1)
        stability_widget_layout.addWidget(self.wsecz_display,             4, 2, 1, 1)
        #stability_widget_layout.addWidget(self.record_button,           4, 0, 1, 1)
        return stability_widget

    def _makeIonTab(self):
        """
        This tab allows configuration of ion chain data to retrieve
        mode values (i.e. eigenvector components and mode frequencies).
        """
        # create holders
        iontab_widget = QWidget()
        iontab_widget_layout = QGridLayout(iontab_widget)
        # total_ions
        total_ion_label = QLabel("# of ions")
        self.total_ions = QDoubleSpinBox()
        self.total_ions.setRange(1, 10)
        self.total_ions.setDecimals(0)
        self.total_ions.setSingleStep(1)
        # ion_list
        ion_list_label = QLabel("Ion #")
        self.ion_list = QComboBox()
        # ion_mass
        ion_mass_label = QLabel("Mass of Ion #0 (amu)")
        self.ion_mass = QDoubleSpinBox()
        self.ion_mass.setRange(1, 200)
        self.ion_mass.setDecimals(1)
        self.ion_mass.setSingleStep(1)
        # l0_distance
        l0_distance_label = QLabel("Equilibrium Distance (\u03BCm)")
        self.l0_distance = QLabel("00.00")

        # lay out
        iontab_widget_layout.addWidget(total_ion_label)
        iontab_widget_layout.addWidget(self.total_ions)
        iontab_widget_layout.addWidget(ion_list_label)
        iontab_widget_layout.addWidget(self.ion_list)
        iontab_widget_layout.addWidget(ion_mass_label)
        iontab_widget_layout.addWidget(self.ion_mass)
        iontab_widget_layout.addWidget(l0_distance_label)
        iontab_widget_layout.addWidget(self.l0_distance)
        # todo: integrate with andor

    def _makeTrapTab(self):
        """
        This tab allows configuration of trap parameters.
        Part of the Parameters QTabWidget.
        """
        # create holders
        trap_widget = QWidget()
        trap_widget_layout = QGridLayout(trap_widget)
        # todo: think of a better way for this
        # lay out
        return trap_widget

    def _makeMathieuDisplayTab(self):
        """
        This tab draws the stability plot display.
        Part of the Display QTabWidget
        """
        # create holder widget
        mathieu_widget = QWidget()
        mathieu_widget_display = QGridLayout(mathieu_widget)
        # create plotwidget for display
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
        # create stability boundaries for mathieu
        # todo: cut off after intersection; also do negative
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
        mathieu_widget_display.addWidget(beta_setting_display,          0, 0, 1, 1)
        mathieu_widget_display.addWidget(self.beta_setting,             1, 0, 1, 1)
        mathieu_widget_display.addWidget(self.autoscale,                1, 1, 1, 1)
        mathieu_widget_display.addWidget(self.stability_display,        2, 0, 3, 3)
        return 

    def _makeEigenTab(self):
        """
        This tab displays the ion chain mode data.
        Part of the Display QTabWidget.
        """
        pass

    def makeLayout(self):
        # create tabwidget to store the Parameters and Chain tabs
        parameterTabWidget = QTabWidget()
        displayTabWidget = QTabWidget()
        # create parameter tabs
        parameter_tabs = {
            'Stability': self._makeStabilityTab(),
            'Ion Chain': self._makeIonTab(),
            'Trap': self._makeTrapTab()
        }
        for tab_name, tab_widget in parameter_tabs.items():
            parameterTabWidget.addTab(tab_widget, tab_name)
        # create display tabs
        display_tabs = {
            'Mathieu': self._makeMathieuDisplayTab(),
            'Eigenmode Data': self._makeEigenTab(),
        }
        for tab_name, tab_widget in display_tabs.items():
            displayTabWidget.addTab(tab_widget, tab_name)
        # title
        title = QLabel('Stability Client')
        title.setFont(QFont(_SHELL_FONT, pointSize=18))
        title.setAlignment(Qt.AlignCenter)
        # lay out
        layout = QGridLayout(self)
        layout.addWidget(title,                             0, 0, 1, 4)
        layout.addWidget(parameterTabWidget,                1, 0, 2, 4)
        layout.addWidget(displayTabWidget,                  4, 0, 3, 4)

    def drawStability(self, beta=0.4):
        xarr = np.linspace(0, 1, 100)
        yarr = np.power(beta, 2) - 0.5 * np.power(xarr, 2)
        self.stability_region.setData(xarr, yarr)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(stability_gui)
