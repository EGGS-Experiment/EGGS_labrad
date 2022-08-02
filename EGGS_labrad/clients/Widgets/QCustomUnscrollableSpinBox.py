from PyQt5.QtWidgets import QDoubleSpinBox

__all__ = ["QCustomUnscrollableSpinBox"]


class QCustomUnscrollableSpinBox(QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        self.wheelEvent = lambda event:None
        super().__init__(*args, **kwargs)
