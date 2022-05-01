from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGridLayout, QWidget, QLabel


class QInitializePlaceHolder(QWidget):
    """
    A blank widget that serves as a placeholder
    during GUIClient initialization.
    """

    def __init__(self):
        """
        NOTE: when both labels and addtext are not
        None, labels take precedence.

        Parameters
        ----------
        button_text: could be a 2-tuple of string, a string, or None.
            When it's a 2-tuple, the first entry corresponds to text when the
        """
        super().__init__()
        loading_image = QLabel()
        loading_image.setPixmap(QPixmap("loading.png"))
        layout = QGridLayout(self)
        layout.addWidget(loading_image)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(QInitializePlaceHolder)
