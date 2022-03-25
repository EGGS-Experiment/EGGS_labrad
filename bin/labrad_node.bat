:: LabRAD Node
:: Starts a LabRAD node and all necessary components

@ECHO OFF
SETLOCAL EnableDelayedExpansion

REM: Prepare LabRAD CMD
CALL %EGGS_LABRAD_ROOT%\bin\prepare_labrad.bat

REM: Parse arguments
SET /A argCount=1
SET /A ip_ind=0
SET /A raw_flag=0
FOR %%x IN (%*) DO (
    SET /a argCount+= 1
    IF "%%x"=="--ip" (SET /a ip_ind=!argCount!)
    IF "%%x"=="-r" (SET /a raw_flag=1)
    IF "%%x"=="-h" (GOTO HELP)
    IF "%%x"=="--help" (GOTO HELP)
)

IF NOT %ip_ind%==0 (CALL SET ip_addr=%%%ip_ind%%
) ELSE (CALL SET ip_addr=%LABRADHOST%)

REM: Core Servers
START "Labrad Web GUI" /min %HOME%\Code\scalabrad-web-server-2.0.6\bin\labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%\Code\pylabrad\labrad\node\__init__.py"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667

REM: Don't open any servers if raw flag is active
IF "%%x"=="-r" (GOTO SHELL)

REM: Device Busses
TIMEOUT 5 > NUL && START /min CMD /c %EGGS_LABRAD_ROOT%\bin\utils\start_labrad_devices.bat

REM: Clients
START /min CMD /c %EGGS_LABRAD_ROOT%\bin\utils\start_labrad_clients.bat

:SHELL

REM: Run all device servers as specified, then open a python shell to begin
CALL %EGGS_LABRAD_ROOT%\bin\labrad_cxn.bat

GOTO EOF

:HELP
@ECHO usage: labrad_node [-h] [-r] [--ip IP_ADDRESS]
@ECHO:
@ECHO LabRAD Node
@ECHO Optional Arguments:
@ECHO    -h, --help          show this message and exit
@ECHO    -r                  start only the labrad core (i.e. the manager, a node, and the Chromium GUI)
@ECHO    --ip                connect to the labrad manager at the given IP address (default: %LABRADHOST%)
@ECHO:

:EOF

REM: Unset variables
SET "argCount="
SET "raw_flag="
SET "ip_ind="
SET "ip_addr="
