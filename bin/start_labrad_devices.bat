@ECHO OFF

START "GPIB Bus Server" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/gpib/gpib_bus_server.py"
START "GPIB Device Manager" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/gpib/gpib_device_manager.py"
START "Serial Server" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/serial/serial_server.py"