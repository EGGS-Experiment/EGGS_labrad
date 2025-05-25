#Grants's stuff
import labrad
import time


cxn=labrad.connect()
dc=cxn.dc_server
#dc.voltage(23,0)
#dc.voltage_fast(24,1)

#dc.voltage(23,18.277)
#dc.voltage_fast(27,1)
dc.voltage_fast(23, 16.8)

time.sleep(0.9)
#dc.voltage(23,0)
#dc.voltage_fast(27,292)
dc.voltage_fast(23, 2.8)
#dc.toggle(23,0)
#dc.toggle(27,1)
dc.toggle(23,1)
cxn.disconnect()
