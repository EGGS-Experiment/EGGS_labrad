:: LabRAD Master
::  Starts the LabRAD Master.
::  @REM: todo: use %dp0 thing instead of setting eggs_labrad root and going from there; do we even needs eggs_labrad_root???
::  @REM: todo: change bin to frontend

@ECHO OFF
@SETLOCAL EnableDelayedExpansion

@REM: Set file home
SET PROG_HOME=%~dp0

@REM: Prepare LabRAD CMD
CALL %PROG_HOME%\prepare_labrad.bat

@REM: Parse arguments for server activation
SET /A server_flag=0
SET /A raw_flag=0
FOR %%x IN (%*) DO (
    IF "%%x"=="-s" (SET /a server_flag=1)
    IF "%%x"=="-r" (SET /a raw_flag=1)
    IF "%%x"=="-h" (GOTO HELP)
    IF "%%x"=="--help" (GOTO HELP)
)

@REM: Set up syslog for Grafana
START "Loki Syslog" /min CMD "/k %HOME%\Code\loki\loki-windows-amd64.exe -config.file %PROG_HOME%\logging\loki-syslog-config.yaml"
START "Promtail Syslog" /min CMD "/k %HOME%\Code\loki\promtail-windows-amd64.exe -config.file %PROG_HOME%\logging\promtail-syslog-config.yaml"

@REM: Set up autosaver
START "LabRAD Autosaver" /min %PROG_HOME%\labrad_autosaver.bat

@REM: Set up port forwarder to allow access via http
@REM: todo: check if we actually need to run activate labart here
START "LabRAD Forwarder" /min CMD "/k activate labart && python %PROG_HOME%\labrad_forwarder.py 8682:127.0.0.1:7682"

@REM: Core Servers
START "LabRAD Manager" /min %PROG_HOME%\scalabrad_minimum_startup.bat --tls-required false
START "LabRAD Web GUI" /min %PROG_HOME%\scalabrad-web_minimum_startup.bat
@REM: todo: check if we actually need to run activate labart here
START "LabRAD Node" /min CMD "/k activate labart && python %HOME%\Code\pylabrad\labrad\node\__init__.py -s -x %LABRADHOST%:%EGGS_LABRAD_SYSLOG_PORT% -k True"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:3000

@REM: ARTIQ
START /min CMD /c %PROG_HOME%\artiq_start.bat

@REM: Run all device servers as specified, then open a python shell to begin
IF %server_flag%==1 (
    TIMEOUT 8 > NUL && START /min CMD /c %PROG_HOME%\utils\start_labrad_servers.bat
)

@REM: Clients
START /min CMD /c %PROG_HOME%\utils\start_labrad_clients.bat

@REM: If all device servers are specified, open cxn with all servers assigned standard nicknames, otherwise run normal shell
IF %server_flag%==1 (
    TIMEOUT 8 > NUL && CALL %PROG_HOME%\server_cxn.bat
) ELSE ( CALL %PROG_HOME%\labrad_cxn.bat )


GOTO EOF
:HELP
@ECHO usage: labrad_master [-h] [-s] [-r]
@ECHO:
@ECHO LabRAD Master
@ECHO Optional Arguments:
@ECHO    -h, --help          show this message and exit
@ECHO    -s                  start all day-to-day device servers (specific to EGGS Experiment)
@ECHO    -r                  start only the labrad core (i.e. the manager, a node, and the Chromium GUI)
@ECHO:


:EOF
@ENDLOCAL
