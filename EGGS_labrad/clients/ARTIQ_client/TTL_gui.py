from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QFrame, QSizePolicy

from EGGS_labrad.clients.Widgets import TextChangingButton, QCustomGroupBox, QChannelHolder


class TTL_channel(QFrame):
    """
    GUI for a single TTL channel.
    """

    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0003)
        #self.setFrameStyle(QFrame.WinPanel)
        self.setFrameShadow(QFrame.Raised)
        # self.setLineWidth(2)
        self.makeLayout(name)
        self.setFixedSize(150, 75)

    def makeLayout(self, title):
        layout = QGridLayout(self)
        # labels
        title = QLabel(title)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=10))
        title.setAlignment(Qt.AlignCenter)
        title.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        # buttons
        self.toggleswitch = TextChangingButton(("ON", "OFF"))
        self.lockswitch = TextChangingButton(("Unlocked", "Locked"))
        self.lockswitch.setFont(QFont('MS Shell Dlg 2', pointSize=8))
        self.lockswitch.toggled.connect(lambda status: self.lock(status))
        self.lockswitch.setChecked(False)
        # set layout
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(self.toggleswitch, 1, 0, 1, 1)
        layout.addWidget(self.lockswitch, 1, 1, 1, 1)

        # connect signal to slot

    def lock(self, status):
        self.toggleswitch.setEnabled(status)


class TTL_gui(QWidget):
    """
    GUI for all TTL channels.
    """

    name = "ARTIQ TTL GUI"
    row_length = 5
    # todo: qgroupbox for organization

    def __init__(self, ttl_list, parent=None):
        super().__init__(parent)
        self.ttl_list = ttl_list
        # start connections
        self.makeLayout()

    def makeLayout(self):
        layout = QGridLayout(self)
        # set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        title.setMargin(4)
        layout.addWidget(title, 0, 0, 1, 10)
        # layout widgets
        total_height = 2
        for ttl_category_name, ttl_category_list in self.ttl_list.items():
            # automatically adjust for larger TTL groups
            num_TTLs = len(ttl_category_list.keys())
            group_height = 2 * int(num_TTLs / self.row_length + 1)
            # create TTL category group
            ttl_category_group = self._makeTTLGroup(ttl_category_list, ttl_category_name)
            layout.addWidget(ttl_category_group, total_height, 0, group_height, self.row_length)
            total_height += group_height

    def _makeTTLGroup(self, ttlgroup_list, ttlgroup_name):
        """
        Creates a group of TTLs as a widget.
        """
        # create widget
        ttl_group = QWidget()
        ttl_group_layout = QGridLayout(ttl_group)
        # layout individual ttls on group
        ttl_iter = iter(range(len(ttlgroup_list.keys())))
        #dict_dj = {}
        for channel_name in ttlgroup_list.keys():
            channel_num = next(ttl_iter)
            # initialize GUI
            channel_gui = TTL_channel(channel_name)
            # layout channel GUI
            row = int(channel_num / self.row_length) + 2
            column = channel_num % self.row_length
            # add widget to client list and layout
            self.ttl_list[ttlgroup_name][channel_name] = channel_gui
            #dict_dj[channel_name] = ((row, column), channel_gui)
            ttl_group_layout.addWidget(channel_gui, row, column)
        # wrap TTLs in a QGroupBox
        # ttl_wrapped = QChannelHolder(dict_dj, ttlgroup_name, scrollable=False) # for QChannelHolder
        ttl_wrapped = QCustomGroupBox(ttl_group, ttlgroup_name)
        return ttl_wrapped


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # run a TTL channel
    # runGUI(TTL_channel, name='TTL Channel')

    # run TTL GUI
    # todo: fix, come up with some tmp config so we can try it out
    ttl_list_tmp = {"Input": {"ttl_0": None}, "Output": {"ttl_1": None}}
    runGUI(TTL_gui, ttl_list_tmp)
