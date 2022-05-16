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
        self.setFixedSize(300, 200)
        self.makeWidgets()
        self.makeLayout()
        self.show()

    def makeWidgets(self):
        # self.setStyleSheet("background-color: gray;")
        self.setWindowTitle(self.name)
        # title
        self.title = QLabel(self.name)
        self.title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.title.setAlignment(Qt.AlignCenter)
        # devices
        self.ttl_pmt_label = QLabel('PMT Channel')
        self.ttl_pmt = QComboBox()
        self.ttl_trigger_label = QLabel('Trigger Channel')
        self.ttl_trigger = QComboBox()
        self.trigger_active_label = QLabel('Trigger Status')
        self.trigger_active = TextChangingButton(('Active', 'Inactive'))
        # record time
        self.time_record_label = QLabel('Record Time (us)')
        self.time_record = QDoubleSpinBox()
        self.time_record.setMinimum(1)
        self.time_record.setMaximum(10000)
        self.time_record.setSingleStep(1)
        self.time_record.setDecimals(0)
        # delay time
        self.time_delay_label = QLabel('Delay Time (us)')
        self.time_delay = QDoubleSpinBox()
        self.time_delay.setMinimum(1)
        self.time_delay.setMaximum(10000)
        self.time_delay.setSingleStep(1)
        self.time_delay.setDecimals(0)
        # record length
        self.time_length_label = QLabel('Record Length (us)')
        self.time_length = QDoubleSpinBox()
        self.time_length.setMinimum(10)
        self.time_length.setMaximum(100000)
        self.time_length.setSingleStep(1)
        self.time_length.setDecimals(0)
        # edge method
        self.edge_method_label = QLabel('Edge Type')
        self.edge_method = QComboBox()
        self.edge_method.addItems(['rising', 'falling', 'both'])
        # program
        self.program_button = QPushButton('Program')
        self.start_button = QPushButton('Start')
        self.lockswitch = Lockswitch()

    def makeLayout(self):
        # todo: add power TTL
        layout = QGridLayout(self)
        self.header = QClientMenuHeader()
        layout.setMenuBar(self.header)
        layout.addWidget(self.title,                    1, 0, 1, 3)
        # devices
        layout.addWidget(self.ttl_pmt_label,            2, 0)
        layout.addWidget(self.ttl_trigger_label,        2, 1)
        layout.addWidget(self.trigger_active_label,     2, 2)
        layout.addWidget(self.ttl_pmt,                  3, 0)
        layout.addWidget(self.ttl_trigger,              3, 1)
        layout.addWidget(self.trigger_active,           3, 2)
        # timing
        layout.addWidget(self.time_record_label,        4, 0)
        layout.addWidget(self.time_delay_label,         4, 1)
        layout.addWidget(self.time_length_label,        4, 2)
        layout.addWidget(self.time_record,              5, 0)
        layout.addWidget(self.time_delay,               5, 1)
        layout.addWidget(self.time_length,              5, 2)
        # running
        layout.addWidget(self.start_button,             6, 0)
        layout.addWidget(self.program_button,           6, 1)
        layout.addWidget(self.lockswitch,               6, 2)

    def closeEvent(self, event):
        if self.parent is not None:
            self.parent.close()


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(PMT_gui)
