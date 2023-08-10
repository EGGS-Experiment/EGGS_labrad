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

    channeldict: dict
    {
        channel_name: (num, row, col, max_voltage_v)
    }
        Specifies the channels we want to be displayed
        on the client GUI and their location.

    """
    headerLayout = (1, 1)

    channeldict = {
        'E Endcap':     {'num': 28, 'row': 1, 'col': 0, 'max_voltage_v': 400},
        'W Endcap':     {'num': 27, 'row': 2, 'col': 0, 'max_voltage_v': 400},
        'V Shim':       {'num': 20, 'row': 1, 'col': 1, 'max_voltage_v': 150},
        'H Shim':       {'num': 25, 'row': 2, 'col': 1, 'max_voltage_v': 150},
        'A-Ramp 1':     {'num': 24, 'row': 1, 'col': 2, 'max_voltage_v': 100},
        'A-Ramp 2':     {'num': 23, 'row': 2, 'col': 2, 'max_voltage_v': 100}
    }
