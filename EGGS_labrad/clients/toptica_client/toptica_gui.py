from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QLabel, QGridLayout, QGroupBox, QScrollArea, QWidget, QSizePolicy

from EGGS_labrad.clients.utils import SHELL_FONT
from EGGS_labrad.clients.Widgets import (TextChangingButton, Lockswitch,
                                         QCustomUnscrollableSpinBox, QCustomUnscrollableComboBox)

LABEL_FONT =    QFont(SHELL_FONT, pointSize=8)
MAIN_FONT =     QFont(SHELL_FONT, pointSize=13)
DISPLAY_FONT =  QFont(SHELL_FONT, pointSize=22)
# todo: make it take up all vert space
# todo: keyboard tracking off


class toptica_channel(QFrame):
    """
    GUI for an individual Toptica Laser channel.
    """
    def __init__(self, dev_type=None, parent=None):
        super().__init__()
        self.dev_type = dev_type
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeLayout(dev_type)

    def makeLayout(self, dev_type):
        # create status box
        statusBox = self._createStatusBox()
        # control boxes
        tempLabels = ('Actual Temperature (K):', 'Set Temperature (K):', 'Min. Temperature (K):', 'Max. Temperature (K):')
        tempBox = self._createControlBox('Temperature Control', 'tempBox', tempLabels, dev_type)
        currLabels = ('Actual Current (mA):', 'Set Current (mA):', 'Min. Current (mA):', 'Max. Current (mA):')
        currBox = self._createControlBox('Current Control', 'currBox', currLabels, dev_type, controllable_max=True)
        scanBox = self._createScanBox()

        # create custom device elements
        if dev_type in ('DLpro',):
            self.statusBox.feedbackMode.addItem('Piezo')
            piezoLabels = ('Actual Voltage (V):', 'Set Voltage (V):', 'Min. Voltage (V):', 'Max. Voltage (V):')
            piezoBox = self._createControlBox('Piezo Control', 'piezoBox', piezoLabels, dev_type)
        else:
            piezoBox = QWidget()

        # lay out
        layout = QGridLayout(self)
        layout.minimumSize()
        layout.addWidget(statusBox, 0, 0)
        layout.addWidget(scanBox,   0, 1)
        layout.addWidget(currBox,   0, 2)
        layout.addWidget(tempBox,   0, 3)
        layout.addWidget(piezoBox,  0, 4)

    def _createStatusBox(self):
        box = QWidget()
        box_layout = QGridLayout(box)
        # create labels
        chanLabel = QLabel('Channel:')
        wavLabel = QLabel('Center Wavelength (nm):')
        serLabel = QLabel('Serial Number:')
        for label in (chanLabel, wavLabel, serLabel):
            label.setFont(LABEL_FONT)
            label.setAlignment(Qt.AlignBottom)
        # create displays
        box.channelDisplay = QLabel('1')
        box.wavDisplay = QLabel('854.441')
        box.serDisplay = QLabel('002129')
        for label in (box.channelDisplay, box.wavDisplay, box.serDisplay):
            label.setFont(MAIN_FONT)
            label.setAlignment(Qt.AlignCenter)
        # emission enabled
        box.enabledButton = TextChangingButton('Enabled')
        # create labels
        feedback_label = QLabel('Feedback Channel:')
        feedbackMode_label = QLabel('Feedback Mode:')
        feedbackFactor_label = QLabel('Feedback Factor:')
        for label in (feedback_label, feedbackMode_label, feedbackFactor_label):
            label.setFont(LABEL_FONT)
            label.setAlignment(Qt.AlignBottom)
        # feedback
        box.feedbackFactor = QCustomUnscrollableSpinBox()
        box.feedbackFactor.setDecimals(4)
        box.feedbackFactor.setSingleStep(0.0001)
        box.feedbackFactor.setRange(0, 200)
        box.feedbackFactor.setKeyboardTracking(False)
        box.feedbackFactor.setFont(QFont(SHELL_FONT, pointSize=10))
        box.feedbackChannel = QCustomUnscrollableComboBox()
        box.feedbackChannel.setFont(QFont(SHELL_FONT, pointSize=10))
        box.feedbackChannel.addItems(['Off', 'Fine In 1', 'Fine In 2', 'Fast In 3', 'Fast In 4'])
        box.feedbackMode = QCustomUnscrollableComboBox()
        box.feedbackMode.addItems(['Current', 'Temperature'])
        box.feedbackMode.setFont(QFont(SHELL_FONT, pointSize=10))
        # lay out
        box_layout.addWidget(chanLabel,                 0, 0)
        box_layout.addWidget(box.channelDisplay,        1, 0)
        box_layout.addWidget(wavLabel,                  2, 0)
        box_layout.addWidget(box.wavDisplay,            3, 0)
        box_layout.addWidget(serLabel,                  4, 0)
        box_layout.addWidget(box.serDisplay,            5, 0)
        box_layout.addWidget(box.enabledButton,         6, 0)
        box_layout.addWidget(feedback_label,            7, 0)
        box_layout.addWidget(box.feedbackChannel,       8, 0)
        box_layout.addWidget(feedbackMode_label,        9, 0)
        box_layout.addWidget(box.feedbackMode,          10, 0)
        box_layout.addWidget(feedbackFactor_label,      12, 0)
        box_layout.addWidget(box.feedbackFactor,        12, 0)
        box_layout.minimumSize()
        # set self attribute and create wrapper
        setattr(self, 'statusBox', box)
        return self._wrapGroup('Status', box)

    def _createControlBox(self, name, objName, label_titles, dev_type, controllable_max=False):
        # create holding box
        box = QWidget()
        box_layout = QGridLayout(box)
        # create labels
        actual_label = QLabel(label_titles[0])
        set_label = QLabel(label_titles[1])
        min_label = QLabel(label_titles[2])
        max_label = QLabel(label_titles[3])
        for label in (set_label, min_label, max_label):
            label.setFont(LABEL_FONT)
            label.setAlignment(Qt.AlignBottom)

        # create boxes
        box.setBox = QCustomUnscrollableSpinBox()
        box.actualValue = QLabel('00.0000')
        box.minBox = QLabel('00.0000')
        # create lists of boxes for programmatic instantiation
        spinbox_list = [box.setBox]
        display_list = [box.actualValue, box.minBox]
        if controllable_max:
            box.maxBox = QCustomUnscrollableSpinBox()
            spinbox_list.append(box.maxBox)
        else:
            box.maxBox = QLabel('00.0000')
            display_list.append(box.maxBox)
        # create display
        for display_box in display_list:
            display_box.setFont(DISPLAY_FONT)
            display_box.setAlignment(Qt.AlignRight)
        # customize spinboxes
        for doublespinbox in spinbox_list:
            doublespinbox.setDecimals(4)
            doublespinbox.setSingleStep(0.0001)
            if dev_type == 'BoosTApro':
                doublespinbox.setRange(5, 1100)
            else:
                doublespinbox.setRange(5, 200)
            doublespinbox.setKeyboardTracking(False)
            doublespinbox.setFont(QFont(SHELL_FONT, pointSize=10))

        # create buttons
        box.lockswitch = Lockswitch()
        box.record_button = TextChangingButton(('Stop Recording', 'Record'))

        # lay out
        box_layout.addWidget(actual_label,          0, 0, 1, 1)
        box_layout.addWidget(box.actualValue,       1, 0, 1, 1)
        box_layout.addWidget(box.record_button,     2, 0, 1, 1)
        box_layout.addWidget(set_label,             3, 0, 1, 1)
        box_layout.addWidget(box.setBox,            4, 0, 1, 1)
        box_layout.addWidget(min_label,             5, 0, 1, 1)
        box_layout.addWidget(box.minBox,            6, 0, 1, 1)
        box_layout.addWidget(max_label,             7, 0, 1, 1)
        box_layout.addWidget(box.maxBox,            8, 0, 1, 1)
        box_layout.addWidget(box.lockswitch,        9, 0, 1, 1)
        box_layout.minimumSize()

        # connect signals to slots
        box.lockswitch.toggled.connect(lambda status, parent=objName: self._lock(status, parent))
        box.lockswitch.setChecked(True)
        # create QGroupBox wrapper
        setattr(self, objName, box)
        return self._wrapGroup(name, box)

    def _createScanBox(self):
        box = QWidget()
        box_layout = QGridLayout(box)
        # create labels
        mode_label = QLabel('Scan Mode:')
        shape_label = QLabel('Scan Shape:')
        freq_label = QLabel('Scan Frequency (Hz):')
        amp_label = QLabel('Scan Amplitude (arb.):')
        off_label = QLabel('Scan Offset (arb.):')
        for label in (mode_label, shape_label, freq_label, amp_label, off_label):
            label.setFont(LABEL_FONT)
            label.setAlignment(Qt.AlignBottom)
        # create lockswitch
        box.lockswitch = Lockswitch()
        box.lockswitch.toggled.connect(lambda status: self._scanlock(status, 'scanBox'))
        #box.lockswitch.setChecked(True)
        # create comboboxes
        box.modeBox = QCustomUnscrollableComboBox()
        box.modeBox.addItems(['Current', 'Temperature'])
        box.modeBox.addItem('Temperature')
        box.shapeBox = QCustomUnscrollableComboBox()
        box.shapeBox.addItems(['Triangle', 'Sine'])
        # create doublespinboxes
        box.freqBox = QCustomUnscrollableSpinBox()
        box.ampBox = QCustomUnscrollableSpinBox()
        box.offBox = QCustomUnscrollableSpinBox()
        for doublespinbox in (box.freqBox, box.ampBox, box.offBox):
            doublespinbox.setDecimals(4)
            doublespinbox.setSingleStep(0.0001)
            doublespinbox.setRange(0, 200)
            doublespinbox.setKeyboardTracking(False)
            doublespinbox.setFont(QFont(SHELL_FONT, pointSize=10))
        # lay out
        box_layout.addWidget(mode_label,        0, 0, 1, 1)
        box_layout.addWidget(box.modeBox,       1, 0, 1, 1)
        box_layout.addWidget(shape_label,       2, 0, 1, 1)
        box_layout.addWidget(box.shapeBox,      3, 0, 1, 1)
        box_layout.addWidget(freq_label,        4, 0, 1, 1)
        box_layout.addWidget(box.freqBox,       5, 0, 1, 1)
        box_layout.addWidget(amp_label,         6, 0, 1, 1)
        box_layout.addWidget(box.ampBox,        7, 0, 1, 1)
        box_layout.addWidget(off_label,         8, 0, 1, 1)
        box_layout.addWidget(box.offBox,        9, 0, 1, 1)
        box_layout.addWidget(box.lockswitch,    10, 0, 1, 1)
        box_layout.minimumSize()
        setattr(self, 'scanBox', box)
        return self._wrapGroup('Scan Control', box)

    def _wrapGroup(self, name, widget):
        wrapper = QGroupBox(name)
        wrapper_layout = QGridLayout(wrapper)
        wrapper_layout.addWidget(widget)
        return wrapper

    def _lock(self, status, objName):
        parent = getattr(self, objName)
        parent.setBox.setEnabled(status)
        parent.minBox.setEnabled(status)
        parent.maxBox.setEnabled(status)

    def _scanlock(self, status, objName):
        parent = getattr(self, objName)
        parent.modeBox.setEnabled(status)
        parent.shapeBox.setEnabled(status)
        parent.freqBox.setEnabled(status)
        parent.ampBox.setEnabled(status)
        parent.offBox.setEnabled(status)


