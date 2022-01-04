@ECHO OFF

::activate labart
::CD "%LABRAD_ROOT%"

::Core
START "Labrad Manager" /min %HOME%/Code/scalabrad-0.8.3/bin/labrad.bat --tls-required false
START "Labrad Web GUI" /min %HOME%/Code/scalabrad-web-server-2.0.6/bin/labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%/Code/pylabrad/labrad/node/__init__.py"
START "" "%ProgramFiles(x86)%/chrome-win/chrome.exe" http://localhost:7667

::Devices
START "GPIB Device Manager" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/gpib/gpib_device_manager.py"
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/labrad/start_labrad_devices.bat

::Experiments
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/labrad/start_labrad_experiments.bat

::Clients
::START "Script Scanner Client" /min CMD "/k activate labart && TIMEOUT 3 && python %HOME%\Code\EGGS_labrad\lib\clients\script_scanner_gui\script_scanner_gui.py"
START "Real Simple Grapher" /min CMD "/k activate labart && TIMEOUT 3 && python %HOME%\Code\RealSimpleGrapher\rsg.py"
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/labrad/start_labrad_clients.bat

::Servers
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/labrad/start_labrad_servers.bat

::ARTIQ
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/start_artiq.bat

