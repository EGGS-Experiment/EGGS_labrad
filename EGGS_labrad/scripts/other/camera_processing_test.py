"""
TEST IMAGE PROCESSING & ION POSITION EXTRACTION VIA ANDOR CAMERA
"""
import time
import labrad

import numpy as np
import matplotlib.pyplot as plt

# configure
_IMAGES_PER_PROCESS =   5
_EXPOSURE_TIME_S =      0.1
_EMCCD_GAIN =           250
_POLL_INTERVAL_S =      1.0



# MAIN LOOP
try:
    # get servers
    cxn = labrad.connect()
    cam = cxn.andor_server
    aq = cxn.artiq_server
    dc = cxn.dc_server

    # get camera properties
    image_dimensions = cam.info_detector_dimensions()

    # set up image acquisition
    cam.acquisition_stop()
    cam.mode_acquisition('Run till abort')
    cam.emccd_gain(_EMCCD_GAIN)
    cam.exposure_time(_EXPOSURE_TIME_S)

    # create background-subtracted acquisition function
    def image_acquire_bgr_subtract():
        # acquire background
        aq.dds_toggle('urukul2_sw2', 0)
        time.sleep(1.0)
        img_bgr = cam.acquire_image_recent()

        # acquire signal
        aq.dds_toggle('urukul2_sw2', 1)
        time.sleep(1.0)
        img_signal = cam.acquire_image_recent()

        # return background-subtracted image
        return img_signal - img_bgr


    '''
    DETERMINE A DECENT ROI
    '''
    # set basic ROI and create holder variables
    cam.image_region_set(1, 1, 1, 512, 1, 512)
    _image_holder = np.zeros(np.multiply(*image_dimensions)) * np.nan

    # average a bunch of images
    for i in range(_IMAGES_PER_PROCESS):
        _image_holder += image_acquire_bgr_subtract()
    _image_holder = (_image_holder / _IMAGES_PER_PROCESS).reshape((512, 512))

    # get vertical and horizontal maxima
    x_vals = np.sum(_image_holder, axis=0)
    y_vals = np.sum(_image_holder, axis=1)

    # todo: get first image
    # todo: extract argmin/argmax
    # todo: center around argmin/argmax


    # # acquire a series of images
    # for i in range(num_shots):
    #
    #     # acquire image
    #     cam.acquisition_start()
    #     cam.acquisition_wait()
    #     data_recent = cam.acquire_image_recent()
    #
    #     # check to see if data has changed
    #     if np.all(data_recent == data_old):
    #         print('ERR: old data for acq {:d}'.format(i))
    #
    #     # show image
    #     plt.imshow(data_recent.reshape(image_dimensions))
    #     plt.show()
    #
    #     # store old image and wait for next poll interval
    #     data_old = data_recent
    #     time.sleep(poll_interval_s)

    #

except Exception as e:
    print(e)

finally:
    cam.acquisition_stop()

