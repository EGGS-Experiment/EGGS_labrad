from PyQt5.QtWidgets import QGroupBox, QGridLayout

__all__ = ['QCustomGroupBox']

# todo: create a widget that holds channels of something

class QCustomGroupBox(QGroupBox):
    """
    Button that changes its text to ON or OFF and colors when it's pressed.
    """

    def __init__(self, widget, name, parent=None):
        """
        NOTE: when both labels and addtext are not
        None, labels take precedence.

        Parameters
        ----------
        button_text: could be a 2-tuple of string, a string, or None.
            When it's a 2-tuple, the first entry corresponds to text when the
        """
        super().__init__(name, parent)
        layout = QGridLayout(self)
        layout.addWidget(widget)
