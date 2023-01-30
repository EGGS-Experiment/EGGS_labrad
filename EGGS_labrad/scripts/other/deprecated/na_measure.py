"""
Measure a value from the network analyzer.
"""

import labrad
from time import time, sleep
from datetime import datetime
import pyvisa
from EGGS_labrad.clients import createTrunk

rm=pyvisa.ResourceManager()
lr=rm.list_resources()
na=rm.open_resource(lr[-1])

cxn = labrad.connect()
#na=cxn.network_analyzer_server
#na.select_device()
yz=na.query('*IDN?')
print('id: {}'.format(yz))

# connect to eggs labrad
dv = cxn.data_vault
cr_dv = cxn.context()

# create dataset
trunk = createTrunk('HR Drift Characterization')
dv.cd(trunk, True, context=cr_dv)

dv.new('HR Drift', [('Elapsed time', 's')], [('Channel 1', 'Signal Min', 'dBm')], context=cr_dv)
val = na.query('CALC1:MARK:FUNC:RES?')
print(val)

# start recording
starttime = time()
while True:
    val = na.query('CALC1:MARK:FUNC:RES?')
    elapsedtime = time() - starttime
    dv.add(elapsedtime, float(val), context=cr_dv)
    sleep(0.5)
