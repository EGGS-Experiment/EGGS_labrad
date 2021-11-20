@ECHO OFF

::Core
START "Labrad Manager" /min %HOME%/Code/scalabrad-0.8.3/bin/labrad.bat --tls-required false
START "Labrad Web GUI" /min %HOME%/Code/scalabrad-web-server-2.0.6/bin/labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%/Code/pylabrad/labrad/node/__init__.py"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667

::Devices
START "GPIB Device Manager" /min CMD "/k activate labart && python %HOME%/Code/EGGS_labrad/lib/servers/gpib/gpib_device_manager.py"
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/labrad/start_labrad_devices.bat

::Experiments
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/labrad/start_labrad_experiments.bat

::ARTIQ
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/start_artiq.bat

activate labart
::CD "%HOME%\Code\EGGS_labrad"