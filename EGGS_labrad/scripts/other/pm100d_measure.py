import labrad
from time import time, sleep
from datetime import datetime

# connect to eggs labrad
cxn = labrad.connect('localhost', password='lab')
dv = cxn.data_vault
pm = cxn.pm100d_server
cr_dv = cxn.context()

# create dataset
date = datetime.now()
year = str(date.year)
month = '{:02d}'.format(date.month)
trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
trunk2 = '{0:s}_{1:02d}:{2:02d}'.format('397 Measure', date.hour, date.minute)
dv.cd(['', year, month, trunk1, trunk2], True, context=cr_dv)
dv.new('397nm Power', [('Elapsed time', 's')], [('397', 'Power', 'arb')], context=cr_dv)

# set up recording
pm.wavelength(397)
pm.measure_start()

# start recording
starttime = time()
while True:
    pow = pm.power()
    elapsedtime = time() - starttime
    dv.add(elapsedtime, pow, context=cr_dv)
    sleep(5)

