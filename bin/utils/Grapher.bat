:: Opens the RealSimpleGrapher Client.
::  Intended as a desktop shortcut.

@ECHO OFF
@SETLOCAL

@REM Set up CMD
TITLE Real Simple Grapher
CALL conda activate labart

@REM Set up file location
SET FILE_DIR=%~dp0..\..\..\RealSimpleGrapher\rsg_client.py

@REM Run EGGS GUI
python %FILE_DIR% %*

@ENDLOCAL
EXIT /B
