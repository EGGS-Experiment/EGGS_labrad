import labrad

from numpy import arange
from time import time, sleep
start_time = time()

# connect to labrad
cxn_wm = labrad.connect('10.97.111.8', password='lab')
wm = cxn_wm.multiplexerserver
cr_wm = cxn_wm.context()

cxn_eggs = labrad.connect('localhost', password='lab')
dv = cxn_eggs.data_vault
cr_dv = cxn_eggs.context()


# create dataset
dv.cd(['', '397_2'], True, context=cr_dv)
dv.new('397nm Power', [('Elapsed time', 's')], [('397', 'Power', 'arb')], context=cr_dv)

# start recording
starttime = time()
while True:
    # take rga data
    freq = wm.get_amplitude(5)
    # print(res)
    elapsedtime = time() - starttime
    dv.add(elapsedtime, freq, context=cr_dv)
    sleep(5)

