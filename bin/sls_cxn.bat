@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof
import labrad
cxn = labrad.connect()
tt=cxn.sls_server
tt.select_device('hengfachuen','COM6')