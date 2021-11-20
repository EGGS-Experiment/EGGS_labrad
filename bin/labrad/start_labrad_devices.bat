@ECHO OFF

START "GPIB Bus Server" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/gpib/gpib_bus_server.py"
START "Serial Bus Server" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/serial/serial_bus_server.py"