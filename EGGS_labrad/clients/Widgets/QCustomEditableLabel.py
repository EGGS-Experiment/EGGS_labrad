from PyQt5.QtWidgets import QGridLayout, QWidget, QLabel, QGroupBox, QLineEdit, QFrame, QPushButton
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot

__all__ = ['QCustomEditableLabel']
# todo: center after writing


# class QCustomEditableLabel(QPushButton):
#     """
#     A QLabel that allows the text to be set by double-clicking on the label.
#     """
#
#     doubleClicked = pyqtSignal()
#     clicked = pyqtSignal()
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # create a timer to record double click
#         self.timer = QTimer()
#         self.timer.setSingleShot(True)
#         self.timer.timeout.connect(self.clicked.emit)
#         super().clicked.connect(self.onClick)
#
#     @pyqtSlot()
#     def onClick(self):
#         print('clicked')
#         if self.timer.isActive():
#             self.doubleClicked.emit()
#             self.timer.stop()
#             self.onDoubleClick()
#         else:
#             self.timer.start(250)
#
#     @pyqtSlot()
#     def onDoubleClick(self):
#         print('double clicked')
class QCustomEditableLabel(QLineEdit):
    """
    A QLabel that allows the text to be set by double-clicking on the label.
    """


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print('double clicked')
        #self.setReadOnly(True)


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    runGUI(QCustomEditableLabel)
    # read only until double clicked
    # set text when click away
    # add border
    # make sunken in when not editing
    # look at qdetachabletab to see how to create events