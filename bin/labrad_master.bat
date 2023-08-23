:: LabRAD Master
::  Starts the LabRAD Master.

@ECHO OFF
@SETLOCAL EnableDelayedExpansion

@REM: Set file home
SET PROG_HOME=%~dp0

@REM: Prepare LabRAD CMD environment
CALL "%PROG_HOME%\labrad_prepare.bat"

@REM: Parse arguments for server activation
SET /A server_flag=0
SET /A raw_flag=0
FOR %%x IN (%*) DO (
    IF "%%x"=="-s" (SET /a server_flag=1)
    IF "%%x"=="-r" (SET /a raw_flag=1)
    IF "%%x"=="-h" (GOTO HELP)
    IF "%%x"=="--help" (GOTO HELP)
)


@REM: Start core LabRAD tool suite
IF %raw_flag%==0 (
    @REM: Set up syslog for Grafana
    START "Loki Syslog" /min CMD /k " "%HOME%\Code\loki\loki-windows-amd64.exe" -config.expand-env=true -config.file "%PROG_HOME%\logging\loki-syslog-config.yaml" "
    START "Promtail Syslog - LabRAD" /min CMD /k " "%HOME%\Code\loki\promtail-windows-amd64.exe" -config.file "%PROG_HOME%\logging\promtail-syslog-config.yaml" "
    START "Promtail - ARTIQ" /min CMD /k " "%HOME%\Code\loki\promtail-windows-amd64.exe" -config.file "%PROG_HOME%\logging\promtail-artiq-config.yaml" "

    @REM: Set up autosaver
    START "LabRAD Autosaver" /min "%PROG_HOME%\labrad_autosaver.bat"

    @REM: Set up port forwarder to allow access via http
    START "LabRAD Forwarder" /min CMD /k "activate labart && python "%PROG_HOME%\labrad_forwarder.py" 8682:127.0.0.1:7682"

    @REM: Start core ARTIQ managers
    START /min CMD /c "%PROG_HOME%\artiq_start.bat"
)

@REM: Core Servers
START "LabRAD Manager" /min "%PROG_HOME%\scalabrad_minimum_startup.bat" --tls-required false
START "LabRAD Web GUI" /min "%PROG_HOME%\scalabrad-web_minimum_startup.bat"
START "LabRAD Node" /min CMD /k "activate labart && python "%HOME%\Code\pylabrad\labrad\node\__init__.py" -x %LABRADHOST%:%EGGS_LABRAD_SYSLOG_PORT%"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:3000


@REM: Run all device servers as specified, then open the relevant python shell
IF %server_flag%==1 (
    @REM: Start certain LabRAD servers in a local CMD window
    TIMEOUT 8 > NUL && START /min CMD /c "%PROG_HOME%\utils\start_labrad_servers.bat"

    @REM: Start ARTIQ Server (for LabRAD interfacing)
    START "ARTIQ Server" /min CMD "/k activate labart3 && python %EGGS_LABRAD_ROOT%\EGGS_labrad\servers\ARTIQ\artiq_server.py"

    @REM: Start relevant LabRAD clients (e.g. EGGS GUI, RSG Client, DDS Client)
    START /min CMD /c "%PROG_HOME%\utils\start_labrad_clients.bat"

    @REM: Open a command-line python connection to LabRAD
    TIMEOUT 8 > NUL && CALL "%PROG_HOME%\server_cxn.bat"
) ELSE ( CALL "%PROG_HOME%\labrad_cxn.bat" )

@REM: End of file. Skip the help message unless the -h/--help flag is passed.
GOTO EOF


@REM: Display help message
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
