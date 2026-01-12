import numpy as np
import pyqtgraph as pg

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QGridLayout, QGroupBox, QDoubleSpinBox, QPushButton,\
    QTabWidget, QComboBox, QRadioButton, QHBoxLayout, QVBoxLayout, QTreeWidget, QTreeWidgetItem

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox

_SHELL_FONT = 'MS Shell Dlg 2'
# todo: clean up display pyqtgraph


class stability_gui(QFrame):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(400, 875)
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
        # l0_distance
        l0_distance_label = QLabel("Length Scale (\u03BCm)")
        self.l0_distance = QLabel("00.00")
        self.l0_distance.setStyleSheet('color: blue')
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
        for display in (self.l0_distance, self.aparam_display, self.qparam_display, self.wsecr_display,
                        self.wsecz_display, self.anharmonic_limit):
            display.setFont(QFont(_SHELL_FONT, pointSize=22))
            display.setAlignment(Qt.AlignRight)
            display.setStyleSheet('color: blue')
        for display_label in (l0_distance_label, aparam_display_label, qparam_display_label,
                              wsecr_display_label, wsecz_display_label, anharmonic_limit_label):
            display_label.setAlignment(Qt.AlignRight)
        # layout parameter box elements
        stability_widget_layout.addWidget(anharmonic_limit_label,         1, 0, 1, 1)
        stability_widget_layout.addWidget(self.anharmonic_limit,          2, 0, 1, 1)
        stability_widget_layout.addWidget(aparam_display_label,           1, 1, 1, 1)
        stability_widget_layout.addWidget(self.aparam_display,            2, 1, 1, 1)
        stability_widget_layout.addWidget(qparam_display_label,           1, 2, 1, 1)
        stability_widget_layout.addWidget(self.qparam_display,            2, 2, 1, 1)
        stability_widget_layout.addWidget(wsecr_display_label,            3, 1, 1, 1)
        stability_widget_layout.addWidget(self.wsecr_display,             4, 1, 1, 1)
        stability_widget_layout.addWidget(wsecz_display_label,            3, 2, 1, 1)
        stability_widget_layout.addWidget(self.wsecz_display,             4, 2, 1, 1)
        stability_widget_layout.addWidget(l0_distance_label,              3, 0, 1, 1)
        stability_widget_layout.addWidget(self.l0_distance,               4, 0, 1, 1)
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
        self.total_ions.setKeyboardTracking(False)
        # ion_num
        ion_num_label = QLabel("Ion #")
        self.ion_num = QComboBox()
        # ion_mass
        ion_mass_label = QLabel("Ion Mass (amu)")
        self.ion_mass = QDoubleSpinBox()
        self.ion_mass.setRange(1, 200)
        self.ion_mass.setDecimals(1)
        self.ion_mass.setSingleStep(1)
        self.ion_mass.setKeyboardTracking(False)

        # configure display elements
        for display in (self.total_ions, self.ion_num, self.ion_mass):
            try:
                display.setFont(QFont(_SHELL_FONT, pointSize=18))
                display.setAlignment(Qt.AlignRight)
            except AttributeError:
                pass
        for display_label in (total_ion_label, ion_num_label, ion_mass_label):
            display_label.setAlignment(Qt.AlignRight)

        # lay out
        iontab_widget_layout.addWidget(total_ion_label,             0, 0, 1, 1)
        iontab_widget_layout.addWidget(self.total_ions,             1, 0, 1, 1)
        iontab_widget_layout.addWidget(ion_num_label,              0, 1, 1, 1)
        iontab_widget_layout.addWidget(self.ion_num,               1, 1, 1, 1)
        iontab_widget_layout.addWidget(ion_mass_label,              0, 2, 1, 1)
        iontab_widget_layout.addWidget(self.ion_mass,               1, 2, 1, 1)
        # todo: integrate with andor
        return iontab_widget

    def _makeTrapTab(self):
        """
        This tab allows configuration of dynamic trap parameters.
        Part of the Parameters QTabWidget.
        """
        # create holders
        trap_widget = QWidget()
        trap_widget_layout = QGridLayout(trap_widget)
        # vrf
        vrf_display_label = QLabel('VRF (Vpp)')
        self.vrf_display = QDoubleSpinBox()
        # vrf - offset
        voff_display_label = QLabel('V_off (V)')
        self.voff_display = QDoubleSpinBox()
        # wrf
        wrf_display_label = QLabel('\u03C9RF (x2\u03C0 MHz)')
        self.wrf_display = QDoubleSpinBox()
        # vdc
        vdc_display_label = QLabel('VDC (V)')
        self.vdc_display = QDoubleSpinBox()

        # configure display elements
        for display in (self.vrf_display, self.voff_display, self.wrf_display, self.vdc_display):
            display.setFont(QFont(_SHELL_FONT, pointSize=12))
            display.setAlignment(Qt.AlignRight)
            display.setDecimals(3)
            display.setSingleStep(1)
            display.setRange(-100, 1000)
            display.setKeyboardTracking(False)
        for display_label in (vrf_display_label, voff_display_label,
                              wrf_display_label, vdc_display_label):
            display_label.setAlignment(Qt.AlignRight)

        # create radio buttons
        radio_widget = QWidget()
        radio_widget_layout = QHBoxLayout(radio_widget)
        self.values_get = QRadioButton("Get Values from System")
        self.values_set = QRadioButton("Manually Set Values")
        radio_widget_layout.addWidget(self.values_get)
        radio_widget_layout.addWidget(self.values_set)
        self.values_set.setChecked(True)

        # lay out
        trap_widget_layout.addWidget(radio_widget,                  0, 0, 1, 2)
        trap_widget_layout.addWidget(vrf_display_label,             1, 0, 1, 1)
        trap_widget_layout.addWidget(self.vrf_display,              2, 0, 1, 1)
        trap_widget_layout.addWidget(wrf_display_label,             1, 1, 1, 1)
        trap_widget_layout.addWidget(self.wrf_display,              2, 1, 1, 1)
        trap_widget_layout.addWidget(vdc_display_label,             3, 0, 1, 1)
        trap_widget_layout.addWidget(self.vdc_display,              4, 0, 1, 1)
        trap_widget_layout.addWidget(voff_display_label,              3, 1, 1, 1)
        trap_widget_layout.addWidget(self.voff_display,               4, 1, 1, 1)
        return trap_widget

    def _makeGeometryTab(self):
        """
        This tab allows configuration of trap geometry parameters.
        Part of the Parameters QTabWidget.
        """
        # r0, kr, z0, kz
        # create holders
        geometry_widget = QWidget()
        geometry_widget_layout = QGridLayout(geometry_widget)

        # display labels
        r0_display_label = QLabel('r0 (\u03BCm)')
        kr_display_label = QLabel('\u03BAr')
        z0_display_label = QLabel('z0 (\u03BCm)')
        kz_display_label = QLabel('\u03BAz')

        # spin boxes
        self.r0_display = QDoubleSpinBox()
        self.kr_display = QDoubleSpinBox()
        self.z0_display = QDoubleSpinBox()
        self.kz_display = QDoubleSpinBox()

        # configure display elements
        for spinbox in (self.r0_display, self.kr_display, self.z0_display, self.kz_display):
            spinbox.setFont(QFont(_SHELL_FONT, pointSize=12))
            spinbox.setAlignment(Qt.AlignRight)

        for spinbox in (self.r0_display, self.z0_display):
            spinbox.setRange(0, 10000)
            spinbox.setDecimals(0)
            spinbox.setSingleStep(1)

        for spinbox in (self.kr_display, self.kz_display):
            spinbox.setRange(0, 1)
            spinbox.setDecimals(3)
            spinbox.setSingleStep(1)

        for display_label in (r0_display_label, kr_display_label, z0_display_label, kz_display_label):
            display_label.setAlignment(Qt.AlignRight)

        # lay out
        geometry_widget_layout.addWidget(r0_display_label,              0, 0, 1, 1)
        geometry_widget_layout.addWidget(self.r0_display,               1, 0, 1, 1)
        geometry_widget_layout.addWidget(kr_display_label,              0, 1, 1, 1)
        geometry_widget_layout.addWidget(self.kr_display,               1, 1, 1, 1)
        geometry_widget_layout.addWidget(z0_display_label,              2, 0, 1, 1)
        geometry_widget_layout.addWidget(self.z0_display,               3, 0, 1, 1)
        geometry_widget_layout.addWidget(kz_display_label,              2, 1, 1, 1)
        geometry_widget_layout.addWidget(self.kz_display,               3, 1, 1, 1)
        return geometry_widget

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
        self.beta_setting.setSingleStep(1)
        self.beta_setting.setRange(0, 5)
        self.beta_setting.setKeyboardTracking(False)
        self.beta_setting.setAlignment(Qt.AlignRight)
        # autoscale button
        self.autoscale = QPushButton("Autoscale")
        # lay out
        mathieu_widget_display.addWidget(beta_setting_display,          0, 0, 1, 1)
        mathieu_widget_display.addWidget(self.beta_setting,             1, 0, 1, 1)
        mathieu_widget_display.addWidget(self.autoscale,                1, 1, 1, 1)
        mathieu_widget_display.addWidget(self.stability_display,        2, 0, 3, 3)
        return mathieu_widget

    def _makeEigenTab(self):
        """
        This tab displays the ion chain mode data.
        Part of the Display QTabWidget.
        """
        # create holders
        eigen_widget = QWidget()
        eigen_widget_layout = QGridLayout(eigen_widget)
        # create widgets
        self.eigenmode_axial_display = QTreeWidget()
        self.eigenmode_axial_display.setHeaderLabels(["Mode Frequency (x2\u03C0 MHz)", "Ion Number", "Mode Amplitude"])
        self.eigenmode_radial_display = QTreeWidget()
        self.eigenmode_radial_display.setHeaderLabels(["Mode Frequency (x2\u03C0 MHz)", "Ion Number", "Mode Amplitude"])
        # lay out
        eigen_widget_layout.addWidget(QCustomGroupBox(self.eigenmode_axial_display, "Axial Modes"))
        eigen_widget_layout.addWidget(QCustomGroupBox(self.eigenmode_radial_display, "Radial Modes"))
        return eigen_widget

    def makeLayout(self):
        # create parameter tab widget
        parameterTabWidget = QTabWidget()

        chain_widget = QWidget()
        chain_widget_layout = QVBoxLayout(chain_widget)
        chain_widget_layout.addWidget(QCustomGroupBox(self._makeIonTab(), "Ion Chain"))
        chain_widget_layout.addWidget(QCustomGroupBox(self._makeStabilityTab(), "Ion Stability"))

        trap_widget = QWidget()
        trap_widget_layout = QVBoxLayout(trap_widget)
        trap_widget_layout.addWidget(QCustomGroupBox(self._makeTrapTab(), "Trap Parameter"))
        trap_widget_layout.addWidget(QCustomGroupBox(self._makeGeometryTab(), "Trap Geometry"))

        parameterTabWidget.addTab(chain_widget, "Ion Chain")
        parameterTabWidget.addTab(trap_widget, "Trap")

        # create display tab widget
        display_tabs = {
            'Mathieu': self._makeMathieuDisplayTab(),
            'Eigenmode Data': self._makeEigenTab(),
        }
        displayTabWidget = QTabWidget()
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
