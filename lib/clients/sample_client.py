import os
import time
import datetime as datetime

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.client import GUIClient
from EGGS_labrad.lib.clients.cryovac_clients.twistorr74_gui import twistorr74_gui

class twistorr74_client(GUIClient):

    name = 'Twistorr74 Client'

    PRESSUREID = 694321
    ENERGYID = 694322
    RPMID = 694323
    POWERID = 694324

    @inlineCallbacks
    def initClient(self, cxn):
        # try to get servers
        self.servers = ['TwisTorr74 Server', 'Data Vault']
        try:
            self.tt = self.cxn.twistorr74_server
        except Exception as e:
            print('Required servers not connected, disabling widget.')
            self.setEnabled(False)

        # connect to signals
            #device parameters
        yield self.tt.signal__pressure_update(self.PRESSUREID)
        yield self.tt.addListener(listener=self.updatePressure, source=None, ID=self.PRESSUREID)
        yield self.tt.signal__energy_update(self.ENERGYID)
        yield self.tt.addListener(listener=self.updateEnergy, source=None, ID=self.ENERGYID)
        yield self.tt.signal__rpm_update(self.RPMID)
        yield self.tt.addListener(listener=self.updateRPM, source=None, ID=self.RPMID)
        yield self.tt.signal__power_update(self.POWERID)
        yield self.tt.addListener(listener=self.updatePower, source=None, ID=self.POWERID)

        # start device polling
        poll_params = yield self.tt.polling()
        # only start polling if not started
        if not poll_params[0]:
            yield self.tt.set_polling(True, 5.0)
        print(poll_params)
        return self.cxn

    @inlineCallbacks
    def initializeGUI(self, cxn):
        #startup data
        power_tmp = yield self.tt.toggle()
        self.gui.twistorr_power.setChecked(power_tmp)
        #connect signals to slots
        self.gui.twistorr_lockswitch.toggled.connect(lambda status: self.lock_twistorr(status))
        self.gui.twistorr_power.clicked.connect(lambda status: self.toggle_twistorr(status))
        self.gui.twistorr_record.toggled.connect(lambda status: self.record_pressure(status))


    # SIGNALS
    @inlineCallbacks
    def updatePressure(self, c, pressure):
        """
        Updates GUI when values are received from server.
        """
        self.gui.pressure_display.setText(str(pressure))
        if self.recording:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, pressure, context=self.c_record)

    def updateEnergy(self, c, energy):
        """
        Updates GUI when values are received from server.
        """
        self.gui.power_display.setText(str(energy))

    def updateRPM(self, c, rpm):
        """
        Updates GUI when values are received from server.
        """
        self.gui.rpm_display.setText(str(rpm))

    def updatePower(self, c, power):
        """
        Updates GUI when other clients have made changes to the device.
        """
        self.gui.twistorr_power.setChecked(power)


    # SLOTS
    @inlineCallbacks
    def record_pressure(self, status):
        """
        Creates a new dataset to record pressure and
        tells polling loop to add data to data vault.
        """
        self.recording = status
        if self.recording:
            self.starttime = time.time()
            date = datetime.datetime.now()
            year = str(date.year)
            month = '%02d' % date.month  # Padded with a zero if one digit
            day = '%02d' % date.day  # Padded with a zero if one digit
            hour = '%02d' % date.hour  # Padded with a zero if one digit
            minute = '%02d' % date.minute  # Padded with a zero if one digit

            trunk1 = year + '_' + month + '_' + day
            trunk2 = self.name + '_' + hour + ':' + minute
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
            yield self.dv.new('Twistorr 74 Pump Controller', [('Elapsed time', 't')],
                              [('Pump Pressure', 'Pressure', 'mbar')], context=self.c_record)

    #@inlineCallbacks
    def toggle_twistorr(self, status):
        """
        Sets pump power on or off.
        """
        print('set power: ' + str(status))
        #yield self.tt.toggle(status)

    def lock_twistorr(self, status):
        """
        Locks user interface to device.
        """
        self.gui.twistorr_power.setEnabled(status)

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication([])
    try:
        import qt5reactor
        qt5reactor.install()
    except Exception as e:
        print(e)
    from twisted.internet import reactor
    client = twistorr74_client(reactor, gui=twistorr74_gui)
    try:
        client.gui.show()
    except:
        client.show()
    reactor.run()
    try:
        client.close()
    except:
        sys.exit(app.exec())
