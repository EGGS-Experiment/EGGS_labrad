:: Opens the TTL GUI.
::  Intended as a desktop shortcut.

@ECHO OFF
@SETLOCAL

@REM: Set up CMD
TITLE TTL GUI
CALL conda activate labart

@REM: Set up file location
SET FILE_DIR=%~dp0..\..\EGGS_labrad\clients\ARTIQ_client\TTL_client.py

@REM: Run TTL GUI
python %FILE_DIR% %*

@ENDLOCAL
EXIT /B
