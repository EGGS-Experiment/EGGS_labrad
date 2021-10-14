@ECHO OFF

::start "GPIB Server" /min cmd "/k activate barium && python %HOME%/Code/servers/gpib_server.py"
::start "GPIB Device Manager" /min cmd "/k activate barium && python %HOME%/Code/servers/gpib_device_manager.py"
::start "Serial Server" /min cmd "/k activate barium && python %HOME%/Code/servers/serial_server.py"

start "GPIB Server" /min cmd "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/gpib/gpib_server.py"
start "GPIB Device Manager" /min cmd "/k activate labart && TIMEOUT 2 && python %HOME%/Code/EGGS_labrad/lib/servers/gpib/gpib_device_manager.py"
start "Serial Server" /min cmd "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/serial/serial_server.py"