@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof

# get current module to set server variables
from sys import modules
current_module=modules[__name__]

# connect to labrad
import labrad
cxn = labrad.connect()

# list of servers we want and their shorthand names
server_dict = {
        'ni': 'niops03_server', 'tt': 'twistorr74_server', 'ls': 'lakeshore336_server',
        'rga': 'rga_server', 'rf': 'rf_server', 'sls': 'sls_server', 'aq': 'artiq_server',
        'pmt': 'pmt_server'
        }

for servers in server_dict.items():
    try:
        # set server as variable
        setattr(current_module, servers[0], cxn[servers[1]])
    except Exception as e:
        print("Server unavailable:", e)