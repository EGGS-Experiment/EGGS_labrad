from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from EGGS_labrad.config.device_db import device_db
from EGGS_labrad.clients.Widgets import TextChangingButton


class AD9910_channel(QFrame):
    """
    GUI for a single AD9910 DDS channel.
    """

    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(name)
        self.setMaximumSize(300, 150)

    def makeLayout(self, title):
        layout = QGridLayout(self)
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        title.setAlignment(Qt.AlignCenter)
        freqlabel = QLabel('Frequency (MHz)')
        powerlabel = QLabel('Amplitude (V)')
        attlabel = QLabel('Attenuation (dBm)')

        # editable fields
        self.freq = QDoubleSpinBox()
        self.freq.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        self.freq.setDecimals(3)
        self.freq.setSingleStep(0.001)
        self.freq.setRange(0.0, 400.0)
        self.freq.setKeyboardTracking(False)
        self.ampl = QDoubleSpinBox()
        self.ampl.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        self.ampl.setDecimals(3)
        self.ampl.setSingleStep(0.1)
        self.ampl.setRange(-145.0, 30.0)
        self.ampl.setKeyboardTracking(False)
        self.att = QDoubleSpinBox()
        self.att.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        self.att.setDecimals(3)
        self.att.setSingleStep(0.1)
        self.att.setRange(-145.0, 30.0)
        self.att.setKeyboardTracking(False)
        self.resetswitch = QPushButton('Initialize')
        self.rfswitch = TextChangingButton(("On", "Off"))
        self.lockswitch = TextChangingButton(("Unlocked", "Locked"))
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))

        # add widgets to layout
        layout.addWidget(title, 0, 0, 1, 3)
        layout.addWidget(freqlabel, 1, 0, 1, 1)
        layout.addWidget(powerlabel, 1, 1, 1, 1)
        layout.addWidget(attlabel, 1, 2, 1, 1)
        layout.addWidget(self.freq, 2, 0)
        layout.addWidget(self.ampl, 2, 1)
        layout.addWidget(self.att, 2, 2)
        layout.addWidget(self.resetswitch, 3, 0)
        layout.addWidget(self.rfswitch, 3, 1)
        layout.addWidget(self.lockswitch, 3, 2)

    def lock(self, status):
        self.freq.setEnabled(status)
        self.ampl.setEnabled(status)
        self.att.setEnabled(status)
        self.rfswitch.setEnabled(status)


class DDS_gui(QFrame):
    """
    GUI for all DDS boards and channels.
    """
    name = "ARTIQ DDS Client"
    row_length = 4

    def __init__(self, ddb=device_db, name=None, parent=None):
        super().__init__()
        self.ddb = ddb
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle(self.name)
        # device dictionaries
        self.urukul_list = {}
        self.ad9910_clients = {}
        # start GUI
        self.getDevices()
        self.makeLayout()

    def getDevices(self):
        # get devices
        for name, params in self.ddb.items():
            if 'class' not in params:
                continue
            elif params['class'] == 'CPLD':
                self.urukul_list[name] = {}
            elif params['class'] == 'AD9910':
                # assign ad9910 channels to urukuls
                urukul_name = params["arguments"]["cpld_device"]
                if urukul_name not in self.urukul_list:
                    self.urukul_list[urukul_name] = {}
                self.urukul_list[urukul_name][name] = None
                self.ad9910_clients[name] = None

    def makeLayout(self):
        # create layout
        layout = QGridLayout(self)
        # set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, self.row_length)
        # layout urukuls
        urukul_iter = iter(range(len(self.urukul_list)))
        for urukul_name, ad9910_list in self.urukul_list.items():
            urukul_num = next(urukul_iter)
            # create urukul widget
            urukul_group = self._makeUrukulGroup(urukul_name, ad9910_list)
            layout.addWidget(urukul_group, 2 + urukul_num, 0, 1, self.row_length)

    def _makeUrukulGroup(self, urukul_name, ad9910_list):
        """
        Creates a group of Urukul channels as a widget.
        """
        # create widget
        urukul_group = QFrame()
        urukul_group.setFrameStyle(0x0001 | 0x0010)
        urukul_group.setLineWidth(2)
        layout = QGridLayout(urukul_group)
        # set title
        title = QLabel(urukul_name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0, 1, self.row_length)
        # iterator so we don't have to do a for-range loop
        channel_iter = iter([0, 1, 2, 3])
        # layout individual ad9910 channels
        for ad9910_name in ad9910_list.keys():
            # initialize GUIs for each channel
            channel_num = next(channel_iter)
            channel_gui = AD9910_channel(ad9910_name)
            # layout channel GUI
            row = int(channel_num / self.row_length) + 2
            column = channel_num % self.row_length
            # add widget to client list and layout
            self.urukul_list[urukul_name][ad9910_name] = channel_gui
            layout.addWidget(channel_gui, row, column)
            # print(name + ' - row:' + str(row) + ', column: ' + str(column))
        return urukul_group


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # run AD9910 GUI
    #runGUI(DDS_gui)

    # run DDS GUI
    runGUI(DDS_gui)
