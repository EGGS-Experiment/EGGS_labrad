:: Opens the EGGS GUI.
::  Intended as a desktop SHORTCUT ONLY.
::  i.e. create a shortcut TO THIS FILE and put it on the desktop.
::  This file won't work if not in this folder, since it uses the relative directory structure.

@ECHO OFF
@SETLOCAL

@REM Set up CMD
TITLE EGGS GUI
CALL conda activate labart

@REM Set up file location
SET FILE_DIR=%~dp0..\..\EGGS_labrad\clients\EGGS_GUI\EGGS_gui.py

@REM Run EGGS GUI
python %FILE_DIR% %*

@ENDLOCAL
EXIT /B
