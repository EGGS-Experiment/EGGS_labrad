from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QPushButton, QSizePolicy, QGroupBox, QWidget, QGridLayout, QScrollArea

__all__ = ['QCustomGroupBox']


class QCustomGroupBox(QPushButton):
    """
    Button that changes its text to ON or OFF and colors when it's pressed.
    """

    def __init__(self, button_text, parent=None, fontsize=10):
        """
        NOTE: when both labels and addtext are not
        None, labels take precedence.

        Parameters
        ----------
        button_text: could be a 2-tuple of string, a string, or None.
            When it's a 2-tuple, the first entry corresponds to text when the
            button is "ON", and the second entry corresponds to text when the
            button is "OFF".
            When it's a string, it is the text that gets added before "ON" or
            "OFF".
            When it's None, then the text gets displayed are "On" or "Off".
        """
        super(TextChangingButton, self).__init__(parent)
        self.button_text = button_text
        self.setCheckable(True)
        self.setFont(QFont('MS Shell Dlg 2', pointSize=fontsize))
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        # connect signal for appearance changing
        self.toggled.connect(self.setAppearance)

    def sizeHint(self):
        return QSize(37, 26)

    def _wrapGroup(self, name, widget):
        wrapper = QGroupBox(name)
        wrapper_layout = QGridLayout(wrapper)
        wrapper_layout.addWidget(widget)
        return wrapper
