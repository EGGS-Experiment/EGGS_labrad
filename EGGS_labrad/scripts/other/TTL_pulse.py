import labrad
import time

cxn=labrad.connect()
aq=cxn.artiq_server

#aq.ttl_set("ttl22", 1)
#time.sleep(.2)
aq.ttl_set("ttl20", 1)