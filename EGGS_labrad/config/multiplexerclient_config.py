class multiplexer_config(object):
    """
    Multiplexer client configuration file.
    Attributes
    ----------
    channels: dict
    {
        channel_name: (signal_port, frequency, display_location, display_PID, dac_port, dac_rails)
    }
    """
    ip = '10.97.111.8'

    channels = {
        '397nm': (6,    '755.22244',    (0, 1), True,   5,  [-4, 4]),
        '423nm': (5,    '709.07767',    (0, 2), True,   4,  [-4, 4]),
        '854nm': (14,   '350.862655',   (0, 3), True,   8,  [-4, 4]),
        '866nm': (13,   '345.999945',   (0, 4), True,   7,  [-4, 4]),
    }

    alarm_threshold_mhz = 1
