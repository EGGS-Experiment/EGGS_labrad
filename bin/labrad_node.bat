::Starts a LabRAD node and all necessary components

@ECHO OFF
SETLOCAL EnableDelayedExpansion

REM: Prepare LabRAD CMD
CALL %LABRAD_ROOT%\bin\prepare_labrad.bat

REM: Parse arguments
SET /a argCount=1
SET /a ip_ind=0
FOR %%x IN (%*) DO (
    SET /a argCount += 1
    IF "%%x"=="-ip" (SET /a ip_ind=!argCount!)
)
IF NOT %ip_ind%==0 (CALL SET ip_addr=%%%ip_ind%%
) ELSE (CALL SET ip_addr=%LABRADHOST%)

REM: Core Servers
START "Labrad Web GUI" /min %HOME%\Code\scalabrad-web-server-2.0.6\bin\labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%\Code\pylabrad\labrad\node\__init__.py"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667

REM: Device Buses
START /min CMD /c %LABRAD_ROOT%\bin\labrad\start_labrad_devices.bat

REM: Clients
START /min CMD /c %LABRAD_ROOT%\bin\labrad\start_labrad_clients.bat

REM: Unset variables
SET "argCount="
SET "ip_ind="
SET "ip_addr="
