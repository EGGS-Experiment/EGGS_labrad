# general import
from time import time, sleep
from EGGS_labrad.clients import createTrunk

# connect to labrad
import labrad
cxn = labrad.connect()

# todo: make real script

# parameters
masses = (1, 2, 10, 40)

# get servers
rga = cxn.rga_server
dv = cxn.data_vault
cr = cxn.context()

# create independent variable array
dv_dep_var = [('{:.01f} amu'.format(mass), 'Pressure', 'Torr') for mass in masses]

# set up dataset
trunk_tmp = createTrunk("RGA Continuous Measurement")
dv.cd(trunk_tmp, True, context=cr)
dv.new('RGA Continuous Measurement', [('Elapsed time', 't')], dv_dep_var, context=cr)

# prepare to start
rga.ionizer_filament('*')
res = [0] * len(masses)
start_time = time()

# start recording
while time() - start_time < 3600:
    # take rga data
    for i, mass in enumerate(masses):
        res[i] = rga.smm_start(mass)
    #print(res)

    # add to dataset
    dv.add([time() - start_time] + res, context=cr)
    sleep(5)
