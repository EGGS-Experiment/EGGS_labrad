@ECHO OFF

START "Labrad Web GUI" /min %HOME%/Code/scalabrad-web-server-2.0.6/bin/labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%/Code/pylabrad/labrad/node/__init__.py"
START "GPIB Bus Server" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/gpib/gpib_bus_server.py"
START "Serial Server" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/serial/serial_server.py"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667