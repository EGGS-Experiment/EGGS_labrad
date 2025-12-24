:: Opens the RealSimpleGrapher Client.
::  Intended as a desktop SHORTCUT ONLY.
::  i.e. create a shortcut TO THIS FILE and put it on the desktop.
::  This file won't work if not in this folder, since it uses the relative directory structure.

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
