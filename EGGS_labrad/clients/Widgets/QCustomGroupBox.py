from PyQt5.QtWidgets import QGroupBox, QGridLayout, QScrollArea, QWidget
from PyQt5.QtCore import Qt

__all__ = ['QCustomGroupBox', 'QChannelHolder']


class QCustomGroupBox(QGroupBox):
    """
    A QGroupBox that wraps around a widget for cleanliness.
    Can be scrollable.
    """

    def __init__(self, widget, name, scrollable=False, parent=None):
        """
        Arguments:
            scrollable  (bool)  : whether the groupbox is scrollable.
        """
        super().__init__(name, parent)
        layout = QGridLayout(self)
        if scrollable:
            # create a scroll area
            scroll_area = QScrollArea()
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll_area.setWidget(widget)
            # set the width to be just over the width of the enclosed widget
            scroll_area.setMinimumWidth(widget.sizeHint().width() + 20)
            layout.addWidget(scroll_area)
        else:
            layout.addWidget(widget)


# todo: write
class QChannelHolder(QCustomGroupBox):
    """
    A QCustomGroupBox used to hold a collection of channels for organization.
    Takes in a dictionary of channels where keys are the channel names, and
    values are a tuple of (position, widget).
    Position is an integer tuple of (row_num, col_num) starting from (0, 0)
    being the upper left.
    """

    def __init__(self, channel_dict, name, scrollable=False, parent=None):
        """
        Arguments:
            channel_dict    (dict): {channel_name: ((row_num, col_num), widget)}
            scrollable      (bool): whether this channel holder should be scrollable.
        """
        # create widget to hold channels
        holder_widget = QWidget()
        holder_widget_layout = QGridLayout(holder_widget)
        for values in channel_dict.values():
            position, channel_widget = values
            holder_widget_layout.addWidget(channel_widget,      *position)
        super().__init__(holder_widget, name, scrollable, parent)
