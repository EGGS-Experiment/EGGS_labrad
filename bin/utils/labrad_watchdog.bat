:: LabRAD Watchdog
:: Pings the LabRAD manager regularly, and sends an email if it fails.

@ECHO OFF
SETLOCAL EnableDelayedExpansion

SET THRESHOLD=30
SET IP=%LABRADHOST%
SET TIMEOUTVAL=500
REM SET LOG="watchdog.log"

REM ECHO %DATE% %TIME%: Watchdog started >> %LOG%
ECHO %DATE% %TIME%: Watchdog started.

REM: Loop until <THRESHOLD> failed, consecutive pings are counted

SET /A COUNT=0

:LOOP

REM: ping LabRAD host IP
PING -n 1 -w 5000 -l 1 %IP% | FIND /i " bytes=" >NUL 2>&1

REM: Check if ping was successful
IF %ERRORLEVEL% == 1 (
    REM: increment failed ping count
    SET /A COUNT+=1
    ECHO %DATE% %TIME%: Failed ping detected - Count = !COUNT!.
) ELSE (
    REM: Reset failed ping count if device detected
    SET /A COUNT=0
)

REM: Wait a given amount of time
TIMEOUT %TIMEOUTVAL%

REM: If more than a certain amount of pings fail, notify admin
IF %COUNT% GEQ %THRESHOLD% (
    ECHO %DATE% %TIME%: %THRESHOLD% failed pings exceeded.
    GOTO NOTIFY
)

GOTO LOOP

:NOTIFY


REM: Unset variables
SET "THRESHOLD=30"
SET "IP="
SET "TIMEOUTVAL="
SET "COUNT="
