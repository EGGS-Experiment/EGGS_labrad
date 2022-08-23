"""
Measure a value from the network analyzer.
"""

import labrad
from time import time, sleep
from datetime import datetime


cxn = labrad.connect()
na=cxn.network_analyzer_server
na.select_device()


# connect to eggs labrad
dv = cxn.data_vault
cr_dv = cxn.context()

# create dataset
date = datetime.now()
year = str(date.year)
month = '{:02d}'.format(date.month)
trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
trunk2 = '{0:s}_{1:02d}:{2:02d}'.format('Network Analyzer Measure', date.hour, date.minute)
dv.cd(['', year, month, trunk1, trunk2], True, context=cr_dv)

dv.new('HR Drift', [('Elapsed time', 's')], [('Channel 1', 'Signal Min', 'dBm')], context=cr_dv)
val = na.marker_measure(1)
print(val)

# start recording
starttime = time()
while True:
    val = na.marker_measure(1)
    elapsedtime = time() - starttime
    dv.add(elapsedtime, float(val), context=cr_dv)
    sleep(0.5)
