import pyvisa, csv
import numpy as np

#get device
rm = pyvisa.ResourceManager()
device = rm.list_resource()[1]
oscope = rm.open_resource(device)
oscope.timeout = 20000

#setup
oscope.write('DAT:SOUR CH1')
oscope.write('DAT:STAR 1')
oscope.write('DAT:STOP 100000')
oscope.write('DAT:ENC ASCI')
preamble = oscope.query('WFMO?')
print(preamble)

#get data and process
data = oscope.query('CURV?')
data = np.array(data.split(','), dtype = int)
preamblearr = preamble.split(';')

#write to csv
np.savetxt('data2.csv', data, delimiter = ';')

with open('data2pre.txt', 'w') as text_file:
    text_file.write(preamble)
    text_file.close()

