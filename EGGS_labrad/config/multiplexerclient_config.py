class multiplexer_config(object):
    """
    Multiplexer client configuration file.
    Attributes
    ----------
    ip: IPv4 address of the computer to connect to.
    channels: configure wavemeter channel display as a dict:
        dict(
            channel_name: (
                signal_port, frequency_setpoint_thz, (display_x_position, display_y_position),
                enable_PID_interface, dac_port, [dac_voltage_min_v, dac_voltage_max_v]
            )
        )
        Note: set dac_port to -1 if no DAC port (for the frequency servo) is used for the channel.
    alarm_threshold_mhz: the maximum frequency drift from the configured frequency_setpoint_thz before
        an audible alarm is triggered in the GUI.
    """
    ip = '10.97.111.8'

    channels = {
        # name:         (port,  freq_set_thz,  (x_pos, y_pos), enable_PID_interface, dac_port, [dac_min_v, dac_max_v]
        '397nm':        (1,     '755.2218659',  (0, 1), True,   5,  [-4, 4]),
        '729nm (Inj)':  (11,    '411.0418223',  (0, 2), False,  -1, [-4, 4]),
        '423nm':        (4,     '709.0776400',  (0, 3), True,   4,  [-4, 4]),
        '854nm':        (14,    '350.8624600',  (0, 4), True,   8,  [-4, 4]),
        '866nm':        (13,    '345.9998600',  (0, 5), True,   7,  [-4, 4]),
        '729nm':        (12,    '411.0419021',  (0, 6), False,  -1, [-4, 4]),
    }

    alarm_threshold_mhz = 1e4
