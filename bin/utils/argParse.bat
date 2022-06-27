:: argParse
:: Parse command line arguments by flags

@ECHO OFF
SETLOCAL EnableDelayedExpansion


@REM: Get number of arguments
SET /A argCount=0
FOR %%x IN (%*) DO (
    SET /A argCount+=1
)


@REM: Process arguments
:PROCESSARGS
IF NOT '%1'=='' (
    IF "%1"=="-r" (
        SET argVal=%2
    )
    SHIFT
    GOTO PROCESSARGS
)
echo argval: %argVal%


:EOF
@REM: Unset variables
SET "argCount="
SET "argVal="
