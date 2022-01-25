from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QDoubleSpinBox, QComboBox, QLabel, QGridLayout, QFrame, QPushButton

from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch


class PMT_gui(QFrame):
    """
    GUI for the Hamamatsu PMT via ARTIQ.
    """

    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(275, 225)
        self.makeWidgets()
        self.makeLayout()

    def makeWidgets(self):
        # title
        self.title = QLabel(self.name)
        self.title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        self.title.setAlignment(Qt.AlignCenter)
        # devices
        self.ttl_pmt_label = QLabel('PMT TTL Channel')
        self.ttl_pmt = QComboBox()
        self.ttl_trigger_label = QLabel('Trigger TTL Channel')
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
        self.edge_method.addItem('rising')
        self.edge_method.addItem('falling')
        self.edge_method.addItem('both')
        # program
        self.program_button = QPushButton('Program')
        self.start_button = QPushButton('Start')
        self.lockswitch = Lockswitch()

    def makeLayout(self):
        layout = QGridLayout()
        layout.addWidget(self.title, 0, 0, 1, 3)
        # devices
        layout.addWidget(self.ttl_pmt_label, 1, 0)
        layout.addWidget(self.ttl_trigger_label, 1, 1)
        layout.addWidget(self.trigger_active_label, 1, 2)
        layout.addWidget(self.ttl_pmt, 2, 0)
        layout.addWidget(self.ttl_trigger, 2, 1)
        layout.addWidget(self.trigger_active, 2, 2)
        # timing
        layout.addWidget(self.time_record_label, 2, 0)
        layout.addWidget(self.time_delay_label, 2, 1)
        layout.addWidget(self.time_length_label, 2, 2)
        layout.addWidget(self.time_record, 3, 0)
        layout.addWidget(self.time_delay, 3, 1)
        layout.addWidget(self.time_length, 3, 2)
        # running
        layout.addWidget(self.program_button, 4, 0)
        layout.addWidget(self.start_button, 4, 1)
        layout.addWidget(self.lockswitch, 4, 2)
        self.setLayout(layout)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(PMT_gui, name='PMT GUI')
