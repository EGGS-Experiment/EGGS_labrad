from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGridLayout, QWidget, QLabel


class QInitializePlaceholder(QWidget):
    """
    A blank widget that serves as a placeholder
    during GUIClient initialization.
    """

    def __init__(self):
        super().__init__()
        loading_image = QLabel()
        loading_image.setPixmap(QPixmap("loading.png"))
        layout = QGridLayout(self)
        layout.addWidget(loading_image)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(QInitializePlaceholder)
