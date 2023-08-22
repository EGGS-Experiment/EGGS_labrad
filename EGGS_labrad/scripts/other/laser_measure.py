"""
Measure a value from the wavemeter.
"""

import labrad
from time import time, sleep
from datetime import datetime

from EGGS_labrad.clients import createTrunk

name_tmp = "Wavemeter Frequency Measurement"


# connect to eggs labrad
cxn_eggs = labrad.connect()
dv = cxn_eggs.data_vault
cr_dv = cxn_eggs.context()


# connect to wavemeter labrad
cxn_wm = labrad.connect('10.97.111.8', password='lab')
wm = cxn_wm.multiplexerserver
cr_wm = cxn_wm.context()

# create dataset
date = datetime.now()
year = str(date.year)
trunk_tmp = createTrunk(name_tmp)
dv.cd(trunk_tmp, True, context=cr_dv)
dv.new(
    name_tmp,
    [('Time', 's')],
    [('393nm Frequency', 'Frequency', 'THz')],
    context=cr_dv
)
print('Data vault successfully setup.')

# start recording
starttime = time()
while True:
    freq = wm.get_frequency(4)
    elapsedtime = time() - starttime
    dv.add(elapsedtime, freq, context=cr_dv)
    sleep(1)
