:: LabRAD Autosaver
::  Automatically pushes the datavault contents to
::      the remote repository on the hudsongroup server

@ECHO OFF
@SETLOCAL EnableDelayedExpansion


@REM: Change directory to .labard
CD "%HOME%\.labrad"


@REM: Set default arguments
SET drive_location=""
SET /A backup_interval=600


@REM: See if hudsongroup server is already mounted
FOR /f "tokens=2" %%i IN ('NET USE ^| FIND "\\eric.physics.ucla.edu"') DO (
    SET "drive_location=%%i\motion\.labrad_remote"
)


@REM: Process arguments
:PROCESSARGS
IF NOT '%1'=='' (
    IF "%1"=="-d" (
        IF %drive_location%=="" (
            SET drive_location=%2
        )
    )
    IF "%1"=="-t" (SET backup_interval=%2)
    SHIFT
    GOTO PROCESSARGS
)


@REM: Begin messages
ECHO %DATE% %TIME%: Autosaver started.
ECHO %DATE% %TIME%: Drive location set at %drive_location%.


:LOOPSTART
@REM: Add all files and commit
ECHO %DATE% %TIME%: Saving data...
CALL git add -A > NUL
CALL git commit -m "%COMPUTERNAME%: Saving data." > NUL
CALL git push origin master > NUL


@REM: Process response
IF %ERRORLEVEL%==1 (
    ECHO %DATE% %TIME%: Minor error.
) ELSE (
    ECHO %DATE% %TIME%: Save successful.
)

@REM: Wait for next cycle
@TIMEOUT %backup_interval% /nobreak > NUL
GOTO LOOPSTART


:HELP
@REM: todo: still need to finish
@ECHO usage: labrad_autosaver [-h] [--devices] [-t] [-p] [-n]
@ECHO:
@ECHO LabRAD Autosaver
@ECHO Optional Arguments:
@ECHO    -h, --help             show this message and exit
@ECHO    -d                     set the location to back up to (default: \\eric.physics.ucla.edu\groups\motion\.labrad_remote)
@ECHO    -t                     set the time between backups    (default: 10 minutes)
@ECHO:


:EOF
@ENDLOCAL
