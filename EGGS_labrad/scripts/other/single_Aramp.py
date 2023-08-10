#Grants's stuff
import labrad
import time

servers = {'amo8': 'DC Server'}

cxn=labrad.connect()
dc=cxn.dc_server
#dc.voltage(23,0)
#dc.voltage_fast(24,1)

#dc.toggle(23,1)
#dc.toggle(24,1)
#dc.voltage(23,18+.277)
#dc.voltage_fast(27,1)
dc.voltage_fast(23,6)

time.sleep(.25)

#dc.voltage(23,0)
#dc.voltage_fast(27,292)
dc.voltage_fast(23,0)
#dc.toggle(23,0)
#dc.toggle(27,1)
dc.toggle(23,1)