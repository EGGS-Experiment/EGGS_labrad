import labrad
from labrad.units import WithUnit
import numpy as np
from matplotlib import pyplot
import matplotlib.image as im
import time

identify_exposure = WithUnit(0.2, 's')
start_x = 1; stop_x = 512
start_y = 1; stop_y = 512
image_region = (2,2,start_x,stop_x,start_y,stop_y)

pixels_x = (stop_x - start_x + 1)/2
pixels_y = (stop_y - start_y + 1)/2

cxn = labrad.connect()
cam = cxn.andor_server




cam.abort_acquisition()
initial_exposure = cam.get_exposure_time()
cam.set_exposure_time(identify_exposure)
initial_region = cam.get_image_region()
cam.set_image_region(*image_region)
cam.set_shutter_mode('Open')
cam.set_acquisition_mode('Run till abort')
cam.start_acquisition()
cam.wait_for_acquisition()
image = cam.get_most_recent_image()
cam.abort_acquisition()
cam.set_shutter_mode('Close')

image = np.reshape(image, (pixels_y, pixels_x))
np.save('sample', image)


pyplot.imshow(image)


cam.set_exposure_time(initial_exposure)
cam.set_image_region(initial_region)
cam.start_live_display()


pyplot.show()
