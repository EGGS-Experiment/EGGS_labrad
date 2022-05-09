:: LabRAD Watchdog
:: Pings the LabRAD manager regularly, and sends an email if it fails

@ECHO OFF
SETLOCAL EnableDelayedExpansion

REM: Set default arguments
SET ip_addr=
SET /A fail_flag=0
SET /A timeout_period=20
SET /A fail_counter=0
SET /A fail_pings=5

REM: Parse arguments
SET /A argCount=0
FOR %%x IN (%*) DO (
    SET /A argCount+=1
    IF "%%x"=="-h" (GOTO HELP)
    IF "%%x"=="--help"(GOTO HELP)
    REM: todo: still need to finish
    IF "%%x"=="-t" (ECHO t arg)
    IF "%%x"=="-p" (ECHO p arg)
    IF "%%x"=="-n" (ECHO n arg)
)

REM: IP address must be specified, stop otherwise
IF %argCount% == 0 (
    ECHO Error: target IP address must be specified.
    GOTO EOF
) ELSE (
    SET ip_addr=%1
)


REM: Begin messages
ECHO %DATE% %TIME%: Watchdog started.
ECHO %DATE% %TIME%: Watching %ip_addr%.


:LOOPSTART
REM: Ping target IP address
ECHO %DATE% %TIME%: Pinging %ip_addr%
PING -n 1 -w 1000 -l 1 %ip_addr% | FIND /i " bytes=" >NUL 2>&1

REM: Process ping response
IF %ERRORLEVEL% == 1 (
    SET /A fail_counter+= 1
    REM ECHO %DATE% %TIME%: Pinging failed. ECHO %fail_pings% - %fail_counter% loops left to establish connection.
    IF %fail_counter% == %fail_pings% (
        SET /A fail_flag=1
        GOTO EOF
    )
) ELSE (
    ECHO %DATE% %TIME%: Pinging successful.
)

REM: Wait for next cycle
@TIMEOUT %timeout_period% /nobreak > NUL
GOTO LOOPSTART

:HELP
REM: todo: still need to finish
@ECHO usage: labrad_watchdog [IP_ADDRESS] [-h] [--devices] [-t] [-p] [-n]
@ECHO:
@ECHO LabRAD Node
@ECHO Optional Arguments:
@ECHO    -h, --help          show this message and exit
@ECHO    --devices           start the labrad core as well as GPIB and serial bus servers
@ECHO    --ip                connect to the labrad manager at the given IP address (default: %LABRADHOST%)
@ECHO:


:EOF
REM: Send an email if we have failed
If %fail_flag% == 1 (
    ECHO todo: send email placeholder
)

REM: Unset variables
SET "ip_addr="
SET "success_wait="
SET "fail_wait="
SET "fail_counter="
SET "fail_pings="
