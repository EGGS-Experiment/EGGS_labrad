:: LabRAD Watchdog
:: Pings the LabRAD manager regularly, and sends an email if it fails

@ECHO OFF
SETLOCAL EnableDelayedExpansion

ECHO %DATE% %TIME%: Watchdog started
REM ping 192.168.1.76
REM if %errorlevel%
ping -n 1 -w 1000 -l 1 192.168.1.75 | find /i " bytes=" >NUL 2>&1

if %ERRORLEVEL% == 1 (
    ECHO thkim
) ELSE (
    ECHO yzde
)
