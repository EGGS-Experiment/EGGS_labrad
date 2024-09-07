from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QValidator
from PyQt5.QtWidgets import (QFrame, QWidget, QGridLayout, QLabel, QDoubleSpinBox, QSpinBox,
                             QPushButton, QCheckBox, QSizePolicy, QComboBox, QHBoxLayout,
                             QFileDialog, QLineEdit)

import os

from EGGS_labrad.clients import SHELL_FONT
from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox

_ANDOR_ALIGNMENT = (Qt.AlignRight | Qt.AlignVCenter)


class SidebarTabSave(QWidget):
    """
    Save setup widget for Andor GUI.
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

        '''Save Directory'''
        # file name entry
        file_name_label = QLabel("File Name:")
        file_name_label.setAlignment(_ANDOR_ALIGNMENT)
        self.file_name = QLineEdit()
        self.file_name.setFont(QFont(SHELL_FONT, pointSize=12))
        self.file_name.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # create QValidator object to ensure filename is valid
        self._file_name_validator = QFilenameValidator()
        self.file_name.setValidator(self._file_name_validator)


        # save type (local or labrad)
        save_type_label = QLabel("Save Type:")
        save_type_label.setAlignment(_ANDOR_ALIGNMENT)
        self.save_type = QComboBox()
        self.save_type.setFont(QFont(SHELL_FONT, pointSize=12))
        self.save_type.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.save_type.addItems(['Labrad', 'Local'])

        # save directory (create custom widget)
        save_directory_label = QLabel("Save Directory:")
        save_directory_label.setAlignment(_ANDOR_ALIGNMENT)
        self.save_directory = QDirectoryBrowser()

        # data type
        data_type_label = QLabel("Data Type:")
        data_type_label.setAlignment(_ANDOR_ALIGNMENT)
        self.data_type = QComboBox()
        self.data_type.setFont(QFont(SHELL_FONT, pointSize=12))
        self.data_type.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.data_type.addItems(['CSV', 'JPEG', 'PNG'])

        # include header
        include_header_label = QLabel("Include Header?")
        include_header_label.setAlignment(_ANDOR_ALIGNMENT)
        self.include_header = QCheckBox()
        self.include_header.setFont(QFont(SHELL_FONT, pointSize=12))
        self.include_header.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # create section widget
        save_holder = QWidget()
        save_widget_layout = QGridLayout(save_holder)
        # lay out section
        save_widget_layout.addWidget(file_name_label,           0, 0, 1, 1)
        save_widget_layout.addWidget(self.file_name,            0, 1, 1, 1)
        save_widget_layout.addWidget(save_type_label,           1, 0, 1, 1)
        save_widget_layout.addWidget(self.save_type,            1, 1, 1, 1)
        save_widget_layout.addWidget(save_directory_label,      2, 0, 1, 1)
        save_widget_layout.addWidget(self.save_directory,       2, 1, 1, 1)
        save_widget_layout.addWidget(data_type_label,           3, 0, 1, 1)
        save_widget_layout.addWidget(self.data_type,            3, 1, 1, 1)
        save_widget_layout.addWidget(include_header_label,      4, 0, 1, 1)
        save_widget_layout.addWidget(self.include_header,       4, 1, 1, 1)
        # enclose section in a QGroupBox
        save_widget = QCustomGroupBox(save_holder, "Save Setup")


        '''Recording Setup'''
        # save interval
        save_interval_label = QLabel("Save Interval (s):")
        save_interval_label.setAlignment(_ANDOR_ALIGNMENT)
        self.save_interval = QDoubleSpinBox()
        self.save_interval.setDecimals(0)
        self.save_interval.setSingleStep(1)
        self.save_interval.setRange(1, 60)
        self.save_interval.setFont(QFont(SHELL_FONT, pointSize=12))
        self.save_interval.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # record time
        # todo: somehow enforce that record time exceeds save interval
        record_time_label = QLabel("Total Record Time (s):")
        record_time_label.setAlignment(_ANDOR_ALIGNMENT)
        self.record_time = QDoubleSpinBox()
        self.record_time.setDecimals(0)
        self.record_time.setSingleStep(100)
        self.record_time.setRange(2, 500000)
        self.record_time.setFont(QFont(SHELL_FONT, pointSize=12))
        self.record_time.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        # create section widget
        record_holder = QWidget()
        record_widget_layout = QGridLayout(record_holder)
        # lay out section
        record_widget_layout.addWidget(save_interval_label,    0, 0, 1, 1)
        record_widget_layout.addWidget(self.save_interval,     0, 1, 1, 1)
        record_widget_layout.addWidget(record_time_label,      1, 0, 1, 1)
        record_widget_layout.addWidget(self.record_time,       1, 1, 1, 1)
        # enclose section in a QGroupBox
        record_widget = QCustomGroupBox(record_holder, "Recording Setup")


        '''Lay out GUI elements'''
        layout.addWidget(save_widget,       0, 0)
        layout.addWidget(record_widget,     1, 0)

    def _connectLayout(self):
        pass


class QDirectoryBrowser(QWidget):
    """
    A QWidget that enables the user to browse a directory.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # create widgets
        self.browse_button = QPushButton("Browse")
        self.directory_name = QLineEdit()
        # self.directory_name.setEnabled(False)

        # lay out widgets
        layout = QGridLayout(self)
        layout.addWidget(self.directory_name,   0, 0)
        layout.addWidget(self.browse_button,    0, 1)
        layout.setColumnStretch(0, 4)
        layout.setColumnStretch(1, 1)

        # connect signals to slots
        self._connectLayout()

    def _connectLayout(self):
        """
        Connect signals (i.e. events) to slots (i.e. event processor).
        """
        self.browse_button.clicked.connect(self.set_save_directory)

    def set_save_directory(self):
        """
        Create a QFileDialog object to allow the user to select a save directory.
        """
        base_dir = "/home"
        # see if existing directory name exists
        if os.path.isdir(self.directory_name.text()):
            base_dir = self.directory_name.text()

        # create a QFileDialog at the existing directory
        savedir_dialog = QFileDialog()
        savedir_path = savedir_dialog.getExistingDirectory(self,
                                                           "Image Save Directory",
                                                           base_dir,
                                                           QFileDialog.ShowDirsOnly)
        # display the returned directory name
        self.directory_name.setText(savedir_path)

    def get_save_directory(self):
        """
        Get the desired save directory.
        Intended for use by parent widgets.
        Returns:
            (str): a string of the directory path.
        """
        return self.directory_name.text()


class QFilenameValidator(QValidator):
    """
    Ensures file names contain only valid characters.
    """
    invalid_characters = (" ", "/", "\\", "$", "%")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def validate(self, filename_str, cursor_pos):
        # test if file_str contains invalid characters
        filename_invalid = any([inv_char in filename_str for inv_char in self.invalid_characters])

        if filename_invalid:    return (QValidator.Invalid, filename_str, cursor_pos)
        else:                   return (QValidator.Acceptable, filename_str, cursor_pos)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(SidebarTabSave)
