@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof
import labrad
cxn = labrad.connect()