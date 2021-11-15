@ECHO OFF

START /min CMD /c %HOME%/Code/EGGS_labrad/bin/start_labrad_core.bat
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/start_labrad_devices.bat
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/start_labrad_experiments.bat
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/start_labrad_clients.bat
START /min CMD /c %HOME%/Code/EGGS_labrad/bin/start_artiq.bat

activate labart