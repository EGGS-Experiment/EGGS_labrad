@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof

import labrad
cxn = labrad.connect()

# Cryovac
ni=cxn.niops03_server
tt=cxn.twistorr74_server
ls=cxn.lakeshore336_server
rga=cxn.rga_server

# Trap
rf=cxn.rf_server

# Lasers
sls=cxn.sls_server

# ARTIQ
# aq=cxn.artiq_server