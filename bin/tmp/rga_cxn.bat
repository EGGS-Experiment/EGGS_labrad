@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof
import labrad
cxn = labrad.connect()
rga = cxn.rga_server
rga.device_select('causewaybay','COM4')