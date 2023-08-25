class dds_config(object):
    """
    DDS Client configuration file.
    Specifies waveform parameters for each DDS channel.

    Attributes
    ----------
    channeldict: dict
    {
        channel_name: (num, row, col)
    }
        Specifies the channels we want to be displayed
        on the client GUI and their location.

    """

    channeldict = {
        'urukul0_ch0':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul0_ch1':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul0_ch2':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul0_ch3':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul1_ch0':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul1_ch1':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul1_ch2':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul1_ch3':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul2_ch0':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul2_ch1':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul2_ch2':  {'ftw': 5, 'asf': 1, 'att_mu': 0},
        'urukul2_ch3':  {'ftw': 5, 'asf': 1, 'att_mu': 0}
    }
