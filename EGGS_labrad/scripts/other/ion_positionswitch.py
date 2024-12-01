"""
Use pulsing of the A-ramp to swap ion positions
"""
import labrad
from time import time, sleep
from datetime import datetime
from EGGS_labrad.config.dc_config import dc_config

import atexit
import asyncio
import traceback
from asyncio import new_event_loop, set_event_loop
from sipyco.pc_rpc import Client, AsyncioClient
from sipyco.asyncio_tools import atexit_register_coroutine
from artiq.coredevice.comm_moninj import CommMonInj, TTLOverride

# todo: integrate camera

# experiment parameters
exp_name = 'ion_positionswitch_aramp'

# a-ramp parameters
ARAMP_VOLTAGE_LOW =     2.8
ARAMP_VOLTAGE_HIGH =    8.5
ARAMP_DELAY_S =         0.9

# ARTIQ moninj parameters
ARTIQ_MASTER_IP =       '192.168.1.48'
ARTIQ_MONINJ_PORT =     1383
TTL_CHAN_397 =          0x27
TTL_CHAN_866 =          0x28
TTL_CHAN_854 =          0x29

# aperture parameters
APERTURE_POS_CLOSE =    2888


'''
MAIN LOOP
'''

try:
    time_start = time()

    '''
    Connect to devices
    '''
    # connect to labrad
    cxn = labrad.connect()
    print("CONNECT: LabRAD connection successful.")

    # get labrad servers
    dc =    cxn.dc_server
    ell =   cxn.elliptec_server
    print("CONNECT: LabRAD server connection successful.")

    # set up event loop for ARTIQ MonInj
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # attempt connection to MonInj
    try:
        moninj = CommMonInj(None, None, None)
        atexit_register_coroutine(moninj.close, loop=loop)
        loop.run_until_complete(
            moninj.connect(
                ARTIQ_MASTER_IP, ARTIQ_MONINJ_PORT
            )
        )
    except Exception:
        print("Failed to connect to moninj. Is aqctl_moninj_proxy running?", exc_info=True)
        raise
    else:
        print("CONNECT: MonInj connection successful.")

    def ttl_set(channel, mode):
        if mode == "0":
            moninj.inject(channel, TTLOverride.level.value, 0)
            moninj.inject(channel, TTLOverride.oe.value, 1)
            moninj.inject(channel, TTLOverride.en.value, 1)
        elif mode == "1":
            moninj.inject(channel, TTLOverride.level.value, 1)
            moninj.inject(channel, TTLOverride.oe.value, 1)
            moninj.inject(channel, TTLOverride.en.value, 1)
        elif mode == "exp":
            moninj.inject(channel, TTLOverride.en.value, 0)
        else:
            raise ValueError


    '''
    Set up devices
    '''
    # open aperture
    ell.move_home()
    # sleep(0.5)

    # set up DC server
    dc.polling(False)
    dc.remote(True)
    dc.alarm(False)
    ARAMP_CHAN = dc_config.channeldict['A-Ramp 2']['num']
    print("SETUP: LabRAD device setup successful.")

    # set up moninj/TTL values
    ttl_set(TTL_CHAN_397, "1")
    ttl_set(TTL_CHAN_866, "1")
    ttl_set(TTL_CHAN_854, "1")
    print("SETUP: MonInj setup successful.")


    '''
    Main Sequence
    '''
    try:
        # todo: check ion position on camera in a loop
        # pulse A-ramp
        print("RUN: A-Ramping...")
        dc.voltage_fast(ARAMP_CHAN, ARAMP_VOLTAGE_HIGH)
        sleep(ARAMP_DELAY_S)
        dc.voltage_fast(ARAMP_CHAN, ARAMP_VOLTAGE_LOW)
        sleep(2.0)

    except Exception as e:
        print("\tError: {}".format(e))
        print(traceback.format_exc())

    finally:
        # ensure devices are reset correctly
        ell.move_absolute(APERTURE_POS_CLOSE)
        print("CLEANUP: LabRAD cleanup successful.")

        ttl_set(TTL_CHAN_397, "exp")
        ttl_set(TTL_CHAN_866, "exp")
        ttl_set(TTL_CHAN_854, "exp")
        print("CLEANUP: MonInj cleanup successful.")

except Exception as e:
    print("\tError: {}".format(e))
    print(repr(e))
    print(traceback.format_exc())

finally:
    # disconnect from system
    cxn.disconnect()
    print("CLEANUP: LabRAD disconnect successful.")

    # print runtime
    time_stop = time()
    print("Run time: {:.3g} s".format(time_stop - time_start))
