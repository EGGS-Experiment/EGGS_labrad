#!/usr/bin/python

# get current module to set server variables
from sys import modules
current_module=modules[__name__]

# connect to labrad
import labrad
cxn = labrad.connect()

# connect to wavemeter labrad
# cxn_wm = labrad.connect('10.97.111.8',password='lab')
# wm = cxn_wm.multiplexerserver

# list of servers we want and their shorthand names
server_dict = {

    # MANAGER
    'mgr':          'manager',
    'reg':          'registry',

    # CORE
    'ss':           'script_scanner',
    'pv':           'parameter_vault',
    'dv':           'data_vault',

    # NODES
    'mk':           'node_mongkok',
    'lh':           'node_lahaina',
    'cw':           'node_causewaybay',
    'hf':           'node_hengfachuen',

    # GPIB
    'gpib':         'gpib_device_manager',
    'mk_gpib':      'mongkok_gpib_bus',
    'lh_gpib':      'lahaina_gpib_bus',
    'hf_gpib':      'hengfachuen_gpib_bus',
    'cw_gpib':      'causewaybay_gpib_bus',

    # SERIAL
    'mk_ser':       'mongkok_serial_server',
    'lh_ser':       'lahaina_serial_server',
    'cw_ser':       'causewaybay_serial_server',
    'hf_ser':       'hengfachuen_serial_server',

    # CRYOVAC
    'ni':           'niops03_server',
    'tt':           'twistorr74_server',
    'ls':           'lakeshore336_server',
    'rga':          'rga_server',

    # SCIENCE
    'rf':           'rf_server',
    'dc':           'dc_server',
    'aq':           'artiq_server',

    # LASERS/IMAGING/OPTICS
    'sls':          'sls_server',
    'to':           'toptica_server',
    'cam':          'andor_server',
    'ell':          'elliptec_server',

    # TEST & MEASUREMENT/DAQ
    'os':           'oscilloscope_server',
    'fg':           'function_generator_server',
    'sa':           'spectrum_analyzer_server',
    'na':           'network_analyzer_server',
    'pm':           'power_meter_server',
    'gpp':          'gpp3060_server',
    'ke':           'keithley_2231a_server',
    'lj':           'labjack_server',

    # AMO BOXES
    'amo2':         'amo2_server',
    'amo3':         'amo3_server'
}

# create shortcuts
for servers in server_dict.items():
    try:
        # set server as variable
        setattr(current_module, servers[0], cxn[servers[1]])
    except Exception as e:
        print("Server unavailable:", e)

# try to import packages for convenience
# todo: import matplotlib.pyplot as plt
# todo: import numpy as np
# todo: import scipy as sp
