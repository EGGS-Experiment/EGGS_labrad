from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox


class AD5372_channel(QFrame):
    """
    GUI for a single AD5372 DAC channel (Zotino).
    """

    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self.setMinimumSize(300, 125)
        self.setMaximumSize(400, 175)
        self.makeLayout(name)

    def makeLayout(self, title):
        layout = QGridLayout(self)
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        dac_label = QLabel('DAC Register')
        off_label = QLabel('Offset Register')
        gain_label = QLabel('Gain Register')

        # editable fields
        self.dac = QDoubleSpinBox()
        self.dac.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.dac.setDecimals(0)
        self.dac.setSingleStep(1)
        self.dac.setRange(0, 0xffff)
        self.dac.setKeyboardTracking(False)
        self.dac.setAlignment(Qt.AlignRight)
        self.gain = QDoubleSpinBox()
        self.gain.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.gain.setDecimals(0)
        self.gain.setSingleStep(1)
        self.gain.setRange(0, 0xffff)
        self.gain.setKeyboardTracking(False)
        self.gain.setAlignment(Qt.AlignRight)
        self.off = QDoubleSpinBox()
        self.off.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.off.setDecimals(0)
        self.off.setSingleStep(1)
        self.off.setRange(0, 0xffff)
        self.off.setKeyboardTracking(False)
        self.off.setAlignment(Qt.AlignRight)

        # buttons
        self.resetswitch = QPushButton('Reset')
        self.resetswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.calibrateswitch = QPushButton('Calibrate')
        self.calibrateswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.lockswitch = TextChangingButton(("Unlocked", "Locked"))
        self.lockswitch.toggled.connect(lambda status: self.lock(status))

        # add widgets to layout
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(dac_label, 1, 0, 1, 1)
        layout.addWidget(gain_label, 1, 1, 1, 1)
        layout.addWidget(off_label, 1, 2, 1, 1)
        layout.addWidget(self.dac, 2, 0)
        layout.addWidget(self.gain, 2, 1)
        layout.addWidget(self.off, 2, 2)
        layout.addWidget(self.lockswitch, 3, 0)
        layout.addWidget(self.calibrateswitch, 3, 1)
        layout.addWidget(self.resetswitch, 3, 2)

    def lock(self, status):
        self.resetswitch.setEnabled(status)
        self.calibrateswitch.setEnabled(status)
        self.dac.setEnabled(status)
        self.off.setEnabled(status)
        self.gain.setEnabled(status)


class AD5542_channel(QFrame):
    """
    GUI for a single AD5542 DAC channel (Fastino).
    """

    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self.setMinimumSize(200, 125)
        self.setMaximumSize(300, 200)
        self.makeLayout(name)

    def makeLayout(self, title):
        layout = QGridLayout(self)
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        dac_label = QLabel('DAC Register')

        # editable fields
        self.dac = QDoubleSpinBox()
        self.dac.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.dac.setDecimals(0)
        self.dac.setSingleStep(1)
        self.dac.setRange(0, 0xffff)
        self.dac.setKeyboardTracking(False)
        self.dac.setAlignment(Qt.AlignRight)

        # buttons
        self.resetswitch = QPushButton('Reset')
        self.resetswitch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.lockswitch = TextChangingButton(("Unlocked", "Locked"))
        self.lockswitch.toggled.connect(lambda status: self.lock(status))

        # add widgets to layout
        layout.addWidget(title,             0, 0, 1, 4)
        layout.addWidget(dac_label,         1, 0, 1, 4)
        layout.addWidget(self.dac,          2, 0, 1, 4)
        layout.addWidget(self.lockswitch,   3, 0, 1, 2)
        layout.addWidget(self.resetswitch,  3, 2, 1, 2)

    def lock(self, status):
        self.resetswitch.setEnabled(status)
        self.dac.setEnabled(status)


class DAC_gui(QFrame):
    """
    GUI for all DAC channels (i.e. a Fastino or Zotino).
    """

    name = "Fastino/Zotino GUI"

    def __init__(self, dac_list, parent=None):
        super().__init__(parent)
        self.dac_list = dac_list
        # set GUI layout
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle(self.name)
        self.makeLayout()

    def makeLayout(self):
        # create layout
        layout = QGridLayout(self)
        # set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, 4)
        # layout widgets
        for dac_name in self.dac_list.keys():
            dac_group = self._makeDACGroup(dac_name)
            layout.addWidget(dac_group)

    def _makeDACGroup(self, dac_name):
        """
        Creates a group of DAC channels as a widget.
        """
        # default gui is zotino
        channel_gui = AD5372_channel
        row_length = 5
        # get ad5372 or 5542
        if "FASTINO" in dac_name.upper():
            channel_gui = AD5542_channel
            row_length = 7
        # create widget
        zotino_group = QWidget()
        zotino_group_layout = QGridLayout(zotino_group)
        # set global elements
        zotino_header = QWidget(self)
        zotino_header_layout = QGridLayout(zotino_header)
        zotino_global_ofs_title = QLabel('Global Offset Register', zotino_header)
        self.zotino_global_ofs = QDoubleSpinBox(zotino_header)
        self.zotino_global_ofs.setMaximum(0x2fff)
        self.zotino_global_ofs.setMinimum(0)
        self.zotino_global_ofs.setDecimals(0)
        self.zotino_global_ofs.setSingleStep(1)
        self.zotino_global_ofs.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.zotino_global_ofs.setAlignment(Qt.AlignCenter)
        # lay out
        zotino_header_layout.addWidget(zotino_global_ofs_title)
        zotino_header_layout.addWidget(self.zotino_global_ofs)
        zotino_group_layout.addWidget(zotino_header, 0, 2, 1, 2)
        for i in range(32):
            # initialize GUIs for each channel
            channel_name = dac_name + '_' + str(i)
            channel_widget = channel_gui(channel_name)
            # layout channel GUI
            row = int(i / row_length) + 2
            column = i % row_length
            # add widget to client list and layout
            self.dac_list[dac_name][i] = channel_widget
            zotino_group_layout.addWidget(channel_widget, row, column)
        zotino_wrapped = QCustomGroupBox(zotino_group, dac_name)
        return zotino_wrapped


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # run AD5372 GUI
    # runGUI(AD5372_channel, name='AD5372 Channel')
    # run AD5542 GUI
    # runGUI(AD5542_channel, name='AD5542 Channel')
    # run DAC GUI
    # todo: create some tmp config
    runGUI(DAC_gui)