class toptica_gui(QFrame):
    """
    The full Toptica GUI.
    """
    def __init__(self, channelinfo=None):
        super().__init__()
        self.channels = {}
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle('Toptica GUI')
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)

    def makeLayout(self, channelinfo):
        layout = QGridLayout(self)
        # scrollable holder for laser channels
        wm_scroll = QScrollArea()
        wm_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        wmChan_widget = QWidget()
        wmChan_layout = QGridLayout(wmChan_widget)

        # batch create constituent channel GUIs
        for idx, vals in enumerate(channelinfo):
            chan_num, dev_type = vals[0], vals[2]
            channel_gui = toptica_channel(dev_type=dev_type)
            self.channels[chan_num] = channel_gui
            wmChan_layout.addWidget(channel_gui, idx, 0, 1, 1)

        # add wavemeter channel holder to qBox
        wm_scroll.setWidget(wmChan_widget)
        wm_scroll.setFixedWidth(wmChan_widget.sizeHint().width() - 3)
        # add title
        title = QLabel('Toptica Client')
        title.setFont(QFont(SHELL_FONT, pointSize=18))
        title.setAlignment(Qt.AlignCenter)
        title.setMaximumHeight(40)
        # final layout
        layout.addWidget(title,         1, 0, 1, 1)
        layout.addWidget(wm_scroll,     2, 0, 1, 1)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # # run toptica channel gui
    # runGUI(toptica_channel)

    # run toptica client gui
    runGUI(toptica_gui)
