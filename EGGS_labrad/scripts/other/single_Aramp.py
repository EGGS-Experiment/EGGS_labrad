import labrad
import time

servers = {'amo8': 'DC Server'}

cxn=labrad.connect()
dc=cxn.dc_server
dc.voltage(23,0)
dc.voltage(24,0)

dc.toggle(23,1)
dc.toggle(24,1)
dc.voltage(23,17+.277)
dc.voltage(24,17-.115)

time.sleep(.2)

dc.voltage(23,0)
dc.voltage(24,0)
dc.toggle(23,0)
dc.toggle(24,0)