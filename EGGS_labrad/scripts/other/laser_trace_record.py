"""
Continuously store traces from the wavemeter.
"""

import labrad
from time import time, sleep
from datetime import datetime
from numpy import linspace

name = "854_Trace"
num_points = 512
# range is linspace(0, 2000, num_points)


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
trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(name, date.hour, date.minute)
dv.cd(['', year, month, trunk1, trunk2], True, context=cr_dv)

independents = [('Elapsed Time', [1], 'v', 's')]
dependents = [('Trace', 'Wavemeter Trace', [num_points], 'v', 'arb')]
dv.new_ex(name, independents, dependents, context=cr_dv)

# start recording
starttime = time()
while True:
    trace = wm.get_wavemeter_pattern(13)
    trace = trace[0]
    elapsedtime = time() - starttime
    dv.add_ex([(elapsedtime, trace)], context=cr_dv)
    sleep(300)
