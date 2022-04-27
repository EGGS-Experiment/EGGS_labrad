from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QWidget, QLabel, QGridLayout, QFrame, QSizePolicy

from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.config.device_db import device_db
from EGGS_labrad.clients.Widgets import TextChangingButton


class TTL_channel(QFrame):
    """
    GUI for a single TTL channel.
    """

    def __init__(self, name=None, parent=None):
        QWidget.__init__(self, parent)
        self.name = name
        self.setFrameStyle(0x0001 | 0x0010)
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
        self.toggle = TextChangingButton(("ON", "OFF"))
        self.lockswitch = TextChangingButton(("Unlocked", "Locked"))
        self.lockswitch.setFont(QFont('MS Shell Dlg 2', pointSize=8))
        self.lockswitch.setChecked(True)
        # set layout
        layout.addWidget(title, 0, 0, 1, 2)
        layout.addWidget(self.toggle, 1, 0, 1, 1)
        layout.addWidget(self.lockswitch, 1, 1, 1, 1)

        # connect signal to slot
        self.lockswitch.toggled.connect(lambda status=self.lockswitch.isChecked(): self.lock(status))

    @inlineCallbacks
    def lock(self, status):
        yield self.toggle.setEnabled(status)


class TTL_gui(QWidget):
    """
    GUI for all TTL channels.
    """

    name = "ARTIQ TTL GUI"
    row_length = 5
    # todo: qgroupbox for organization
    def __init__(self, parent=None):
        super(TTL_gui, self).__init__()
        # device dictionary
        self.ttl_list = {
            "Input": {},
            "Output": {},
            "Urukul": {},
            "Other": {}
        }
        # start connections
        self.getDevices()
        self.makeLayout()

    def getDevices(self):
        for name, params in device_db.items():
            # only get devices with named class
            if 'class' not in params:
                continue
            # set device as attribute
            devicetype = params['class']
            if devicetype == 'TTLInOut':
                self.ttl_list["Input"][name] = None
            elif devicetype == 'TTLOut':
                other_names = ('zotino', 'led', 'sampler')
                if 'urukul' in name:
                    self.ttl_list["Urukul"][name] = None
                elif any(string in name for string in other_names):
                    self.ttl_list["Other"][name] = None
                else:
                    self.ttl_list["Output"][name] = None

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
        ttl_group = QFrame()
        ttl_group.setFrameStyle(0x0001 | 0x0010)
        ttl_group.setLineWidth(2)
        layout = QGridLayout(ttl_group)
        # set title
        title = QLabel(ttlgroup_name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0)
        # layout individual ttls on group
        ttl_iter = iter(range(len(ttlgroup_list.keys())))
        for channel_name in ttlgroup_list.keys():
            channel_num = next(ttl_iter)
            # initialize GUI
            channel_gui = TTL_channel(channel_name)
            # layout channel GUI
            row = int(channel_num / self.row_length) + 2
            column = channel_num % self.row_length
            # add widget to client list and layout
            self.ttl_list[ttlgroup_name][channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column)
        return ttl_group


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # run a TTL channel
    # runGUI(TTL_channel, name='TTL Channel')

    # run TTL GUI
    runGUI(TTL_gui)
