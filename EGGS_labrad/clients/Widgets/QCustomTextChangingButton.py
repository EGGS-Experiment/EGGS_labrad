from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPalette
from PyQt5.QtWidgets import QPushButton, QSizePolicy

__all__ = ['TextChangingButton', 'Lockswitch']
# todo: create onoff switch


class TextChangingButton(QPushButton):
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
        self.setAppearance(self.isDown())

    def setAppearance(self, down):
        on_text, off_text = self._setButtonTexts()
        if down:
            self.setText(on_text)
            self.setPalette(QPalette(Qt.darkGreen))
        else:
            self.setText(off_text)
            self.setPalette(QPalette(Qt.black))
        self.setStyleSheet("color: black;")

    def _setButtonTexts(self):
        """
        Return button texts when they are on or off.
        """
        if type(self.button_text) == str:
            on_text = self.button_text + ": On"
            off_text = self.button_text + ": Off"
        elif type(self.button_text) == tuple:
            on_text, off_text = self.button_text
        elif self.button_text is None:
            on_text = "On"
            off_text = "Off"
        else:
            raise TypeError("Error: text to be displayed on a button needs to be a string.")
        return on_text, off_text

    def sizeHint(self):
        return QSize(37, 26)


class Lockswitch(TextChangingButton):
    """
    A TextChangingButton used just for
    preventing changes to a GUI element.
    """

    def __init__(self, parent=None, *args, **kwargs):
        super().__init__(button_text=('Unlocked', 'Locked'), parent=parent)
        # set default parameters
        #self.setFixedHeight(23)
        self.setChecked(True)

    def sizeHint(self):
        return QSize(37, 26)
