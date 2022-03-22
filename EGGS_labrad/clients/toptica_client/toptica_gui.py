from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QSizePolicy, QGridLayout, QGroupBox,\
                            QDesktopWidget, QPushButton, QDoubleSpinBox, QComboBox,\
                            QCheckBox, QScrollArea, QWidget, QVBoxLayout

from EGGS_labrad.clients.Widgets import TextChangingButton

SHELL_FONT = 'MS Shell Dlg 2'
LABEL_FONT = QFont(SHELL_FONT, pointSize=8)
MAIN_FONT = QFont(SHELL_FONT, pointSize=15)
DISPLAY_FONT = QFont(SHELL_FONT, pointSize=20)

#todo: record button
class toptica_channel(QFrame):
    """
    GUI for an individual Toptica Laser channel.
    """

    def __init__(self, piezoControl=True, parent=None):
        super().__init__()
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(piezoControl)

    def makeLayout(self, piezoControl):
        """
        th
        """
        # create status box
        statusBox = self._createStatusBox()
        # create piezo box
        piezoBox = QGroupBox()
        piezoBox_layout = QGridLayout(piezoBox)
        # control boxes
        tempLabels = ('Actual Temperature (K)', 'Set Temperature (K)', 'Min. Temperature (K)', 'Max. Temperature (K)')
        tempBox = self._createControlBox('Temperature Control', tempLabels)
        currLabels = ('Actual Current (mA)', 'Set Current (mA)', 'Min. Current (mA)', 'Max. Current (mA)')
        currBox = self._createControlBox('Current Control', currLabels)

        # add to self
        layout = QGridLayout(self)
        layout.minimumSize()
        layout.addWidget(statusBox,     0, 0)
        layout.addWidget(tempBox,       0, 3)
        layout.addWidget(currBox,       0, 4)
        #layout.addWidget(piezoBox,     0, 5)

    def _createStatusBox(self):
        box = QGroupBox('Laser')
        box_layout = QGridLayout(box)
        # create labels
        chanLabel = QLabel('Channel')
        freqLabel = QLabel('Center Frequency')
        serLabel = QLabel('Serial Number')
        typeLabel = QLabel('Laser Type')
        for label in (chanLabel, freqLabel, serLabel, typeLabel):
            label.setFont(LABEL_FONT)
            label.setAlignment(Qt.AlignLeft)
        # create displays
        channelDisplay = QLabel('#1')
        freqDisplay = QLabel('729.0012')
        serDisplay = QLabel('002129')
        typeDisplay = QLabel('DL Pro')
        for label in (channelDisplay, freqDisplay, serDisplay, typeDisplay):
            label.setFont(MAIN_FONT)
            label.setAlignment(Qt.AlignCenter)
        # emission
        emissionButton = TextChangingButton('Emission')
        box_layout.addWidget(chanLabel,         0, 0)
        box_layout.addWidget(channelDisplay,    1, 0)
        box_layout.addWidget(freqLabel,         2, 0)
        box_layout.addWidget(freqDisplay,       3, 0)
        box_layout.addWidget(serLabel,          4, 0)
        box_layout.addWidget(serDisplay,        5, 0)
        box_layout.addWidget(typeLabel,         6, 0)
        box_layout.addWidget(typeDisplay,       7, 0)
        box_layout.addWidget(emissionButton,    9, 0)
        return box

    def _createControlBox(self, name, label_titles):
        # create holding box
        box = QGroupBox(name)
        box_layout = QGridLayout(box)
        # create labels
        actual_label = QLabel(label_titles[0])
        set_label = QLabel(label_titles[1])
        min_label = QLabel(label_titles[2])
        max_label = QLabel(label_titles[3])
        for label in (set_label, min_label, max_label):
            label.setFont(LABEL_FONT)
            label.setAlignment(Qt.AlignLeft)
        # create display
        actualValue = QLabel('00.0000')
        actualValue.setFont(DISPLAY_FONT)
        actualValue.setAlignment(Qt.AlignCenter)
        # create boxes
        setBox = QDoubleSpinBox()
        minBox = QDoubleSpinBox()
        maxBox = QDoubleSpinBox()
        for doublespinbox in (setBox, minBox, maxBox):
            doublespinbox.setDecimals(4)
            doublespinbox.setSingleStep(0.0004)
            doublespinbox.setRange(15, 50)
            doublespinbox.setKeyboardTracking(False)
        # create lockswitch
        lockswitch = TextChangingButton(('Lock', 'Unlock'))
        # lay out
        box_layout.addWidget(actual_label,      1, 0, 1, 1)
        box_layout.addWidget(actualValue,       2, 0, 2, 1)
        box_layout.addWidget(set_label,         4, 0, 1, 1)
        box_layout.addWidget(setBox,            5, 0, 1, 1)
        box_layout.addWidget(min_label,         6, 0, 1, 1)
        box_layout.addWidget(minBox,            7, 0, 1, 1)
        box_layout.addWidget(max_label,         8, 0, 1, 1)
        box_layout.addWidget(maxBox,            9, 0, 1, 1)
        box_layout.addWidget(lockswitch,        10, 0, 1, 1)

        # todo: connect widgets and switch
        return box
            

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