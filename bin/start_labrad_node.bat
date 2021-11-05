@ECHO OFF

::Starts all necessary components for a LabRAD node

::Core
START "Labrad Web GUI" /min %HOME%/Code/scalabrad-web-server-2.0.6/bin/labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%/Code/pylabrad/labrad/node/__init__.py"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667

::Device Buses
START "GPIB Bus Server" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/gpib/gpib_bus_server.py"
START "Serial Server" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/serial/serial_bus_server.py"

::Clients
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/start_labrad_clients.bat