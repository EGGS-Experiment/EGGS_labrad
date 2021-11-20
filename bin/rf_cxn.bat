@ECHO OFF && conda activate labart && python -ix "%~f0" %* & goto :eof
import labrad
cxn = labrad.connect()
rf=cxn.rf_server
rf.select_device()