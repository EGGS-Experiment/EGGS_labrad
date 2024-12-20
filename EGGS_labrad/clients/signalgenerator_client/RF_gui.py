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
        self.setFixedSize(610, 310)
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

        wav_ampl_label = QLabel("Amplitude (dBm)")
        wav_freq_label = QLabel("Frequency (MHz)")

        self.wav_toggle = TextChangingButton(('On', 'Off'), fontsize=11)
        self.wav_reset = QPushButton("Reset")
        self.wav_reset.setFont(QFont(SHELL_FONT, pointSize=11))
        self.wav_lockswitch = Lockswitch()
        self.wav_lockswitch.setFont(QFont(SHELL_FONT, pointSize=11))

        self.wav_ampl = QCustomUnscrollableSpinBox()
        self.wav_ampl.setDecimals(1)
        self.wav_ampl.setRange(-140.0, -5)
        self.wav_ampl.setSingleStep(0.02)
        self.wav_ampl.setKeyboardTracking(False)
        self.wav_ampl.setFont(QFont(SHELL_FONT, pointSize=11))

        self.wav_freq = QCustomUnscrollableSpinBox()
        self.wav_freq.setDecimals(6)
        self.wav_freq.setRange(0.009, 1040.0)
        self.wav_freq.setSingleStep(0.001)
        self.wav_freq.setProperty("value", 9.0)
        self.wav_freq.setKeyboardTracking(False)
        self.wav_freq.setFont(QFont(SHELL_FONT, pointSize=11))

        # lay out waveform widget
        waveform_layout.addWidget(wav_freq_label,       0, 0, 1, 1)
        waveform_layout.addWidget(self.wav_freq,        1, 0, 1, 1)
        waveform_layout.addWidget(wav_ampl_label,       2, 0, 1, 1)
        waveform_layout.addWidget(self.wav_ampl,        3, 0, 1, 1)
        waveform_layout.addWidget(self.wav_toggle,      4, 0, 1, 1)
        waveform_layout.addWidget(self.wav_reset,       5, 0, 1, 1)
        waveform_layout.addWidget(self.wav_lockswitch,  6, 0, 1, 1)
        return QCustomGroupBox(waveform_widget, "Waveform")

    def _makeModulationWidget(self):
        """
        Create signal modulation widget.
        """
        modulation_widget = QWidget()
        modulation_layout = QGridLayout(modulation_widget)

        # create modulation frequency subwidget
        mod_freq_label = QLabel("Modulation Frequency (kHz)")
        self.mod_freq = QCustomUnscrollableSpinBox()
        self.mod_freq.setDecimals(1)
        self.mod_freq.setRange(1, 500.0)
        self.mod_freq.setSingleStep(1.0)
        self.mod_freq.setKeyboardTracking(False)
        self.mod_freq.setFont(QFont(SHELL_FONT, pointSize=11))

        # create modulation subwidgets
        mod_ampl_depth_label = QLabel("Ampl. Depth (%)")
        self.mod_ampl_toggle = TextChangingButton(('On', 'Off'), fontsize=11)
        self.mod_ampl_depth = QCustomUnscrollableSpinBox()
        self.mod_ampl_depth.setDecimals(1)
        self.mod_ampl_depth.setRange(0, 100.0)
        self.mod_ampl_depth.setSingleStep(0.1)
        self.mod_ampl_depth.setKeyboardTracking(False)
        self.mod_ampl_depth.setFont(QFont(SHELL_FONT, pointSize=11))

        mod_freq_dev_label = QLabel("Freq. Dev. (kHz)")
        self.mod_freq_toggle = TextChangingButton(('On', 'Off'), fontsize=11)
        self.mod_freq_dev = QCustomUnscrollableSpinBox()
        self.mod_freq_dev.setDecimals(2)
        self.mod_freq_dev.setMaximum(2000.0)
        self.mod_freq_dev.setSingleStep(0.01)
        self.mod_freq_dev.setKeyboardTracking(False)
        self.mod_freq_dev.setFont(QFont(SHELL_FONT, pointSize=11))

        mod_phase_dev_label = QLabel("Phase Dev. (rad)")
        self.mod_phase_toggle = TextChangingButton(('On', 'Off'), fontsize=11)
        self.mod_phase_dev = QCustomUnscrollableSpinBox()
        self.mod_phase_dev.setDecimals(3)
        self.mod_phase_dev.setRange(0.0, 400.0)
        self.mod_phase_dev.setSingleStep(1)
        self.mod_phase_dev.setProperty("value", 0.0)
        self.mod_phase_dev.setKeyboardTracking(False)
        self.mod_phase_dev.setFont(QFont(SHELL_FONT, pointSize=11))

        def _createMiniWidget(subwidget_list, title):
            widget = QWidget()
            layout = QVBoxLayout(widget)
            for subwidget in subwidget_list:
                layout.addWidget(subwidget)
            return QCustomGroupBox(widget, title)

        am_widget = _createMiniWidget([self.mod_ampl_toggle, mod_ampl_depth_label, self.mod_ampl_depth], "Amplitude Modulation")
        fm_widget = _createMiniWidget([self.mod_freq_toggle, mod_freq_dev_label, self.mod_freq_dev], "Frequency Modulation")
        pm_widget = _createMiniWidget([self.mod_phase_toggle, mod_phase_dev_label, self.mod_phase_dev], "Phase Modulation")

        modulation_layout.addWidget(mod_freq_label,             0, 1, 1, 4)
        modulation_layout.addWidget(self.mod_freq,              1, 1, 1, 4)
        modulation_layout.addWidget(am_widget,                  3, 0, 3, 2)
        modulation_layout.addWidget(fm_widget,                  3, 2, 3, 2)
        modulation_layout.addWidget(pm_widget,                  3, 4, 3, 2)
        return QCustomGroupBox(modulation_widget, "Modulation")

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
        waveform_widget_wrapped =   self._makeWaveformWidget()
        modulation_widget_wrapped = self._makeModulationWidget()
        waveform_widget_wrapped.setFixedWidth(140)
        modulation_widget_wrapped.setFixedWidth(440)

        # lay out
        layout.addWidget(title,                             0, 0, 1, 4)
        layout.addWidget(waveform_widget_wrapped,           1, 0, 6, 1)
        layout.addWidget(modulation_widget_wrapped,         1, 1, 6, 3)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(RF_gui)
