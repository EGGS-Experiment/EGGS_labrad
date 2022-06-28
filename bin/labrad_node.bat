:: LabRAD Node
::  Starts a LabRAD node and all necessary components.

@ECHO OFF
@SETLOCAL EnableDelayedExpansion

@REM: Set file home
SET PROG_HOME=%~dp0

@REM: Prepare LabRAD CMD
CALL %PROG_HOME%\prepare_labrad.bat

@REM: Parse arguments
SET /A argCount=1
SET /A ip_ind=0
SET /A dev_flag=0
FOR %%x IN (%*) DO (
    SET /A argCount+= 1
    IF "%%x"=="--ip" (SET /a ip_ind=!argCount!)
    IF "%%x"=="-h" (GOTO HELP)
    IF "%%x"=="--help" (GOTO HELP)
    @REM: IF "%%x"=="-w" (SET /a
)

IF NOT %ip_ind%==0 (
    CALL SET ip_addr=%%%ip_ind%%
) ELSE (
    CALL SET ip_addr=%LABRADHOST%
)


@REM: Core Servers
START "LabRAD Web GUI" /min %PROG_HOME%\scalabrad-web_minimum_startup.bat
START "LabRAD Node" /min CMD "/k activate labart && python %HOME%\Code\pylabrad\labrad\node\__init__.py -s -x %LABRADHOST%:%EGGS_LABRAD_SYSLOG_PORT% -k True"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://%LABRADHOST%:3000

@REM: ARTIQ Dashboard
START "ARTIQ Dashboard" /min CMD "/k activate artiq && CALL artiq_dashboard -s %LABRADHOST%"

@REM: Clients
TIMEOUT 10 > NUL && START /min CMD /c %PROG_HOME%\utils\start_labrad_clients.bat

@REM: Run all device servers as specified, then open a python shell to begin
CALL %PROG_HOME%\labrad_cxn.bat

GOTO EOF

:HELP
@ECHO usage: labrad_node [-h] [--ip IP_ADDRESS]
@ECHO:
@ECHO LabRAD Node
@ECHO Optional Arguments:
@ECHO    -h, --help          show this message and exit
@ECHO    --ip                connect to the labrad manager at the given IP address (default: %LABRADHOST%)
@ECHO:

:EOF
@ENDLOCAL
