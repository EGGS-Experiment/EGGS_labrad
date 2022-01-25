::Starts all LabRAD servers necessary for device communication

@ECHO OFF

START "GPIB Bus Server" /min CMD "/k activate labart && TIMEOUT 2 && python %LABRAD_ROOT%\EGGS_labrad\servers\gpib\gpib_bus_server.py"
START "Serial Bus Server" /min CMD "/k activate labart && python %LABRAD_ROOT%\EGGS_labrad\servers\serial\serial_bus_server.py"