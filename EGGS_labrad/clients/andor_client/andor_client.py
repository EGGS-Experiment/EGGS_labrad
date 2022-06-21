import os
import numpy as np
from datetime import datetime
from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.clients import GUIClient
from EGGS_labrad.clients.andor_gui import AndorGUI
from EGGS_labrad.clients.andor_gui.image_region_selection import image_region_selection_dialog
from EGGS_labrad.config.andor_config import AndorConfig as config
# todo: document


class AndorClient(GUIClient):
    """
    A client for Andor iXon cameras.
    """

    def getgui(self):
        if self.gui is None:
            self.gui = AndorGUI()

    def __init__(self, server):
        super(AndorGUI, self).__init__()
        self.server = server
        self.setup_layout()
        self.live_update_loop = LoopingCall(self.live_update)
        self.connect_layout()
        self.saved_data = None

        self.save_images_state = False
        self.image_path = config.image_path

        try:
            self.save_in_sub_dir = config.save_in_sub_dir
        except Exception as e:
            self.save_in_sub_dir = False
            print("save_in_sub_dir not found in config")
        try:
            self.save_format = config.save_format
        except Exception as e:
            self.save_format = "tsv"
            print("save_format not found in config")
        try:
            self.save_header = config.save_header
        except Exception as e:
            self.save_header = False
            print("save_header not found in config")

    @inlineCallbacks
    def connect_layout(self):
        # self.emrange= yield self.server.getemrange(None)
        # mingain, maxgain = self.emrange
        # self.emccdSpinBox.setMinimum(0)
        # self.emccdSpinBox.setMaximum(4096)
        self.set_image_region_button.clicked.connect(self.on_set_image_region)
        self.plt.scene().sigMouseClicked.connect(self.mouse_clicked)
        exposure = yield self.server.getExposureTime(None)
        self.exposureSpinBox.setValue(exposure['s'])
        self.exposureSpinBox.valueChanged.connect(self.on_new_exposure)
        gain = yield self.server.getEMCCDGain(None)
        self.emccdSpinBox.setValue(gain)
        trigger_mode = yield self.server.getTriggerMode(None)
        self.trigger_mode.setText(trigger_mode)
        acquisition_mode = yield self.server.getAcquisitionMode(None)
        self.acquisition_mode.setText(acquisition_mode)
        self.emccdSpinBox.valueChanged.connect(self.on_new_gain)
        self.live_button.clicked.connect(self.on_live_button)
        self.save_images.stateChanged.connect(lambda state= \
                                                         self.save_images.isChecked(): self.save_image_data(state))

    def save_image_data(self, state):
        self.save_images_state = bool(state)


    # SLOTS
    def on_set_image_region(self, checked):
        # displays a non-modal dialog
        dialog = image_region_selection_dialog(self, self.server)
        one = dialog.open()
        two = dialog.show()
        three = dialog.raise_()

    @inlineCallbacks
    def on_new_exposure(self, exposure):
        if self.live_update_loop.running:
            yield self.on_live_button(False)
            yield self.server.setExposureTime(None, exposure)
            yield self.on_live_button(True)
        else:
            yield self.server.setExposureTime(None, exposure)

    def set_exposure(self, exposure):
        self.exposureSpinBox.blockSignals(True)
        self.exposureSpinBox.setValue(exposure)
        self.exposureSpinBox.blockSignals(False)
        # todo: server

    def set_trigger_mode(self, mode):
        self.trigger_mode.setText(mode)
        # todo: server

    def set_acquisition_mode(self, mode):
        self.acquisition_mode.setText(mode)
        # todo: server

    @inlineCallbacks
    def on_new_gain(self, gain):
        yield self.server.setEMCCDGain(None, gain)

    def set_gain(self, gain):
        self.emccdSpinBox.blockSignals(True)
        self.emccdSpinBox.setValue(gain)
        self.emccdSpinBox.blockSignals(False)

    @inlineCallbacks
    def on_live_button(self, checked):
        if checked:
            yield self.server.setTriggerMode(None, 'Internal')
            yield self.server.setAcquisitionMode(None, 'Run till abort')
            yield self.server.set_shutter_mode(None, 'Open')
            yield self.server.startAcquisition(None)
            self.binx, self.biny, self.startx, self.stopx, self.starty, self.stopy = yield self.server.getImageRegion(
                None)
            self.pixels_x = int((self.stopx - self.startx + 1) / self.binx)
            self.pixels_y = int((self.stopy - self.starty + 1) / self.biny)
            yield self.server.waitForAcquisition(None)
            self.live_update_loop.start(0)
        else:
            yield self.live_update_loop.stop()
            yield self.server.abortAcquisition(None)
            yield self.server.set_shutter_mode(None, 'Close')

    @inlineCallbacks
    def live_update(self):
        data = yield self.server.getMostRecentImage(None)
        image_data = np.reshape(data, (self.pixels_y, self.pixels_x))
        self.img_view.setImage(image_data.transpose(), autoRange=False, autoLevels=False,
                               pos=[self.startx, self.starty], scale=[self.binx, self.biny], autoHistogramRange=False)

        if self.save_images_state == True:
            self.save_image(image_data)

    def get_image_header(self):
        header = ""
        shutter_time = self.exposureSpinBox.value()
        header += "shutter_time " + str(shutter_time) + "\n"
        em_gain = self.emccdSpinBox.value()
        header += "em_gain " + str(em_gain)
        return header

    def save_image(self, image_data):
        if not np.array_equal(image_data, self.saved_data):
            self.saved_data = image_data
            saved_data_in_int = self.saved_data.astype("int16")
            time_stamp = "-".join(self.datetime_to_str_list())
            if self.save_in_sub_dir:
                path = self.check_save_path_exists()
                path = os.path.join(path, time_stamp)
            else:
                path = os.path.join(self.image_path, time_stamp)
            if self.save_header:
                header = self.get_image_header()
            else:
                header = ""
            if self.save_format == "tsv":
                np.savetxt(path + ".tsv", saved_data_in_int, fmt='%i', header=header)
            elif self.save_format == "csv":
                np.savetxt(path + ".csv", saved_data_in_int, fmt='%i', delimiter=",", header=header)
            elif self.save_format == "bin":
                saved_data_in_int.tofile(path + ".dat")
            else:
                np.savetxt(path + ".tsv", saved_data_in_int, fmt='%i', header=header)

    def datetime_to_str_list(self):
        dt = datetime.now()
        dt_str = [str(dt.year).rjust(4, "0"), str(dt.month).rjust(2, "0"), str(dt.day).rjust(2, "0"),
                  str(dt.hour).rjust(2, "0"),
                  str(dt.minute).rjust(2, "0"), str(dt.second).rjust(2, "0"),
                  str(int(dt.microsecond / 1000)).rjust(3, "0")]
        return dt_str

    def str_datetime_to_path(self, str_datetime):
        year = str_datetime[0]
        month = str_datetime[1]
        day = year + "_" + month + "_" + str_datetime[2]
        return (year, month, day)

    def check_save_path_exists(self):
        folders = self.str_datetime_to_path(self.datetime_to_str_list())
        path = self.image_path
        for sub_dir in folders:
            path = os.path.join(path, sub_dir)
            if not os.path.isdir(path):
                os.makedirs(path)
        return path

    @inlineCallbacks
    def start_live_display(self):
        self.live_button.setChecked(True)
        yield self.on_live_button(True)

    @inlineCallbacks
    def stop_live_display(self):
        self.live_button.setChecked(False)
        yield self.on_live_button(False)

    @property
    def live_update_running(self):
        return self.live_update_loop.running


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(AndorClient)
