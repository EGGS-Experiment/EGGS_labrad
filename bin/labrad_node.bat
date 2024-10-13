:: LabRAD Node
::  Starts a LabRAD node and all necessary components.

@ECHO OFF
@SETLOCAL EnableDelayedExpansion

@REM Set file home
SET PROG_HOME=%~dp0

@REM Prepare LabRAD CMD environment
CALL "%PROG_HOME%\labrad_prepare.bat"

@REM Parse arguments
SET /A argCount=1
SET /A ip_ind=0
SET /A dev_flag=0
SET /A raw_flag=0
FOR %%x IN (%*) DO (
    SET /A argCount+= 1
    IF "%%x"=="-r" (SET /a raw_flag=1)
    IF "%%x"=="--ip" (SET /a ip_ind=!argCount!)
    IF "%%x"=="-h" (GOTO HELP)
    IF "%%x"=="--help" (GOTO HELP)
)

@REM Get desired IP address based on result of --ip argument
IF NOT %ip_ind%==0 (
    CALL SET ip_addr=%%%ip_ind%%
) ELSE (
    CALL SET ip_addr=%LABRADHOST%
)


@REM Core Servers
START "LabRAD Web GUI" /min "%PROG_HOME%\scalabrad-web_minimum_startup.bat"
START "LabRAD Node" /min CMD /k "activate labart && python "%HOME%\Code\pylabrad\labrad\node\__init__.py" -x %LABRADHOST%:%EGGS_LABRAD_SYSLOG_PORT%"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://%LABRADHOST%:3000

@REM Start LabRAD/ARTIQ clients
IF %raw_flag%==0 (
    @REM ARTIQ Dashboard
    START "ARTIQ MonInj Proxy" /min CMD /k "activate artiq8 && CALL aqctl_moninj_proxy 192.168.1.76"
    START "ARTIQ Dashboard" /min CMD /k "activate artiq8 && CALL artiq_dashboard -s %LABRADHOST%"

    @REM Start relevant LabRAD clients (e.g. EGGS GUI, RSG Client, DDS Client)
    TIMEOUT 10 > NUL && START /min CMD /c "%PROG_HOME%\utils\start_labrad_clients.bat"
)

@REM Open a command-line python connection to LabRAD
CALL "%PROG_HOME%\server_cxn.bat"

@REM End of file. Skip the help message unless the -h/--help flag is passed.
GOTO EOF


@REM Display help message
:HELP
@ECHO usage: labrad_node [-h] [--ip IP_ADDRESS]
@ECHO:
@ECHO LabRAD Node
@ECHO Optional Arguments:
@ECHO    -h, --help          show this message and exit
@ECHO    -r                  start only the labrad core without any GUIs (i.e. a node, and Chromium GUI)
@ECHO    --ip                connect to the labrad manager at the given IP address (default: %LABRADHOST%)
@ECHO:

:EOF
@ENDLOCAL
