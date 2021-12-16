@ECHO OFF

::Starts all necessary components for a LabRAD node

::Move into main labrad library so other windows will have it too
activate labart
CD "%LABRAD_ROOT%"

::Core
START "Labrad Web GUI" /min %HOME%\Code\scalabrad-web-server-2.0.6\bin\labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%\Code\pylabrad\labrad\node\__init__.py"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667

::Device Buses
START /min CMD /c %HOME%\Code\EGGS_labrad\bin\labrad\start_labrad_devices.bat

::Clients
START /min CMD /c %HOME%\Code\EGGS_labrad\bin\labrad\start_labrad_clients.bat