:: ARTIQ Start
:: Starts all components necessary for running ARTIQ

@ECHO OFF

@REM: MOVE TO ARTIQ ROOT
CD %ARTIQ_ROOT%
CALL conda activate artiq

SETLOCAL EnableDelayedExpansion

@REM: Parse arguments
SET /a argCount=1
SET /a ddb_ind=0
SET "ddb_name="
SET /a ip_ind=0
SET "ip_addr="

FOR %%x IN (%*) DO (
    SET /a argCount+= 1
    IF "%%x"=="--ddb" (SET /a ddb_ind=!argCount!)
    IF "%%x"=="--ip" (SET /a ip_ind=!argCount!)
    IF "%%x"=="-h" (GOTO HELP)
    IF "%%x"=="--help" (GOTO HELP)
)


@REM: Set arguments
IF NOT %ddb_ind%==0 (CALL SET ddb_name=%ARTIQ_ROOT%\%%%ddb_ind%%
) ELSE (CALL SET ddb_name=%ARTIQ_DDB%)

IF NOT %ip_ind%==0 (CALL SET ip_addr=%%%ip_ind%%
) ELSE (CALL SET ip_addr=%ARTIQ_HOST%)


@REM: Start ARTIQ interface
TIMEOUT 3 > NUL && START "ARTIQ Master" /min CMD "/c artiq_master -g -r %ARTIQ_ROOT%/repository --device-db %ARTIQ_ROOT%\%ddb_name% --bind=%ip_addr%"
@REM: START "ARTIQ Master" CMD "/c artiq_master --device-db %ARTIQ_ROOT%\%ddb_name% --bind=%ip_addr%"
TIMEOUT 3 > NUL && START "ARTIQ Dashboard" /min CMD "/c TIMEOUT 2 && CALL artiq_dashboard"
TIMEOUT 3 > NUL && START "ARTIQ Controller Manager" /min CMD "/k TIMEOUT 2 && artiq_ctlmgr"

GOTO EOF

:HELP
@ECHO usage: artiq_start [-h] [--ip IP_ADDRESS] [-ddb DEVICE_DB]
@ECHO:
@ECHO ARTIQ Starter
@ECHO Optional Arguments:
@ECHO    -h, --help          show this message and exit
@ECHO    --ip                bind the artiq_master to the given IP address (default: %ARTIQ_HOST%)
@ECHO    --ddb               device database file (default: %ARTIQ_DDB%)
@ECHO

:EOF
@REM: Unset variables
SET "argCount="
SET "ddb_ind="
SET "ip_ind="
SET "ddb_name="
SET "ip_addr="
