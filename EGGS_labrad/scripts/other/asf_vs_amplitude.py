"""
Measure the power and amplitude of the DDS output
as a function of asf (amplitude scaling factor).
"""
import labrad
from time import sleep

from numpy import linspace
from EGGS_labrad.clients import createTrunk

name_tmp = 'ASF Characterization'
(dds_channel_amp, dds_channel_power) = ('urukul0_ch1', 'urukul0_ch3')
dds_frequency_hz = 100 * 1e6
dds_attenuation_dbm = 10
amp_range = linspace(1, 100, 100)
os_channel = 2


try:
    # connect to labrad
    cxn = labrad.connect()
    print('Connection successful.')

    # get servers
    aq = cxn.artiq_server
    os = cxn.oscilloscope_server
    sa = cxn.spectrum_analyzer_server
    dv = cxn.data_vault
    cr = cxn.context()
    print('Server connection successful.')

    # set up DDSs
    for dds_name in (dds_channel_amp, dds_channel_power):
        # set frequency
        aq.dds_frequency(dds_name, dds_frequency_hz)
        # set attenuation
        aq.dds_attenuation(dds_name, dds_attenuation_dbm)
        # turn on
        aq.dds_toggle(dds_name, 1)

    # set up oscilloscope
    os.select_device()
    os.measure_setup(1, os_channel, 'AMP')
    os.trigger_channel(os_channel)
    print('Oscilloscope setup successful.')

    # set up spectrum analyzer
    sa.select_device()
    sa.marker_toggle(1, True)
    print('Spectrum analyzer setup successful.')

    # create dataset
    trunk_tmp = createTrunk(name_tmp)
    dv.cd(trunk_tmp, True, context=cr)
    dv.new(
        'ASF Characterization',
        [('ASF', 'Scale')],
        [('DDS Amplitude', 'Amplitude', 'V'), ('DDS Power', 'Power', 'dBm')],
        context=cr
    )
    print('Dataset successfully created.')


    # MAIN SEQUENCE
    for amp_val in amp_range:
        # set asf
        aq.dds_amplitude(dds_channel_amp, amp_val)
        aq.dds_amplitude(dds_channel_power, amp_val)

        # scale oscope
        os.autoscale()

        # scale spec anal
        sa.autoset()
        sleep(5)

        # get oscope amplitude
        os_amplitude = os.measure(3)

        # get spec anal power
        sa_power = os.marker_amplitude(1)

        # record result
        dv.add(amp_val, os_amplitude, sa_power, context=cr)

except Exception as e:
    print('Error:', e)
