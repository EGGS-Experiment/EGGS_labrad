from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QWidget, QVBoxLayout, QComboBox, QGridLayout

from EGGS_labrad.clients.utils import SHELL_FONT
from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox, QCustomUnscrollableSpinBox


class lakeshore336_gui(QFrame):
    """
    GUI for the lakeshore 336 temperature controller.
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(500, 400)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("Lakeshore 336 Client")
        self.makeLayout()

    def _makeTemperatureWidget(self):
        temp_widget = QWidget()
        temp_layout = QVBoxLayout(temp_widget)

        temp1_label = QLabel("Diode 1 (K)")
        temp2_label = QLabel("Diode 2 (K)")
        temp3_label = QLabel("Diode 3 (K)")
        temp4_label = QLabel("Diode 4 (K)")
        self.temp1 = QLabel("000.0000")
        self.temp2 = QLabel("000.0000")
        self.temp3 = QLabel("000.0000")
        self.temp4 = QLabel("000.0000")

        self.tempAll_record = TextChangingButton(('Stop Recording', 'Start Recording'))
        temp_layout.addWidget(self.tempAll_record)

        for widget in (self.temp1, self.temp2, self.temp3, self.temp4):
            widget.setAlignment(Qt.AlignRight)
            widget.setFont(QFont(SHELL_FONT, pointSize=24))
            widget.setStyleSheet('color: blue')

        for widget in (temp1_label, self.temp1, temp2_label, self.temp2,
                       temp3_label, self.temp3, temp4_label, self.temp4):
            temp_layout.addWidget(widget)
        return QCustomGroupBox(temp_widget, "Temperature Readout")

    def _makeHeaterWidget(self):
        # heater 1
        heater1_widget = QWidget()
        heater1_layout = QVBoxLayout(heater1_widget)

        heat1_range_label = QLabel("Output Range (%)")
        self.heat1_range = QComboBox()
        self.heat1_range.addItems(["Off", "1", "10", "100"])
        self.heat1_range.setFont(QFont(SHELL_FONT, pointSize=12))

        heat1_res_label = QLabel("Resistance (\u03A9)")
        self.heat1_res = QComboBox()
        self.heat1_res.addItems(["25", "50"])
        self.heat1_res.setFont(QFont(SHELL_FONT, pointSize=12))

        heat1_curr_label = QLabel("Max. Curr. (A)")
        self.heat1_curr = QCustomUnscrollableSpinBox()
        self.heat1_curr.setFont(QFont(SHELL_FONT, pointSize=12))

        heat1_p1_label = QLabel("Curr. (% max)")
        self.heat1_p1 = QCustomUnscrollableSpinBox()
        self.heat1_p1.setRange(0, 300.0)
        self.heat1_p1.setFont(QFont(SHELL_FONT, pointSize=12))

        for widget in (heat1_range_label, self.heat1_range, heat1_res_label, self.heat1_res,
                       heat1_curr_label, self.heat1_curr, heat1_p1_label, self.heat1_p1):
            heater1_layout.addWidget(widget)


        # heater 2
        heater2_widget = QWidget()
        heater2_layout = QVBoxLayout(heater2_widget)

        heat2_range_label = QLabel("Output Range")
        self.heat2_range = QComboBox()
        self.heat2_range.addItems(["Off", "1", "10", "100"])
        self.heat2_range.setFont(QFont(SHELL_FONT, pointSize=12))

        heat2_res_label = QLabel("Resistance (\u03A9)")
        self.heat2_res = QComboBox()
        self.heat2_res.addItems(["25", "50"])
        self.heat2_res.setFont(QFont(SHELL_FONT, pointSize=12))

        heat2_curr_label = QLabel("Max. Curr. (A)")
        self.heat2_curr = QCustomUnscrollableSpinBox()
        self.heat2_curr.setFont(QFont(SHELL_FONT, pointSize=12))

        heat2_p1_label = QLabel("Curr. (% max)")
        self.heat2_p1 = QCustomUnscrollableSpinBox()
        self.heat2_p1.setRange(0, 300.0)
        self.heat2_p1.setFont(QFont(SHELL_FONT, pointSize=12))

        for widget in (heat2_range_label, self.heat2_range, heat2_res_label, self.heat2_res,
                       heat2_curr_label, self.heat2_curr, heat2_p1_label, self.heat2_p1):
            heater2_layout.addWidget(widget)

        # create heater holder
        heater1_widget_wrapped = QCustomGroupBox(heater1_widget, "Heater 1")
        heater2_widget_wrapped = QCustomGroupBox(heater2_widget, "Heater 2")
        self.heatAll_lockswitch = TextChangingButton(('Locked', 'Unlocked'))

        heaterAll_widget = QWidget()
        heaterAll_layout = QGridLayout(heaterAll_widget)
        heaterAll_layout.addWidget(self.heatAll_lockswitch, 0, 1, 1, 2)
        heaterAll_layout.addWidget(heater1_widget_wrapped,  1, 0, 4, 2)
        heaterAll_layout.addWidget(heater2_widget_wrapped,  1, 2, 4, 2)
        return QCustomGroupBox(heaterAll_widget, "Heater Control")

    def makeLayout(self):
        layout = QGridLayout(self)

        # title
        title = QLabel("Lakeshore 336 Client")
        title.setFont(QFont('MS Shell Dlg 2', pointSize=20))
        title.setAlignment(Qt.AlignCenter)

        # make widgets
        temperature_widget = self._makeTemperatureWidget()
        heater_widget_wrapped = self._makeHeaterWidget()

        # lay out
        layout.addWidget(title,                 0, 0, 1, 8)
        layout.addWidget(temperature_widget,    1, 0, 9, 4)
        layout.addWidget(heater_widget_wrapped, 1, 4, 9, 4)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(lakeshore336_gui)
