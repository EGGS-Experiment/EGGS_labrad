# connect to labrad
import labrad
cxn = labrad.connect()

# todo: make real script
# todo: allow general masses

# general import
from numpy import arange
from time import time, sleep
from EGGS_labrad.clients import createTrunk
start_time = time()

# get servers
rga = cxn.rga_server
dv = cxn.data_vault
cr = cxn.context()

# parameters
(mass_initial, mass_final, mass_steps) = (1, 50, 1)
dv_dep_var = [(':.01f amu'.format(mass), 'Pressure', 'Torr')
              for mass in arange(mass_initial, mass_final + mass_steps, mass_steps)]

# create dataset
trunk_tmp = createTrunk("RGA Continuous Measurement")
dv.cd(trunk_tmp, True, context=cr)
dv.new('RGA Continuous Measurement', [('Elapsed time', 't')], dv_dep_var, context=cr)

# set up rga scan
rga.scan_mass_initial(mass_initial)
rga.scan_mass_final(mass_final)
#rga.scan_mass_steps(mass_steps)

# turn on rga
rga.ionizer_filament('*')

# start recording
starttime = time()
while time() - start_time < 3600:
    # take rga data
    res = rga.scan_start('h', 1)
    res = list(res[1])
    res = [time() - start_time] + res
    #print(res)
    dv.add(res, context=cr)
    sleep(5)
