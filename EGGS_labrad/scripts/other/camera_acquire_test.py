'''
test camera image acquisition
'''
import labrad
import time

import numpy as np
import matplotlib.pyplot as plt

# configure
num_shots = 10
exposure_time_s = 0.1
emccd_gain = 200
poll_interval_s = 1.0

# main loop
try:
    #  get servers
    cxn = labrad.connect()
    cam = cxn.andor_server

    # get camera properties
    image_dimensions = cam.info_detector_dimensions()

    # set up image acquisition
    cam.acquisition_stop()
    cam.mode_acquisition('Run till abort')
    cam.emccd_gain(emccd_gain)
    cam.exposure_time(exposure_time_s)

    # prepare storage arrays
    data_recent =   np.zeros(np.multiply(*image_dimensions)) * np.nan
    data_old =      np.zeros(np.multiply(*image_dimensions)) * np.nan

    # acquire a series of images
    for i in range(num_shots):

        # acquire image
        cam.acquisition_start()
        cam.acquisition_wait()
        data_recent = cam.acquire_image_recent()

        # check to see if data has changed
        if np.all(data_recent == data_old):
            print('ERR: old data for acq {:d}'.format(i))

        # show image
        plt.imshow(data_recent.reshape(image_dimensions))
        plt.show()

        # store old image and wait for next poll interval
        data_old = data_recent
        time.sleep(poll_interval_s)

except Exception as e:
    print(e)

finally:
    cam.acquisition_stop()
