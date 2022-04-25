@ECHO OFF & TITLE LabRAD Shell && conda activate labart && python -ix "%~f0" %* & goto :eof

import pyvisa

rm = pyvisa.ResourceManager()
lr = rm.list_resources()
print(lr)

rmor = rm.open_resource
