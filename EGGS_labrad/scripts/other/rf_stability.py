from numpy import pi, sqrt, nan
cxn=labrad.connect()
os=cxn.oscilloscope_server
rf=cxn.rf_server
dc=cxn.dc_server

devices = os.list_devices()
for dev_id in devices:
    dev_name = dev_id[1]
    if ('DS1Z' in dev_name) and ('2765' in dev_name):
            os.select_device(dev_name)
        # connect to RF server
rf.select_device()

_PICKOFF_FACTOR = 300
_GEOMETRIC_FACTOR_RADIAL = 1
_GEOMETRIC_FACTOR_AXIAL = 0.06
_ELECTRODE_DISTANCE_RADIAL = 5.5e-4
_ELECTRODE_DISTANCE_AXIAL = 2.2e-3
_ION_MASS = 40 * 1.66053907e-27
_ELECTRON_CHARGE = 1.60217e-19

v_rf = os.measure_amplitude(1)
v_rf = 0.5 * v_rf * _PICKOFF_FACTOR
freq = rf.frequency()
Omega = freq / 2e6 # convert to Mathieu Omega
v_dc = dc.voltage(1)
a_param = _ELECTRON_CHARGE * (v_dc * _GEOMETRIC_FACTOR_AXIAL) / (_ELECTRODE_DISTANCE_AXIAL ** 2) / (2 * pi * freq) ** 2 / _ION_MASS
q_param = 2 * _ELECTRON_CHARGE * (v_rf * _GEOMETRIC_FACTOR_RADIAL) / (_ELECTRODE_DISTANCE_RADIAL ** 2) / (2 * pi * freq) ** 2 / _ION_MASS


wsecr = Omega * sqrt(0.5 * q_param ** 2 + a_param)

print(wsecr)


