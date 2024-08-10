from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QFrame, QWidget, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox,
                             QPushButton, QCheckBox, QSizePolicy, QComboBox, QHBoxLayout)


from EGGS_labrad.clients import SHELL_FONT
from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox, QCustomUnscrollableSpinBox

_ANDOR_ALIGNMENT = (Qt.AlignRight | Qt.AlignVCenter)


class SidebarTabAcquisition(QWidget):
    """
    Acquisition setup widget for Andor GUI.
    Intended for use as a sidebar widget.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Acquisition Setup")
        self._makeLayout()
        self._connectLayout()

    def _makeLayout(self):
        """
        Create GUI layout.
        """
        # create master layout
        layout = QGridLayout(self)

        '''Setup - Exposure'''
        # exposure time
        exposure_time_label = QLabel("Exposure Time (s):")
        exposure_time_label.setAlignment(_ANDOR_ALIGNMENT)
        self.exposure_time = QCustomUnscrollableSpinBox()
        self.exposure_time.setDecimals(3)
        self.exposure_time.setSingleStep(0.001)
        self.exposure_time.setRange(0.0, 10000.0)
        self.exposure_time.setKeyboardTracking(False)

        # frame transfer
        frame_transfer_label = QLabel("Frame Transfer:")
        frame_transfer_label.setAlignment(_ANDOR_ALIGNMENT)
        self.frame_transfer = QCheckBox()

        # create section widget
        exposure_time_holder = QWidget()
        exposure_time_widget_layout = QGridLayout(exposure_time_holder)
        # lay out section
        exposure_time_widget_layout.addWidget(exposure_time_label,      0, 0, 1, 1)
        exposure_time_widget_layout.addWidget(self.exposure_time,       0, 1, 1, 1)
        exposure_time_widget_layout.addWidget(frame_transfer_label,     1, 0, 1, 1)
        exposure_time_widget_layout.addWidget(self.frame_transfer,      1, 1, 1, 1)
        # enclose section in a QGroupBox
        exposure_time_widget = QCustomGroupBox(exposure_time_holder, "Exposure Time")


        '''Setup - Vertical Shift'''
        # shift speed
        shift_speed_label = QLabel("Vertical Shift Speed (us):")
        shift_speed_label.setAlignment(_ANDOR_ALIGNMENT)
        self.shift_speed = QComboBox()
        self.shift_speed.setFont(QFont(SHELL_FONT, pointSize=12))
        self.shift_speed.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.shift_speed.addItems(['todo: idk'])

        # clock voltage
        clock_voltage_label = QLabel("Clock Voltage (V):")
        clock_voltage_label.setAlignment(_ANDOR_ALIGNMENT)
        self.clock_voltage = QComboBox()
        self.clock_voltage.setFont(QFont(SHELL_FONT, pointSize=12))
        self.clock_voltage.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.clock_voltage.addItems(['todo: idk'])

        # create section widget
        vertical_shift_holder = QWidget()
        vertical_shift_widget_layout = QGridLayout(vertical_shift_holder)
        # lay out section
        vertical_shift_widget_layout.addWidget(shift_speed_label,       0, 0, 1, 1)
        vertical_shift_widget_layout.addWidget(self.shift_speed,        0, 1, 1, 1)
        vertical_shift_widget_layout.addWidget(clock_voltage_label,     1, 0, 1, 1)
        vertical_shift_widget_layout.addWidget(self.clock_voltage,      1, 1, 1, 1)
        # enclose section in a QGroupBox
        vertical_shift_widget = QCustomGroupBox(vertical_shift_holder, "Vertical Shift")


        '''Setup - Horizontal Shift'''
        # readout rate
        readout_rate_label = QLabel("Readout Rate:")
        readout_rate_label.setAlignment(_ANDOR_ALIGNMENT)
        self.readout_rate = QComboBox()
        self.readout_rate.setFont(QFont(SHELL_FONT, pointSize=12))
        self.readout_rate.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.readout_rate.addItems(['todo: idk'])

        # preamplifier gain
        preamplifier_gain_label = QLabel("Preamplifier Gain:")
        preamplifier_gain_label.setAlignment(_ANDOR_ALIGNMENT)
        self.preamplifier_gain = QComboBox()
        self.preamplifier_gain.setFont(QFont(SHELL_FONT, pointSize=12))
        self.preamplifier_gain.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.preamplifier_gain.addItems(['todo: idk'])

        # create section widget
        horizontal_shift_holder = QWidget()
        horizontal_shift_widget_layout = QGridLayout(horizontal_shift_holder)
        # lay out section
        horizontal_shift_widget_layout.addWidget(readout_rate_label,        0, 0, 1, 1)
        horizontal_shift_widget_layout.addWidget(self.readout_rate,         0, 1, 1, 1)
        horizontal_shift_widget_layout.addWidget(preamplifier_gain_label,   1, 0, 1, 1)
        horizontal_shift_widget_layout.addWidget(self.preamplifier_gain,    1, 1, 1, 1)
        # enclose section in a QGroupBox
        horizontal_shift_widget = QCustomGroupBox(horizontal_shift_holder, "Horizontal Shift")


        '''Setup - EMCCD'''
        # emccd enable
        emccd_enable_label = QLabel("Enable EMCCD:")
        emccd_enable_label.setAlignment(_ANDOR_ALIGNMENT)
        self.emccd_enable = QCheckBox()

        # emccd gain
        emccd_gain_label = QLabel("EMCCD Gain:")
        emccd_gain_label.setAlignment(_ANDOR_ALIGNMENT)
        self.emccd_gain = QCustomUnscrollableSpinBox()
        self.emccd_gain.setDecimals(0)
        self.emccd_gain.setSingleStep(1)
        self.emccd_gain.setRange(1, 250)
        self.emccd_gain.setKeyboardTracking(False)

        # create section widget
        emccd_holder = QWidget()
        emccd_widget_layout = QGridLayout(emccd_holder)
        # lay out section
        emccd_widget_layout.addWidget(emccd_enable_label,   0, 0, 1, 1)
        emccd_widget_layout.addWidget(self.emccd_enable,    0, 1, 1, 1)
        emccd_widget_layout.addWidget(emccd_gain_label,     1, 0, 1, 1)
        emccd_widget_layout.addWidget(self.emccd_gain,      1, 1, 1, 1)
        # enclose section in a QGroupBox
        emccd_widget = QCustomGroupBox(emccd_holder, "EMCCD")


        '''Lay out GUI elements'''
        layout.addWidget(exposure_time_widget,      0, 0)
        layout.addWidget(vertical_shift_widget,     1, 0)
        layout.addWidget(horizontal_shift_widget,   2, 0)
        layout.addWidget(emccd_widget,              3, 0)


    def _connectLayout(self):
        pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(SidebarTabAcquisition)
