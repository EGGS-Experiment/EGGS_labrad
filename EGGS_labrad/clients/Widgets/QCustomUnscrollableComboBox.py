from PyQt5.QtWidgets import QComboBox

__all__ = ["QCustomUnscrollableComboBox"]


class QCustomUnscrollableComboBox(QComboBox):
    def __init__(self, *args, **kwargs):
        self.wheelEvent = lambda event: None
        super().__init__(*args, **kwargs)
