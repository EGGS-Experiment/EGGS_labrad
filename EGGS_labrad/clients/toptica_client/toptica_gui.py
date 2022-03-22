from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QSizePolicy, QGridLayout, QGroupBox,\
                            QDesktopWidget, QPushButton, QDoubleSpinBox, QComboBox,\
                            QCheckBox, QScrollArea, QWidget, QVBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton


#todo: record button
class toptica_channel(QFrame):
    """
    GUI for an individual Toptica Laser channel.
    """

    def __init__(self, piezoControl=True, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        yz1 = self._createTempBox()
        th1 = QGridLayout(self)
        th1.addWidget(yz1, 0,0)
        #self.makeLayout(piezoControl)

    def makeLayout(self, name, piezoControl):
        """
        th
        """
        shell_font = 'MS Shell Dlg 2'
        display_font = QFont(shell_font, pointSize=16)
        label_font = QFont(shell_font, pointSize=10)

        # create holder widgets
        statusBox = QGroupBox()
        statusBox_layout = QGridLayout(statusBox)
        currBox = QGroupBox()
        currBox_layout = QGridLayout(currBox)
        tempBox = QGroupBox()
        tempBox_layout = QGridLayout(tempBox)
        piezoBox = QGroupBox()
        piezoBox_layout = QGridLayout(piezoBox)

        # current
        self.curr_actual = QLabel()
        self.curr_actual.setAlignment

        # add to self
        layout = QGridLayout(self)
        layout.minimumSize()
        layout.addWidget(statusBox)
        layout.addWidget(tempBox)
        layout.addWidget(currBox)
        layout.addWidget(piezoBox)

    def _createTempBox(self):
        shell_font = 'MS Shell Dlg 2'
        display_font = QFont(shell_font, pointSize=16)
        label_font = QFont(shell_font, pointSize=10)

        tempBox = QGroupBox('Temperature Control')
        tempBox_layout = QGridLayout(tempBox)

        self.temp_actual = QLabel('')
        self.temp_actual.setFont(display_font)
        self.temp_actual.setAlignment(Qt.AlignCenter)

        tempSet_label = QLabel('Set Current (mA)')
        tempMin_label = QLabel('Min Current (mA)')
        tempMax_label = QLabel('Max Current (mA)')
        for label in (tempSet_label, tempMin_label, tempMax_label):
            label.setFont(label_font)
            label.setAlignment(Qt.AlignLeft)
        
        self.tempSetBox = QDoubleSpinBox()
        self.tempMinBox = QDoubleSpinBox()
        self.tempMaxBox = QDoubleSpinBox()
        for doublespinbox in (self.tempSetBox, self.tempMinBox, self.tempMaxBox):
            doublespinbox.setDecimals(4)
            doublespinbox.setSingleStep(0.0004)
            doublespinbox.setRange(15, 50)
            doublespinbox.setKeyboardTracking(False)

        tempBox_layout.addWidget(self.temp_actual,      0, 0, 2, 1)
        tempBox_layout.addWidget(tempSet_label,         1, 0, 1, 1)
        tempBox_layout.addWidget(self.tempSetBox,       2, 0, 1, 1)
        tempBox_layout.addWidget(tempMin_label,         3, 0, 1, 1)
        tempBox_layout.addWidget(self.tempMinBox,       4, 0, 1, 1)
        tempBox_layout.addWidget(tempMax_label,         5, 0, 1, 1)
        tempBox_layout.addWidget(self.tempMaxBox,       6, 0, 1, 1)

        return tempBox

            

class toptica_gui():
    """

    """


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # run toptica channel gui
    runGUI(toptica_channel)

    # run toptica client gui
    # from EGGS_labrad.config.multiplexerclient_config import multiplexer_config
    # runGUI(multiplexer_gui, multiplexer_config.channels)