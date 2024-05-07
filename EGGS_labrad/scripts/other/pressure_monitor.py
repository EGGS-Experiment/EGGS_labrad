"""
PRESSURE MONITORING FOR LOADING HCl
"""
import os
import time
import labrad

# SETUP VARIABLES
_THRESHOLD_PRESSURE_MBAR =  3.e-6
_POLL_INTERVAL_S =          1.0
_RUN_TIME_S =               300.0

# establish labrad server connections
cxn = labrad.connect()
tt = cxn.twistorr74_server


# set up audio warning
_PLAYSOUND_ENABLE = False
try:
    from playsound import playsound
    _SOUND_PATH_WARNING = os.path.join(
        os.environ['EGGS_LABRAD_ROOT'],
        'EGGS_labrad\\clients\\wavemeter_client\\channel_unlocked_short.mp3'
    )

except Exception as e:
    print('Warning: playsound package not installed.')
    raise e

# main loop
try:

    # set up loop variables
    time_start_stamp = time.time()
    time_end_stamp = time_start_stamp + _RUN_TIME_S

    # polling loop
    while time.time() < time_end_stamp:

        # check if magnetron pressure has exceeded threshold
        if tt.pressure() >= _THRESHOLD_PRESSURE_MBAR:
            # play warning sound if above threshold and exit loop
            for i in range(3):
                playsound(_SOUND_PATH_WARNING)
            break
        else:
            time.sleep(_POLL_INTERVAL_S)



except Exception as e:
    print("Error: {}".format(e))


