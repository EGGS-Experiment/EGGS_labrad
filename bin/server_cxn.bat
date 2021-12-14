@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof

import labrad
cxn = labrad.connect()

rf=cxn.rf_server
ni=cxn.niops03_server
tt=cxn.twistorr74_server
ls=cxn.lakeshore336_server
sls=cxn.sls_server
# aq=cxn.artiq_server

sls.set_polling(False)
ls.set_polling(False)
ni.set_polling(False)
tt.set_polling(False)