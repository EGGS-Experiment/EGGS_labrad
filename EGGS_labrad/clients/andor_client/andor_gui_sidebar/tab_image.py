from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QFrame, QWidget, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox,
                             QPushButton, QCheckBox, QSizePolicy, QComboBox, QHBoxLayout)


from EGGS_labrad.clients import SHELL_FONT
from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox

_ANDOR_ALIGNMENT = (Qt.AlignRight | Qt.AlignVCenter)


class SidebarTabImage(QWidget):
    """
    Image setup widget for Andor GUI.
    Intended for use as a sidebar widget.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._makeLayout()
        self._connectLayout()

    def _makeLayout(self):
        """
        Create GUI layout.
        """
        # create master layout
        layout = QGridLayout(self)

        '''Setup - ROI'''
        # ROI selection
        roi_label = QLabel("ROI:")
        roi_label.setAlignment(_ANDOR_ALIGNMENT)
        self.roi = QComboBox()
        self.roi.setFont(QFont(SHELL_FONT, pointSize=12))
        self.roi.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.roi.addItems(['todo: idk'])

        # ROI - custom
        # todo: only enable if the custom label is selected


        # binning
        binning_label = QLabel("Binning:")
        binning_label.setAlignment(_ANDOR_ALIGNMENT)
        self.binning = QComboBox()
        self.binning.setFont(QFont(SHELL_FONT, pointSize=12))
        self.binning.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.binning.addItems(['todo: idk'])

        # create section widget
        roi_holder = QWidget()
        roi_widget_layout = QGridLayout(roi_holder)
        # lay out section
        roi_widget_layout.addWidget(roi_label,          0, 0, 1, 1)
        roi_widget_layout.addWidget(self.roi,           0, 1, 1, 1)
        roi_widget_layout.addWidget(binning_label,      1, 0, 1, 1)
        roi_widget_layout.addWidget(self.binning,       1, 1, 1, 1)
        # enclose section in a QGroupBox
        roi_widget = QCustomGroupBox(roi_holder, "ROI (Region of Interest)")


        '''Setup - Display'''
        # rotation
        rotation_label = QLabel("Rotate Image:")
        rotation_label.setAlignment(_ANDOR_ALIGNMENT)
        self.rotation = QComboBox()
        self.rotation.setFont(QFont(SHELL_FONT, pointSize=12))
        self.rotation.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.rotation.addItems(['None', 'Clockwise', 'Anticlockwise'])

        # flip image
        flip_vertical_label = QLabel("Flip Vertically:")
        flip_vertical_label.setAlignment(_ANDOR_ALIGNMENT)
        self.flip_vertical = QCheckBox()
        self.flip_vertical.setFont(QFont(SHELL_FONT, pointSize=12))
        self.flip_vertical.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        flip_horizontal_label = QLabel("Flip Horizontally:")
        flip_horizontal_label.setAlignment(_ANDOR_ALIGNMENT)
        self.flip_horizontal = QCheckBox()
        self.flip_horizontal.setFont(QFont(SHELL_FONT, pointSize=12))
        self.flip_horizontal.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # create section widget
        display_holder = QWidget()
        display_widget_layout = QGridLayout(display_holder)
        # lay out section
        display_widget_layout.addWidget(flip_vertical_label,        0, 0, 1, 1)
        display_widget_layout.addWidget(self.flip_vertical,         0, 1, 1, 1)
        display_widget_layout.addWidget(flip_horizontal_label,      1, 0, 1, 1)
        display_widget_layout.addWidget(self.flip_horizontal,       1, 1, 1, 1)
        display_widget_layout.addWidget(rotation_label,             2, 0, 1, 1)
        display_widget_layout.addWidget(self.rotation,              2, 1, 1, 1)
        # enclose section in a QGroupBox
        display_widget = QCustomGroupBox(display_holder, "Display")


        '''Lay out GUI elements'''
        layout.addWidget(roi_widget,        0, 0)
        layout.addWidget(display_widget,    1, 0)


    def _connectLayout(self):
        pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(SidebarTabImage)
