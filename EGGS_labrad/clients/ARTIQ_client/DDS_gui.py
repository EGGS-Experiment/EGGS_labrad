from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox


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
        powerlabel = QLabel('Amplitude (%)')
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
        self.ampl.setDecimals(2)
        self.ampl.setSingleStep(1)
        self.ampl.setRange(0.0, 100.0)
        self.ampl.setKeyboardTracking(False)
        self.att = QDoubleSpinBox()
        self.att.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        self.att.setDecimals(1)
        self.att.setSingleStep(1)
        self.att.setRange(0, 31.5)
        self.att.setValue(31.5)
        self.att.setKeyboardTracking(False)
        self.initbutton = QPushButton('Initialize')
        self.rfswitch = TextChangingButton(("On", "Off"))
        self.lockswitch = TextChangingButton(("Unlocked", "Locked"))
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))

        # add widgets to layout
        layout.addWidget(title,                 0, 0, 1, 3)
        layout.addWidget(freqlabel,             1, 0, 1, 1)
        layout.addWidget(powerlabel,            1, 1, 1, 1)
        layout.addWidget(attlabel,              1, 2, 1, 1)
        layout.addWidget(self.freq,             2, 0)
        layout.addWidget(self.ampl,             2, 1)
        layout.addWidget(self.att,              2, 2)
        layout.addWidget(self.initbutton,       3, 0)
        layout.addWidget(self.rfswitch,         3, 1)
        layout.addWidget(self.lockswitch,       3, 2)

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

    def __init__(self, urukul_list, parent=None):
        super().__init__(parent)
        self.urukul_list = urukul_list
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
        urukul_group = QWidget()
        urukul_group_layout = QGridLayout(urukul_group)
        # add initialize button
        init_cpld = QPushButton('Initialize Board')
        urukul_group_layout.addWidget(init_cpld,        0, 0, 1, 1)
        setattr(self, '{:s}_init'.format(urukul_name), init_cpld)
        # layout individual ad9910 channels
        for channel_num, ad9910_name in enumerate(ad9910_list.keys()):
            # initialize GUIs for each channel
            channel_gui = AD9910_channel(ad9910_name)
            # layout channel GUI
            row = int(channel_num / self.row_length) + 1
            column = channel_num % self.row_length
            # add widget to client list and layout
            self.urukul_list[urukul_name][ad9910_name] = channel_gui
            urukul_group_layout.addWidget(channel_gui, row, column)
        # wrap channels in QGroupBox
        urukul_wrapped = QCustomGroupBox(urukul_group, urukul_name)
        return urukul_wrapped


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # run AD9910 GUI
    #runGUI(DDS_gui)

    # run DDS GUI
    urukul_list_tmp = {
        "urukul0_cpld": {
            "urukul0_ch0": None, "urukul0_ch1": None, "urukul0_ch2": None, "urukul0_ch3": None
        }
    }
    runGUI(DDS_gui, urukul_list_tmp)
