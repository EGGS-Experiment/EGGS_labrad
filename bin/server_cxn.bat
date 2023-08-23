:: Server Connection
::  Creates a connection to labrad with all servers given shortcuts.

@ECHO OFF
@SETLOCAL

@REM Set up CMD
TITLE LabRAD Shell
CALL conda activate labart

@REM Set up file location
SET FILE_DIR=%~dp0server_cxn.py

@REM Run server_cxn.py
python -ix "%FILE_DIR%" %*

@ENDLOCAL
EXIT /B
