@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof
import labrad
cxn = labrad.connect()
sls=cxn.sls_server
sls.select_device('hengfachuen','COM6')