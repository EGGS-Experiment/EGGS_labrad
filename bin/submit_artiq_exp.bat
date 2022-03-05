::Submits an experiment to ARTIQ

@ECHO OFF

REM: MOVE TO ARTIQ ROOT
CD %ARTIQ_ROOT%
CALL conda activate labart2

SETLOCAL EnableDelayedExpansion

REM: Parse arguments
SET /a argCount=1
SET /a ddb_ind=0
SET "ddb_name="
SET /a ip_ind=0
SET "ip_addr="
FOR %%x IN (%*) DO (
    SET /a argCount+= 1
    IF "%%x"=="-ddb" (SET /a ddb_ind=!argCount!)
    IF "%%x"=="-ip" (SET /a ip_ind=!argCount!)
)

REM: Set arguments
IF NOT %ddb_ind%==0 (CALL SET ddb_name=%ARTIQ_ROOT%\%%%ddb_ind%%
) ELSE (CALL SET ddb_name=%ARTIQ_DDB%)

IF NOT %ip_ind%==0 (CALL SET ip_addr=%%%ip_ind%%
) ELSE (CALL SET ip_addr=%ARTIQ_HOST%)

REM: Start ARTIQ interface
START "ARTIQ Master" CMD "/c artiq_master -g -r %ARTIQ_ROOT%/repository --device-db %ARTIQ_ROOT%\%ddb_name% --bind=%ip_addr%"
TIMEOUT 2 > NUL && START "ARTIQ Dashboard" /min CMD "/c TIMEOUT 2 && CALL artiq_dashboard"
TIMEOUT 2 > NUL && START "ARTIQ Controller Manager" /min CMD "/k TIMEOUT 2 && artiq_ctlmgr"

REM: Unset variables
SET "argCount="
SET "ddb_ind="
SET "ip_ind="
SET "ddb_name="
SET "ip_addr="