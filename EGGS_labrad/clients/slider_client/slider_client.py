from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.slider_client.slider_gui import slider_gui


class slider_client(GUIClient):

    name = 'Slider Client'

    STATUSID = 984165
    POSITIONID = 984166

    servers = {'ss': 'Slider Server'}

    def getgui(self):
        if self.gui is None:
            self.gui = slider_gui()
        return self.gui

    @inlineCallbacks
    def initClient(self):
        # connect to device signals
        yield self.ss.signal__status_update(self.STATUSID)
        yield self.ss.addListener(listener=self.updateStatus, source=None, ID=self.STATUSID)
        yield self.ss.signal__position_update(self.POSITIONID)
        yield self.ss.addListener(listener=self.updatePosition, source=None, ID=self.POSITIONID)

    @inlineCallbacks
    def initData(self):
        position = yield self.ss.position()
        self.updatePosition(None, position)

    def initGUI(self):
        self.gui.home_button.clicked.connect(lambda status: self.ss.move_home())
        self.gui.forward_button.clicked.connect(lambda status: self.ss.move_jog(1))
        self.gui.backward_button.clicked.connect(lambda status: self.ss.move_jog(0))
        # start up locked
        self.gui.lockswitch.setChecked(False)

    # SIGNALS
    # @inlineCallbacks
    def updateStatus(self, c, status):
        """
        Updates device status.
        """
        pass

    def updatePosition(self, c, position):
        """
        Updates the slider position on the GUI.
        """
        widget = self.gui.position_buttons[position]
        # todo
        pass


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(slider_client)
