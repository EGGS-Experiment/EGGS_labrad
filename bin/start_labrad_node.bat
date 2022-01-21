::Starts a LabRAD node and all necessary components

@ECHO OFF

REM: Prepare LabRAD CMD
CALL %LABRAD_ROOT%\bin\prepare_labrad.bat

REM: Core
START "Labrad Web GUI" /min %HOME%\Code\scalabrad-web-server-2.0.6\bin\labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%\Code\pylabrad\labrad\node\__init__.py"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667

REM: Device Buses
START /min CMD /c %LABRAD_ROOT%\bin\labrad\start_labrad_devices.bat

REM: Clients
START /min CMD /c %LABRAD_ROOT%\bin\labrad\start_labrad_clients.bat