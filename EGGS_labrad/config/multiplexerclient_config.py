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
        '397nm':        (5,    '755.221845',   (0, 1), True,   5,  [-4, 4]),
        '423nm':        (3,    '709.077640',   (0, 2), True,   4,  [-4, 4]),
        '729nm':        (12,   '411.041907',   (0, 5), False,  -1, [-4, 4]),
        '729nm - Inj.': (11,   '411.041826',   (0, 6), False,  -1, [-4, 4]),
        '854nm':        (14,   '350.862460',   (0, 4), True,   8,  [-4, 4]),
        '866nm':        (13,   '345.999860',   (0, 3), True,   7,  [-4, 4]),
    }

    alarm_threshold_mhz = 1e12
