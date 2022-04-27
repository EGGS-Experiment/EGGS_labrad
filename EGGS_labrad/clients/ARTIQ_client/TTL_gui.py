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
    row_length = 10


    def __init__(self, parent=None):
        super(TTL_gui, self).__init__()
        # device dictionary
        self.ttl_list = {
            "ttlin_list": {},
            "ttlout_list": {},
            "ttlurukul_list": {},
            "ttlother_list": {}
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
                self.ttl_list["ttlin_list"][name] = None
            elif devicetype == 'TTLOut':
                other_names = ('zotino', 'led', 'sampler')
                if 'urukul' in name:
                    self.ttl_list["ttlurukul_list"][name] = None
                elif any(string in name for string in other_names):
                    self.ttl_list["ttlother_list"][name] = None
                else:
                    self.ttl_list["ttlout_list"][name] = None

    def makeLayout(self):
        layout = QGridLayout(self)
        # set title
        title = QLabel(self.name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=16))
        title.setAlignment(Qt.AlignCenter)
        title.setMargin(4)
        # layout widgets
        in_ttls = self._makeTTLGroup(self.ttlin_list, "Input")
        out_ttls = self._makeTTLGroup(self.ttlout_list, "Output")
        urukul_ttls = self._makeTTLGroup(self.ttlurukul_list, "Urukul")
        other_ttls = self._makeTTLGroup(self.ttlother_list, "Other")
        # lay out widgets
        layout.addWidget(title,             0, 0, 1, 10)
        layout.addWidget(in_ttls,           2, 0, 2, 4)
        layout.addWidget(out_ttls,          5, 0, 3, 10)
        layout.addWidget(urukul_ttls,       9, 0, 3, 10)
        layout.addWidget(other_ttls,        13, 0, 2, 5)

    def _makeTTLGroup(self, ttl_list, name):
        """
        Creates a group of TTLs as a widget.
        """
        # create widget
        ttl_group = QFrame()
        ttl_group.setFrameStyle(0x0001 | 0x0010)
        ttl_group.setLineWidth(2)
        layout = QGridLayout(ttl_group)
        # set title
        title = QLabel(name)
        title.setFont(QFont('MS Shell Dlg 2', pointSize=13))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title, 0, 0)
        # layout individual ttls on group
        ttl_iter = iter(range(len(ttl_list.keys())))
        for channel_name in ttl_list.keys():
            channel_num = next(ttl_iter)
            # initialize GUI
            channel_gui = TTL_channel(channel_name)
            # layout channel GUI
            row = int(channel_num / self.row_length) + 2
            column = channel_num % self.row_length
            # add widget to client list and layout
            self.ttl_clients[channel_name] = channel_gui
            layout.addWidget(channel_gui, row, column)
        return ttl_group


if __name__ == "__main__":
    from EGGS_labrad.clients import runGUI
    # run a TTL channel
    # runGUI(TTL_channel, name='TTL Channel')

    # run TTL GUI
    runGUI(TTL_gui)
