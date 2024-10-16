from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QFrame, QLabel, QGridLayout, QPushButton, QVBoxLayout

from EGGS_labrad.clients.utils import SHELL_FONT
from EGGS_labrad.clients.Widgets import Lockswitch, TextChangingButton, QCustomGroupBox, QCustomUnscrollableSpinBox


class RF_gui(QFrame):
    """
    GUI for the trap RF signal generator.
    """

    def __init__(self):
        super().__init__()
        self.setFixedSize(200, 300)
        self.setFrameStyle(0x0001 | 0x0030)
        self.setWindowTitle("RF Client")
        self.makeLayout()

    def _makeWaveformWidget(self):
        """
        Create general waveform widget.
        """
        waveform_widget = QWidget()
        waveform_layout = QGridLayout(waveform_widget)
        waveform_layout.setContentsMargins(0, 0, 0, 0)

        self.wav_toggle = TextChangingButton(('On', 'Off'), fontsize=11)
        self.wav_lockswitch = Lockswitch()
        self.wav_lockswitch.setFont(QFont(SHELL_FONT, pointSize=11))

        wav_freq_label = QLabel("Frequency (MHz)")
        wav_freq_label.setFont(QFont(SHELL_FONT, pointSize=10))
        self.wav_freq = QCustomUnscrollableSpinBox()
        self.wav_freq.setDecimals(6)
        self.wav_freq.setRange(0.009, 1040.0)
        self.wav_freq.setSingleStep(0.001)
        self.wav_freq.setProperty("value", 9.0)
        self.wav_freq.setKeyboardTracking(False)
        self.wav_freq.setFont(QFont(SHELL_FONT, pointSize=14))
        self.wav_freq.setAlignment(Qt.AlignRight)

        wav_ampl_label = QLabel("Amplitude (dBm)")
        wav_ampl_label.setFont(QFont(SHELL_FONT, pointSize=10))
        self.wav_ampl = QCustomUnscrollableSpinBox()
        self.wav_ampl.setDecimals(2)
        self.wav_ampl.setRange(-140.0, -5)
        self.wav_ampl.setSingleStep(0.02)
        self.wav_ampl.setKeyboardTracking(False)
        self.wav_ampl.setFont(QFont(SHELL_FONT, pointSize=14))
        self.wav_ampl.setAlignment(Qt.AlignRight)

        # lay out waveform widget
        waveform_layout.addWidget(self.wav_lockswitch,  0, 0, 1, 1)
        waveform_layout.addWidget(wav_freq_label,       1, 0, 1, 1)
        waveform_layout.addWidget(self.wav_freq,        2, 0, 1, 1)
        waveform_layout.addWidget(wav_ampl_label,       3, 0, 1, 1)
        waveform_layout.addWidget(self.wav_ampl,        4, 0, 1, 1)
        waveform_layout.addWidget(self.wav_toggle,      5, 0, 1, 1)
        return QCustomGroupBox(waveform_widget, "Waveform")

    def makeLayout(self):
        """
        Create the main GUI widgets and lay them out.
        """
        layout =    QGridLayout(self)

        # title
        title = QLabel("Trap RF Client")
        title.setFont(QFont(SHELL_FONT, pointSize=17))
        title.setAlignment(Qt.AlignCenter)

        # make widgets
        waveform_widget_wrapped = self._makeWaveformWidget()
        # waveform_widget_wrapped.setFixedWidth(140)


        # lay out
        layout.addWidget(title,                             0, 0, 1, 2)
        layout.addWidget(waveform_widget_wrapped,           1, 0, 6, 2)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(RF_gui)
