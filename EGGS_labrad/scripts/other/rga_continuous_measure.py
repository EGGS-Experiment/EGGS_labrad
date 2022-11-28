# general import
from numpy import linspace
from time import time, sleep
from EGGS_labrad.clients import createTrunk

# connect to labrad
import labrad
cxn = labrad.connect()

# todo: make real script

# parameters
(mass_initial, mass_final, mass_steps) = (1, 50, 10)
scan_type = 'h'

# get servers
rga = cxn.rga_server
dv = cxn.data_vault
cr = cxn.context()

# set up rga scan
rga.scan_mass_initial(mass_initial)
rga.scan_mass_final(mass_final)
rga.scan_mass_steps(mass_steps)
num_points = rga.scan_points(scan_type)

# create array for independent variables (i.e. mass array)
dv_dep_var = [('{:.01f} amu'.format(mass), 'Pressure', 'Torr')
              for mass in linspace(mass_initial, mass_final, num_points)]

# create dataset
trunk_tmp = createTrunk("RGA Continuous Measurement")
dv.cd(trunk_tmp, True, context=cr)
dv.new('RGA Continuous Measurement', [('Elapsed time', 't')], dv_dep_var, context=cr)

# prepare to start
rga.ionizer_filament('*')
start_time = time()

# start recording
while time() - start_time < 3600:
    # take rga data
    res = rga.scan_start(scan_type, 1)
    res = list(res[1])
    #print(res)

    # add to dataset
    dv.add([time() - start_time] + res, context=cr)
    sleep(5)
