class multiplexer_config(object):
    """
    Multiplexer client configuration file.
    Attributes
    ----------
    channels: dict
    {
        channel_name: (signal_port, frequency, display_location, stretched, display_pid, dac_port, dac_rails, displayPattern)
    }
    """

    channels = {
        '397nm': (5, '755.22244', (0, 1), False, False, 4, [-4, 4], True),
        '423nm': (6, '709.07767', (0, 2), True, False, 5, [-4, 4], True),
        # '854nm': (13, '350.86265', (0, 3), True, False, 12, [-4, 4], True)
        # '866nm': (14, '346.00002', (0, 4), True, False, 13, [-4, 4], True),
    }

    ip = '10.97.111.8'
