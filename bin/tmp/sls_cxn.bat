@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof
import labrad
cxn = labrad.connect()
sls=cxn.sls_server
sls.device_select('hengfachuen','COM6')