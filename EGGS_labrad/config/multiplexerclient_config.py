class multiplexer_config(object):
    """
    Multiplexer client configuration file.
    Attributes
    ----------
    channels: dict
    {
        channel_name: (signal_port, frequency, display_location, dac_port, dac_rails)
    }
    """

    channels = {
        '397nm': (5, '755.22244', (0, 1), True, 4, [-4, 4]),
        '423nm': (6, '709.07767', (0, 2), True, 5, [-4, 4]),
        '854nm': (13, '350.862655', (0, 3), True, 12, [-4, 4]),
        '866nm': (14, '345.999945', (0, 4), True, 13, [-4, 4]),
    }

    ip = '10.97.111.8'
