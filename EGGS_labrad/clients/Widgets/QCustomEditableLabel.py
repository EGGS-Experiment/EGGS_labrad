from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QLineEdit, QFrame

__all__ = ['QCustomEditableLabel']

# todo: add border
# todo: make sunken in when not editing


class QCustomEditableLabel(QLineEdit):
    """
    A QLabel that allows the text to be set by double-clicking on the label.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.setFrameShadow(QFrame.Raised)
        # self.setFrameStyle(0x0001 | 0x0030)
        # self.setFrameStyle(QFrame.WinPanel)
        self.setAlignment(Qt.AlignCenter)
        self.setFrame(True)
        self.setReadOnly(True)
        # set style
        self.editStatus = False
        self.editStyle = "background-color:white; color:black; border: 1px solid black"
        self.disabledStyle = "background-color:gray; color:black; border: 3px solid gray"
        self.setStyleSheet(self.disabledStyle)
        # connect slots
        self.editingFinished.connect(lambda: self.toggleEditable(False))

    def mouseDoubleClickEvent(self, event):
        # only make editable if not already editing
        if self.editStatus is False:
            self.toggleEditable(True)

    def toggleEditable(self, status):
        if status is True:
            self.setStyleSheet(self.editStyle)
            self.setReadOnly(False)
        elif status is False:
            self.setReadOnly(True)
            self.setStyleSheet(self.disabledStyle)
            # todo: check if text changed

    # def mousePressEvent(self, event):
    #     print('mouse press')
    #
    # def focusOutEvent(self, event):
    #     print('focus out')
    #
    # def clearFocus(self, event):
    #     print('focus clear')
