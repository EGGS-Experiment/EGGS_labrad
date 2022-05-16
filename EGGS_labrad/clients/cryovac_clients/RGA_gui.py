from PyQt5.QtGui import QFont
from PyQt5.QtCore import QRect, Qt
from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout, QPushButton, QWidget, QDoubleSpinBox, QComboBox, QPlainTextEdit

from EGGS_labrad.clients.Widgets import Lockswitch, QCustomGroupBox


class RGA_gui(QFrame):

    def __init__(self):
        super().__init__()
        self.setFixedSize(650, 445)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("SRS RGA Client")
        self.makeLayout()

    def _makeGeneralWidget(self):
        general_widget = QWidget()
        general_widget_layout = QGridLayout(general_widget)
        general_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.calibrate_electrometer = QPushButton("Calibrate Electrometer")
        self.calibrate_detector = QPushButton("Calibrate Detector")
        self.initialize = QPushButton("Initialize")
        self.general_lockswitch = Lockswitch()
        self.degas = QPushButton("Degas")
        self.general_tp = QPushButton("Total Pressure")
        
        general_widget_layout.addWidget(self.general_lockswitch,        1, 1, 1, 1)
        general_widget_layout.addWidget(self.initialize,                2, 1, 1, 1)
        general_widget_layout.addWidget(self.calibrate_detector,        3, 1, 1, 1)
        general_widget_layout.addWidget(self.calibrate_electrometer,    4, 1, 1, 1)
        general_widget_layout.addWidget(self.degas,                     5, 1, 1, 1)
        general_widget_layout.addWidget(self.general_tp,                6, 1, 1, 1)
        return QCustomGroupBox(general_widget, "General")

    def _makeScanWidget(self):
        scan_widget = QWidget()
        scan_widget_layout = QGridLayout(scan_widget)
        scan_widget_layout.setContentsMargins(0, 0, 0, 0)

        scan_mf_label = QLabel("Stop Mass (amu)")
        scan_mi_label = QLabel("Start Mass (amu)")
        scan_sa_label = QLabel("Steps per amu")
        mass_lock_label = QLabel("Mass Lock")
        scan_num_label = QLabel("Number of scans")
        scan_type_label = QLabel("Type")

        self.scan_lockswitch = Lockswitch()
        self.scan_start = QPushButton("Start")
        
        self.scan_num = QDoubleSpinBox()
        self.scan_num.setKeyboardTracking(False)
        self.scan_num.setDecimals(0)
        self.scan_num.setRange(1.0, 255.0)

        self.scan_sa = QDoubleSpinBox()
        self.scan_sa.setKeyboardTracking(False)
        self.scan_sa.setDecimals(0)
        self.scan_sa.setRange(10.0, 25.0)
        self.scan_sa.setSingleStep(1.0)

        self.scan_type = QComboBox()
        self.scan_type.addItems(["Analog", "Histogram", "Single Mass", "Total Pressure"])

        self.mass_lock = QDoubleSpinBox()
        self.scan_mi = QDoubleSpinBox()
        self.scan_mf = QDoubleSpinBox()
        for widget in (self.mass_lock, self.scan_mi, self.scan_mf):
            widget.setKeyboardTracking(False)
            widget.setDecimals(0)
            widget.setRange(0.0, 200.0)
        
        scan_widget_layout.addWidget(self.scan_lockswitch,      1, 1, 1, 1)
        scan_widget_layout.addWidget(scan_type_label,           2, 1, 1, 1)
        scan_widget_layout.addWidget(self.scan_type,            3, 1, 1, 1)
        scan_widget_layout.addWidget(mass_lock_label,           4, 1, 1, 1)
        scan_widget_layout.addWidget(scan_mi_label,             6, 1, 1, 1)
        scan_widget_layout.addWidget(self.mass_lock,            5, 1, 1, 1)
        scan_widget_layout.addWidget(self.scan_mi,              7, 1, 1, 1)
        scan_widget_layout.addWidget(scan_mf_label,             10, 1, 1, 1)
        scan_widget_layout.addWidget(self.scan_mf,              11, 1, 1, 1)
        scan_widget_layout.addWidget(scan_sa_label,             12, 1, 1, 1)
        scan_widget_layout.addWidget(self.scan_sa,              13, 1, 1, 1)
        scan_widget_layout.addWidget(scan_num_label,            14, 1, 1, 1)
        scan_widget_layout.addWidget(self.scan_num,             15, 1, 1, 1)
        scan_widget_layout.addWidget(self.scan_start,           18, 1, 1, 1)
        return QCustomGroupBox(scan_widget, "Scan")

    def _makeDetectorWidget(self):
        detector_widget = QWidget()
        detector_widget_layout = QGridLayout(detector_widget)
        detector_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.detector_lockswitch = Lockswitch()

        detector_cv_label = QLabel("CDEM Voltage (V)")
        detector_nf_label = QLabel("Noise Floor")

        self.detector_hv = QDoubleSpinBox()
        self.detector_hv.setKeyboardTracking(False)
        self.detector_hv.setDecimals(0)
        self.detector_hv.setRange(10, 2490)
        self.detector_hv.setSingleStep(1)

        self.detector_nf = QComboBox()
        for i in range(8):
            self.detector_nf.addItem(str(i))

        detector_widget_layout.addWidget(self.detector_lockswitch,      2, 1, 1, 1)
        detector_widget_layout.addWidget(detector_cv_label,             3, 1, 1, 1)
        detector_widget_layout.addWidget(self.detector_hv,              4, 1, 1, 1)
        detector_widget_layout.addWidget(detector_nf_label,             5, 1, 1, 1)
        detector_widget_layout.addWidget(self.detector_nf,              6, 1, 1, 1)
        return QCustomGroupBox(detector_widget, "Detector")

    def _makeIonizerWidget(self):
        ionizer_widget = QWidget()
        ionizer_widget_layout = QGridLayout(ionizer_widget)
        ionizer_widget_layout.setContentsMargins(0, 0, 0, 0)
        self.ionizer_lockswitch = Lockswitch()

        ionizer_ie_label = QLabel("Ion Energy (eV)")
        ionizer_ee_label = QLabel("Electron Energy (eV)")
        ionizer_vf_label = QLabel("Focus Voltage (V)")
        ionizer_fl_label = QLabel("Filament Current (mA)")

        self.ionizer_ee = QDoubleSpinBox()
        self.ionizer_ee.setKeyboardTracking(False)
        self.ionizer_ee.setDecimals(0)
        self.ionizer_ee.setRange(25.0, 105.0)
        self.ionizer_ee.setSingleStep(1.0)

        self.ionizer_ie = QComboBox()
        self.ionizer_ie.addItems(["8", "12"])

        self.ionizer_fl = QDoubleSpinBox()
        self.ionizer_fl.setKeyboardTracking(False)
        self.ionizer_fl.setDecimals(2)
        self.ionizer_fl.setRange(0.0, 3.5)
        self.ionizer_fl.setSingleStep(0.1)

        self.ionizer_vf = QDoubleSpinBox()
        self.ionizer_vf.setKeyboardTracking(False)
        self.ionizer_vf.setDecimals(0)
        self.ionizer_vf.setRange(0, 150)
        self.ionizer_vf.setSingleStep(1)
        
        ionizer_widget_layout.addWidget(self.ionizer_lockswitch,      2, 0, 1, 1)
        ionizer_widget_layout.addWidget(ionizer_fl_label,             3, 0, 1, 1)
        ionizer_widget_layout.addWidget(self.ionizer_fl,              4, 0, 1, 1)
        ionizer_widget_layout.addWidget(ionizer_vf_label,             5, 0, 1, 1)
        ionizer_widget_layout.addWidget(self.ionizer_vf,              6, 0, 1, 1)
        ionizer_widget_layout.addWidget(ionizer_ee_label,             7, 0, 1, 1)
        ionizer_widget_layout.addWidget(self.ionizer_ee,              8, 0, 1, 1)
        ionizer_widget_layout.addWidget(ionizer_ie_label,             9, 0, 1, 1)
        ionizer_widget_layout.addWidget(self.ionizer_ie,              10, 0, 2, 1)
        return QCustomGroupBox(ionizer_widget, "Ionizer")

    def _makeBufferWidget(self):
        buffer_widget = QWidget()
        buffer_widget_layout = QGridLayout(buffer_widget)
        buffer_widget_layout.setContentsMargins(0, 0, 0, 0)

        self.buffer_readout = QPlainTextEdit()
        self.buffer_readout.setReadOnly(True)
        self.buffer_clear = QPushButton("Clear")
        
        buffer_widget_layout.addWidget(self.buffer_readout,     1, 0, 1, 1)
        buffer_widget_layout.addWidget(self.buffer_clear,       2, 0, 1, 1)
        return QCustomGroupBox(buffer_widget, "Buffer")

    def makeLayout(self):
        font = QFont('MS Shell Dlg 2', pointSize=20)
        layout = QGridLayout(self)

        # title
        title = QLabel("SRS RGA Client")
        title.setFont(font)
        title.setAlignment(Qt.AlignCenter)

        # make widgets
        general_widget_wrapped = self._makeGeneralWidget()
        detector_widget_wrapped = self._makeDetectorWidget()
        ionizer_widget_wrapped = self._makeIonizerWidget()
        scan_widget_wrapped = self._makeScanWidget()
        buffer_widget_wrapped = self._makeBufferWidget()
        for widget in (general_widget_wrapped, detector_widget_wrapped, ionizer_widget_wrapped, scan_widget_wrapped, buffer_widget_wrapped):
            widget.setFixedWidth(150)

        # lay out
        layout.addWidget(title,                         0, 0, 1, 4)
        layout.addWidget(general_widget_wrapped,        1, 0, 6, 1)
        layout.addWidget(detector_widget_wrapped,       7, 0, 4, 1)
        layout.addWidget(ionizer_widget_wrapped,        1, 1, 7, 1)
        layout.addWidget(scan_widget_wrapped,           1, 2, 10, 1)
        layout.addWidget(buffer_widget_wrapped,         1, 3, 10, 1)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(RGA_gui)
