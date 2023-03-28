from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QDoubleSpinBox, QLabel, QGridLayout, QFrame, QPushButton, QWidget, QVBoxLayout, QRadioButton

from EGGS_labrad.clients.Widgets import TextChangingButton, Lockswitch, QCustomARTIQMonitor


class PMT_gui(QFrame):
    """
    GUI for the Hamamatsu PMT via ARTIQ.
    """

    def __init__(self, name=None, parent=None):
        super().__init__()
        self.name = 'PMT Client'
        self.parent = parent
        self.setFrameStyle(0x0001 | 0x0030)
        self.setFixedSize(300, 350)
        self.makeWidgets()
        self.makeLayout()
        self.show()

    def makeWidgets(self):
        # general
        self.setWindowTitle(self.name)
        self.lockswitch = Lockswitch()
        self.read_once_switch = QPushButton("Read Once")
        self.read_once_switch.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        self.read_cont_switch = TextChangingButton(("Stop", "Loop"))
        self.title = QLabel(self.name)
        self.title.setFont(QFont('MS Shell Dlg 2', pointSize=15))
        self.title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        # create artiq experiment monitor
        self.artiq_monitor = QCustomARTIQMonitor(self)

        # display
        self.count_display_label = QLabel("Counts")
        self.count_display_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.count_display = QLabel("0.000")
        self.count_display.setStyleSheet('color: red')
        self.count_display.setFont(QFont('MS Shell Dlg 2', pointSize=17))
        self.count_display.setAlignment(Qt.AlignCenter)

        # sample time
        self.sample_time_label = QLabel('Sample Time (us)')
        self.sample_time = QDoubleSpinBox()
        self.sample_time.setMinimum(1)
        self.sample_time.setMaximum(5000000)
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

        # create radio buttons
        self.std_widget = QWidget()
        self.sample_std_on = QRadioButton("On")
        self.sample_std_off = QRadioButton("Off")
        self.sample_std_off.setChecked(True)
        std_widget_layout = QVBoxLayout(self.std_widget)
        std_widget_layout.addWidget(QLabel("Std. Dev."))
        std_widget_layout.addWidget(self.sample_std_on)
        std_widget_layout.addWidget(self.sample_std_off)

        # polling
        self.poll_interval_label = QLabel('Poll Interval (s)')
        self.poll_interval = QDoubleSpinBox()
        self.poll_interval.setMinimum(.01)
        self.poll_interval.setMaximum(600)
        self.poll_interval.setSingleStep(1)
        self.poll_interval.setDecimals(1)
        self.poll_interval.setAlignment(Qt.AlignRight)
        self.poll_interval.setFont(QFont('MS Shell Dlg 2', pointSize=12))

        # record
        self.record_button = TextChangingButton(("Stop Recording", "Start Recording"))

        # grant's magic button
        self.quick_check = QPushButton("Quick Check")

        # Grant's real magic button a.k.a. flipper
        self.flip = QPushButton("Flip")
        self.flip.setFont(QFont('MS Shell Dlg 2', pointSize=10))


    def makeLayout(self):
        layout = QGridLayout(self)
        layout.addWidget(self.title,                    0, 0, 1, 2)
        layout.addWidget(self.artiq_monitor,            0, 2, 1, 1)
        # displays
        layout.addWidget(self.count_display_label,      3, 0, 1, 1)
        layout.addWidget(self.std_widget,               3, 2, 2, 1)
        layout.addWidget(self.count_display,            4, 0, 3, 2)
        # timing
        layout.addWidget(self.sample_time_label,        7, 0)
        layout.addWidget(self.sample_num_label,         7, 1)
        layout.addWidget(self.poll_interval_label,      7, 2)
        layout.addWidget(self.sample_time,              8, 0)
        layout.addWidget(self.sample_num,               8, 1)
        layout.addWidget(self.poll_interval,            8, 2)
        # running
        layout.addWidget(self.read_once_switch,         9, 0)
        layout.addWidget(self.read_cont_switch,         9, 1)
        layout.addWidget(self.lockswitch,               9, 2)
        # flipper integration
        layout.addWidget(self.flip,                     10, 0)
        # recording
        layout.addWidget(self.record_button,            10, 1)


    def stdToggle(self, status):
        """
        Changes display to include standard deviation.
        """
        if status:
            pass
        else:
            pass

    def closeEvent(self, event):
        if self.parent is not None:
            self.parent.close()


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(PMT_gui)
