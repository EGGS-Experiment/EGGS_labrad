from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDoubleSpinBox, QComboBox, QLabel, QGridLayout, QFrame, QPushButton

from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QClientMenuHeader


class PMT_gui(QFrame):
    """
    GUI for the Hamamatsu PMT via ARTIQ.
    """

    def __init__(self, name=None, parent=None):
        super().__init__()
        self.name = 'PMT Client'
        self.parent = parent
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(300, 250)
        self.makeWidgets()
        self.makeLayout()
        self.show()

    def makeWidgets(self):
        # general
        self.setWindowTitle(self.name)
        self.lockswitch = Lockswitch()
        self.read_once_switch = QPushButton("Read Once")
        self.read_once_switch.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        self.read_cont_switch = TextChangingButton(("Read Continuously", "Stop"))
        self.title = QLabel(self.name)
        self.title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        self.title.setAlignment(Qt.AlignCenter)
        # display
        self.count_display_label = QLabel("Counts")
        self.count_display_label.setAlignment(Qt.AlignLeft)
        self.count_display = QLabel("0.00")
        self.count_display.setStyleSheet('color: blue')
        self.count_display.setFont(QFont('MS Shell Dlg 2', pointSize=30))
        self.count_display.setAlignment(Qt.AlignCenter)
        # todo: record button
        # sample time
        self.sample_time_label = QLabel('Sample Time (us)')
        self.sample_time = QDoubleSpinBox()
        self.sample_time.setMinimum(1)
        self.sample_time.setMaximum(10000)
        self.sample_time.setSingleStep(1)
        self.sample_time.setDecimals(0)
        self.sample_time.setAlignment(Qt.AlignRight)
        self.sample_time.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        # number of samples
        self.sample_num_label = QLabel('Number of Samples')
        self.sample_num = QDoubleSpinBox()
        self.sample_num.setMinimum(1)
        self.sample_num.setMaximum(10000)
        self.sample_num.setSingleStep(1)
        self.sample_num.setDecimals(0)
        self.sample_num.setAlignment(Qt.AlignRight)
        self.sample_num.setFont(QFont('MS Shell Dlg 2', pointSize=12))
        # polling
        self.poll_interval_label = QLabel('Poll Interval (s)')
        self.poll_interval = QDoubleSpinBox()
        self.poll_interval.setMinimum(2)
        self.poll_interval.setMaximum(20)
        self.poll_interval.setSingleStep(1)
        self.poll_interval.setDecimals(1)
        self.poll_interval.setAlignment(Qt.AlignRight)
        self.poll_interval.setFont(QFont('MS Shell Dlg 2', pointSize=12))

    def makeLayout(self):
        layout = QGridLayout(self)
        self.header = QClientMenuHeader()
        layout.setMenuBar(self.header)
        layout.addWidget(self.title,                    0, 0, 1, 3)
        # devices
        layout.addWidget(self.count_display_label,      3, 1, 1, 1)
        layout.addWidget(self.count_display,            4, 0, 4, 3)
        # timing
        layout.addWidget(self.sample_time_label,        8, 0)
        layout.addWidget(self.sample_num_label,         8, 1)
        layout.addWidget(self.poll_interval_label,      8, 2)
        layout.addWidget(self.sample_time,              9, 0)
        layout.addWidget(self.sample_num,               9, 1)
        layout.addWidget(self.poll_interval,            9, 2)
        # running
        layout.addWidget(self.read_once_switch,         10, 0)
        layout.addWidget(self.read_cont_switch,         10, 1)
        layout.addWidget(self.lockswitch,               10, 2)

    def closeEvent(self, event):
        if self.parent is not None:
            self.parent.close()


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(PMT_gui)
