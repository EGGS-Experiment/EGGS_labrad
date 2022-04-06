"""
Measure a value from the wavemeter.
"""

import labrad
from time import time, sleep
from datetime import datetime

# connect to wavemeter labrad
cxn_wm = labrad.connect('10.97.111.8', password='lab')
wm = cxn_wm.multiplexerserver
cr_wm = cxn_wm.context()
# connect to eggs labrad
cxn_eggs = labrad.connect('localhost', password='lab')
dv = cxn_eggs.data_vault
cr_dv = cxn_eggs.context()

# create dataset
date = datetime.now()
year = str(date.year)
month = '{:02d}'.format(date.month)
trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
trunk2 = '{0:s}_{1:02d}:{2:02d}'.format('397 Measure', date.hour, date.minute)
dv.cd(['', year, month, trunk1, trunk2], True, context=cr_dv)
dv.new('397nm Power', [('Elapsed time', 's')], [('397', 'Frequency', 'THz')], context=cr_dv)

# start recording
starttime = time()
while True:
    freq = wm.get_frequency(14)
    elapsedtime = time() - starttime
    dv.add(elapsedtime, freq, context=cr_dv)
    sleep(5)
