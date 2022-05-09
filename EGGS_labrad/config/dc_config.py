class dc_config(object):
    """
    DC Client configuration file.
    Specifies which channels from the server to break out in the client
    and their layout.

    Attributes
    ----------
    headerLayout: (int, int)
        Specifies the layout of the header as [row, column].
        Starts from 0.

    channel_dict: dict
    {
        channel_name: (num, row, col)
    }
        Specifies the channels we want to be displayed
        on the client GUI and their location.

    """
    headerLayout = (1, 1)

    channeldict = {
        'E Endcap':     {'num': 1, 'row': 1, 'col': 0},
        'W Endcap':     {'num': 2, 'row': 2, 'col': 0},
        'V Shim':       {'num': 3, 'row': 1, 'col': 1},
        'H Shim':       {'num': 4, 'row': 2, 'col': 1},
        'A-Ramp 1':     {'num': 5, 'row': 1, 'col': 2},
        'A-Ramp 2':     {'num': 6, 'row': 2, 'col': 2}
    }
