# connect to labrad
import labrad
cxn = labrad.connect()

from time import time, sleep
start_time = time()

# get servers
rga = cxn.rga_server
dv = cxn.data_vault
cr = cxn.context()

# create dataset
dv.cd(['', 'rgaActual'], True, context=cr)
dv.new('rgaActual', [('Elapsed time', 't')], [
    ('39.0 amu', 'Pressure', 'Torr'), ('39.1 amu', 'Pressure', 'Torr'), ('39.2 amu', 'Pressure', 'Torr'),
    ('39.3 amu', 'Pressure', 'Torr'), ('39.4 amu', 'Pressure', 'Torr'), ('39.5 amu', 'Pressure', 'Torr'),
    ('39.6 amu', 'Pressure', 'Torr'), ('39.7 amu', 'Pressure', 'Torr'), ('39.8 amu', 'Pressure', 'Torr'),
    ('39.9 amu', 'Pressure', 'Torr'), ('40.0 amu', 'Pressure', 'Torr'), ('40.1 amu', 'Pressure', 'Torr'),
    ('40.2 amu', 'Pressure', 'Torr'), ('40.3 amu', 'Pressure', 'Torr'), ('40.4 amu', 'Pressure', 'Torr'),
    ('40.5 amu', 'Pressure', 'Torr'), ('40.6 amu', 'Pressure', 'Torr'), ('40.7 amu', 'Pressure', 'Torr'),
    ('40.8 amu', 'Pressure', 'Torr'), ('40.9 amu', 'Pressure', 'Torr'), ('41.0 amu', 'Pressure', 'Torr')
    ], context=cr)
# can we open multiple datasets at same time?
# how to efficiently store horizontally large datasets?
# make into exp w/params
# create uninterruptible exp/script
rga.scan_mass_initial(2)
rga.scan_mass_final(60)
rga.ionizer_filament('*')
starttime = time()
while time() - start_time < 3600:
    # take rga data 35-45
    res = rga.scan_start('a', 1)
    res = list(res[1])
    # print(res)
    dv.add(time() - start_time,
           res[0], res[1], res[2], res[3], res[4], res[5], res[6],
           res[7], res[8], res[9], res[10], res[11], res[12], res[13],
           res[14], res[15], res[16], res[17], res[18], res[19], res[20], context=cr)
    sleep(5)

