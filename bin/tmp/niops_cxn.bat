@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof
import labrad
cxn = labrad.connect()
ni=cxn.niops03_server
ni.device_select('causewaybay','COM8')