
import labrad
from time import sleep

from numpy import linspace
from EGGS_labrad.clients import createTrunk
# connect to labrad
cxn = labrad.connect()

rf = cxn.rf_server
print('starting now')
sleep(7200)
rf.select_device()
rf.gpib_write('AM:OFF')
th=rf.gpib_query('AM?')
