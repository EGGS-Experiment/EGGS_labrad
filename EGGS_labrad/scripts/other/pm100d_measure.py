import labrad
from time import time, sleep
from numpy import arange, linspace, zeros, mean, amax

from EGGS_labrad.clients import createTrunk

name_tmp = "PM100D Measure"
interval_s = 2


cxn = labrad.connect()
print('Connection successful.')

# get servers
pm = cxn.power_meter_server
dv = cxn.data_vault
cr = cxn.context()
print('Server connection successful.')

# set up power meter
pm.select_device()
pm.configure_mode('POW')


# create dataset
trunk_tmp = createTrunk(name_tmp)
dv.cd(trunk_tmp, True, context=cr)
dv.new(
    name_tmp,
    [('Time', 's')],
    [('729nm Power', 'Power', 'mW')],
    context=cr
)
print('Data vault successfully setup.')

# set up recording
#pm.wavelength(400)

# start recording
starttime = time()
while True:
    pow = pm.measure()
    elapsedtime = time() - starttime
    dv.add(elapsedtime, pow * 1e3, context=cr)
    sleep(interval_s)
